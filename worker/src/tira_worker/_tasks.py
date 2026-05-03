import sys
import threading
from pathlib import Path
from typing import Callable, Optional

from celery import Celery
from tira.io_utils import get_tira_id, persist_tira_metadata_for_job
from tira.rest_api_client import Client as RestClient
from tira.rest_api_client import TiraClient
from tira.workflows import run_workflow

from .settings import CPU_COUNT, MEMORY_LIMIT, QUEUE_BROKER_URL, QUEUE_RESULTS_BACKEND_URL
from .utils import gpu_device_ids
import os
from shutil import copytree

app = Celery("tira-tasks", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)
gpu_executor = Celery("tira-gpu-executor", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)
MONITORED_EXECUTION_POLL_INTERVAL_SECONDS = 90


def get_admin_client() -> TiraClient:
    ret: "TiraClient" = RestClient()
    role = ret.json_response("/api/role")

    if not role or "role" not in role or "admin" != role["role"]:
        raise ValueError(f"The tira client has no admin credentials. Got {role}")

    return ret


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
    ret = []

    if stdout:
        ret += ["## stdout (Last 15 lines)", stdout]
    if stderr:
        ret += ["# stderr (Last 15 lines)", stderr]

    return "\n\n".join(ret)


def execute_monitored(method: Callable, client: "Optional[TiraClient]" = None, job_id: "Optional[str]" = None):
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
            except:
                print("Failed to load running processes")
                running_process_response = None

            if running_process_response and  "killing" in running_process_response and running_process_response["killing"]:
                print("I will kill all running containers...")
                client.local_execution.kill_all_running_containers()
                print("The running containers are killed...")

    return result["ret"]


@gpu_executor.task()
def run(
    dataset: str,
    task: str,
    docker_image: str,
    command: str,
    software_id: str,
    team: str,
    job_id: str,
    mount_hf_model: "Optional[list[str]]" = None,
    task_workflow_configuration: "Optional[dict]" = None,
    software_workflow_configuration: "Optional[dict]" = None,
) -> None:
    client: TiraClient = get_admin_client()
    global gpu_devices

    system_inputs = client.download_dataset(task, dataset)
    print("Inputs are available locally:", system_inputs)

    hf_models = None
    if mount_hf_model:
        from tira.io_utils import huggingface_model_mounts

        hf_models = huggingface_model_mounts(mount_hf_model)
        hf_models = [k + ":" + v["bind"] + ":" + v["mode"] for k, v in hf_models.items()]
        print(f"The following models from huggingface are mounted: {hf_models}\n\n")

    allow_network = False

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
                tira=client
            )
            os.rmdir(i)
            copytree(run_results.run / "output", i)
            
            try:
                print((run_results.run / "stdout.txt").read_text())
            except:
                pass

            try:
                print((run_results.run / "stderr.txt").read_text(), file=sys.stderr)
            except:
                pass

        run_results = execute_monitored(
            run_tmp,
            client=client,
            job_id=job_id,
        )
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
        eval_results, f"{get_tira_id()}-evaluates-{run_id}", run_id, evaluator_id, dataset, task
    )

    client.upload_run_admin(eval_results, job_id)


if "celery" in sys.argv[0]:
    get_admin_client()
