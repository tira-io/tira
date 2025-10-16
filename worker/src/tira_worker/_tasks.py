import sys
from pathlib import Path
from typing import Callable, Optional

from celery import Celery
from tira.io_utils import get_tira_id, persist_tira_metadata_for_job
from tira.rest_api_client import Client as RestClient
from tira.rest_api_client import TiraClient

from .settings import CPU_COUNT, MEMORY_LIMIT, QUEUE_BROKER_URL, QUEUE_RESULTS_BACKEND_URL
from .utils import gpu_device_ids

app = Celery("tira-tasks", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)
gpu_executor = Celery("tira-gpu-executor", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)


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


def execute_monitored(method: Callable):
    from tira.io_utils import MonitoredExecution

    return MonitoredExecution().run(lambda i: method(i))


@gpu_executor.task
def run(
    dataset: str,
    task: str,
    docker_image: str,
    command: str,
    software_id: str,
    team: str,
    mount_hf_model: "Optional[list[str]]" = None,
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

    run_results = execute_monitored(
        lambda i: client.local_execution.run(
            image=docker_image,
            command=command,
            input_dir=system_inputs,
            output_dir=i,
            allow_network=False,
            additional_volumes=hf_models,
            cpu_count=CPU_COUNT,
            mem_limit=MEMORY_LIMIT,
            gpu_device_ids=gpu_devices,
        )
    )
    persist_tira_metadata_for_job(run_results, get_tira_id(), "none", software_id, dataset, task)
    client.upload_run_admin(dataset, team, run_results)


@app.task
def evaluate(run_id: str, dataset: str, evaluator_id: str, task: str, team: str) -> None:
    client: TiraClient = get_admin_client()

    truths = client.download_dataset(task, dataset, truth_dataset=True)
    print("Truths are available locally:", truths)
    run_dir = client.download_zip_to_cache_directory(run_id=run_id, dataset=dataset, task=task, team=team)
    print("Run is available locally:", run_dir)

    eval_results = execute_monitored(lambda i: client.evaluate(run_dir, dataset, i))
    persist_tira_metadata_for_job(
        eval_results, f"{get_tira_id()}-evaluates-{run_id}", run_id, evaluator_id, dataset, task
    )

    client.upload_run_admin(dataset, team, eval_results)


get_admin_client()
