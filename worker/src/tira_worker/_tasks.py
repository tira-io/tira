from __future__ import annotations

import os
import sys
import threading
from os import environ
from pathlib import Path
from shutil import copytree
from subprocess import check_output
from typing import Callable, Optional

from celery import Celery
from tira.io_utils import (
    get_tira_id,
    hf_cache_dir,
    huggingface_model_mounts,
    persist_tira_metadata_for_job,
)
from tira.rest_api_client import Client as RestClient
from tira.third_party_integrations import is_public_huggingface_model
from tira.tira_client import TiraClient
from tira.workflows import run_workflow

from .settings import (
    CPU_COUNT,
    MEMORY_LIMIT,
    QUEUE_BROKER_URL,
    QUEUE_RESULTS_BACKEND_URL,
)
from .utils import gpu_device_ids

app = Celery("tira-tasks", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)
app.conf.control_queue_exclusive = True  # Not required after celery 5.7 is released
app.conf.control_queue_durable = False  # Not required after celery 5.7 is released

gpu_executor = Celery("tira-gpu-executor", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)
gpu_executor.conf.control_queue_exclusive = True  # Not required after celery 5.7 is released
gpu_executor.conf.control_queue_durable = False  # Not required after celery 5.7 is released

# Poll every 90 seconds (TODO: make me configurable?)
MONITORED_EXECUTION_POLL_INTERVAL_SECONDS = 90


def get_admin_client() -> TiraClient:
    ret: TiraClient = RestClient()
    role = ret.json_response("/api/role")

    if not role or "role" not in role or "admin" != role["role"]:
        raise ValueError(f"The tira client has no admin credentials. Got {role}")

    return ret


def fail_if_tracker_does_not_work() -> None:
    from pathlib import Path

    from tira.rest_api_client import Client as RestClient
    from tira.third_party_integrations import temporary_directory
    ret = temporary_directory()
    tira = RestClient()
    tira.local_execution.run(
        image="ubuntu:24.04",
        command="echo 'check if tirex-tracker works'",
        input_dir="/tmp",
        output_dir=ret,
    )
    if not (Path(ret) / ".tracking-results.yml").is_file():
        msg = f"the tirex-tracker does not work. Could not find the tracking file in {ret}."
        print(msg)
        raise ValueError(msg)
    else:
        print(f"Tirex tracker works, see {ret}")


if "celery" in sys.argv[0]:
    fail_if_tracker_does_not_work()


if "celery" in sys.argv[0] and "gpu_executor" in sys.argv[2]:
    gpu_devices = gpu_device_ids()
    get_admin_client().local_execution.run(
        image="bash",
        command="ls -lha",
        input_dir="/tmp",
        output_dir="/tmp/foo",
        cpu_count=CPU_COUNT,
        mem_limit=MEMORY_LIMIT,
        gpu_device_ids=gpu_devices,
    )
else:
    gpu_devices = None


def _tail_lines(text: str, line_count: int = 15) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-line_count:])


def _current_monitored_output(monitored_execution) -> str:
    stdout = _tail_lines(monitored_execution.stdout.getvalue())
    stderr = _tail_lines(monitored_execution.stderr.getvalue())
    ret: list[str] = []

    if stdout:
        ret.extend(("## stdout (Last 15 lines)", stdout))
    if stderr:
        ret.extend(("## stderr (Last 15 lines)", stderr))

    return "\n\n".join(ret)


def execute_monitored(method: Callable, client: Optional[TiraClient] = None, job_id: Optional[str] = None) -> Path:
    from tira.io_utils import MonitoredExecution

    monitored_execution = MonitoredExecution()
    result = {}

    def run_in_background():
        result["ret"] = monitored_execution.run(lambda i: method(i))

    thread = threading.Thread(target=run_in_background)
    thread.start()

    while thread.is_alive():
        thread.join(timeout=MONITORED_EXECUTION_POLL_INTERVAL_SECONDS)

        if client is not None and job_id is not None:
            current_output = _current_monitored_output(monitored_execution)
            try:
                running_process_response = client.update_running_process_output_admin(job_id, current_output)
            except Exception:
                print("Failed to load running processes")
                running_process_response = None

            if (
                running_process_response
                and "killing" in running_process_response
                and running_process_response["killing"]
            ):
                print("I will kill all running containers...")
                client.local_execution.kill_all_running_containers()
                print("The running containers are killed...")

    return result["ret"]


def rsync_from_local_or_fail(src_dir: Path, target_dir: Path):
    if not src_dir.is_dir():
        raise ValueError(f"Expected local directory '{src_dir}' to exist for rsync.")

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "rsync",
        "-a",
        "--size-only",
        "--ignore-existing",
        f"{str(src_dir).rstrip('/')}/",
        f"{str(target_dir).rstrip('/')}/",
    ]
    print(" ".join(cmd))
    check_output(cmd)


def download_hf_model(model: str) -> None:
    from huggingface_hub import snapshot_download

    repo_id = model.replace("--", "/")
    if is_public_huggingface_model(repo_id):
        snapshot_download(repo_id=repo_id)
    else:
        model_in_fs = ("models/" + str(model)).replace("/", "--")

        src_dir = Path("/mnt/ceph/tira/data/publicly-shared-datasets/huggingface/hub") / model_in_fs
        target_dir = hf_cache_dir() / model_in_fs

        rsync_from_local_or_fail(src_dir, target_dir)


def resolve_hf_models(mount_hf_model: Optional[list[str]]) -> Optional[list[str]]:
    ret = None
    if mount_hf_model:
        for model in mount_hf_model:
            download_hf_model(model)

        hf_models = huggingface_model_mounts(mount_hf_model)
        ret = [k + ":" + v["bind"] + ":" + v["mode"] for k, v in hf_models.items()]
        print(f"The following models from huggingface are mounted: {ret}\n\n")

    return ret


@gpu_executor.task()
def run(
    dataset: str,
    task: str,
    docker_image: str,
    command: str,
    software_id: str,
    team: str,
    job_id: str,
    mount_hf_model: Optional[list[str]] = None,
    task_workflow_configuration: Optional[dict] = None,
    software_workflow_configuration: Optional[dict] = None,
    env_to_forward: Optional[dict] = None,
    dynamic_mounts: Optional[dict] = None,
) -> None:
    client: TiraClient = get_admin_client()
    global gpu_devices

    system_inputs = client.download_dataset(task, dataset)
    print("Inputs are available locally:", system_inputs)

    hf_models = resolve_hf_models(mount_hf_model)

    allow_network = False
    forward_environment_variables = None
    if env_to_forward:
        forward_environment_variables = list(set(env_to_forward.keys()))
        for k, v in env_to_forward.items():
            environ[k] = v

    mount_directory = {}
    cache_directory = {}

    if dynamic_mounts:
        from tira.third_party_integrations import temporary_directory

        for k, v in dynamic_mounts.items():

            if v["source"] == "EMPTY_DIR" and v["mode"] == "rw":
                cache_directory[k] = temporary_directory()
            else:
                mount_directory[k] = temporary_directory()
        
        print("cache_directory", cache_directory)
        print("mount_directory", mount_directory)

    if task_workflow_configuration is None and software_workflow_configuration is None:
        run_results = execute_monitored(
            lambda i: client.local_execution.run(
                image=docker_image,
                command=command,
                input_dir=system_inputs,
                output_dir=i,
                allow_network=allow_network,
                additional_volumes=hf_models,
                cpu_count=CPU_COUNT,
                mem_limit=MEMORY_LIMIT,
                gpu_device_ids=gpu_devices,
                forward_environment_variables=forward_environment_variables,
            ),
            client=client,
            job_id=job_id,
        )
    else:
        software_workflow_configuration["image"] = docker_image

        def run_tmp(i):
            run_results = run_workflow(
                system_inputs,
                task_workflow_configuration["name"],
                task_workflow_configuration,
                software_workflow_configuration,
                allow_network=allow_network,
                additional_volumes=hf_models,
                gpu_device_ids=gpu_devices,
                tira=client,
                forward_environment_variables=forward_environment_variables,
                cache_directory=cache_directory,
                mount_directory=mount_directory,
            )
            os.rmdir(i)
            print(run_results.message)
            copytree(run_results.run / "output", i)

            try:
                print((run_results.run / "stdout.txt").read_text())
            except Exception:
                pass

            try:
                print((run_results.run / "stderr.txt").read_text(), file=sys.stderr)
            except Exception:
                pass

            for k, v in cache_directory.items():
                try:
                    copytree(run_results.run / k, i.parent / v)
                except Exception:
                    print("something failed ....")
                    pass

        run_results = execute_monitored(
            run_tmp,
            client=client,
            job_id=job_id,
        )

    if forward_environment_variables:
        for k in forward_environment_variables:
            try:
                del environ[k]
            except Exception:
                pass

    persist_tira_metadata_for_job(run_results, get_tira_id(), "none", software_id, dataset, task)
    client.upload_run_admin(run_results, job_id)


@app.task()
def evaluate(run_id: str, dataset: str, evaluator_id: str, task: str, team: str, job_id: str) -> None:
    client: TiraClient = get_admin_client()

    truths = client.download_dataset(task, dataset, truth_dataset=True)
    print("Truths are available locally:", truths)
    run_dir = client.download_zip_to_cache_directory(run_id=run_id, dataset=dataset, task=task, team=team)
    print("Run is available locally:", run_dir)

    eval_results = execute_monitored(lambda i: client.evaluate(run_dir, dataset, i), client=client, job_id=job_id)
    persist_tira_metadata_for_job(
        eval_results,
        f"{get_tira_id()}-evaluates-{run_id}",
        run_id,
        evaluator_id,
        dataset,
        task,
    )

    client.upload_run_admin(eval_results, job_id)


if "celery" in sys.argv[0]:
    get_admin_client()
