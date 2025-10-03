from pathlib import Path
from typing import Callable

from celery import Celery
from tira.io_utils import get_tira_id, persist_tira_metadata_for_job, zip_dir
from tira.rest_api_client import Client as RestClient
from tira.rest_api_client import TiraClient

from .settings import QUEUE_BROKER_URL, QUEUE_RESULTS_BACKEND_URL

app = Celery("tira-tasks", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)


def get_admin_client() -> TiraClient:
    ret: "TiraClient" = RestClient()
    role = ret.json_response("/api/role")

    if not role or "role" not in role or "admin" != role["role"]:
        raise ValueError(f"The tira client has no admin credentials. Got {role}")

    return ret


@app.task
def dummytask(name: str) -> str:
    """
    I just greet everyone who calls me :)
    TODO: remove me when the deployment gets serious
    """
    import socket

    return f"{socket.gethostname()} says hello to {name}"


def execute_monitored(method: Callable):
    from tira.io_utils import MonitoredExecution

    def failsave_exec(i):
        try:
            method(i)
        except:
            pass

    return MonitoredExecution().run(lambda i: failsave_exec(i))


@app.task
def evaluate(run_id: str, dataset: str, task: str, team: str) -> bytes:
    client: TiraClient = get_admin_client()

    truths = client.download_dataset(task, dataset, truth_dataset=True)
    print("Truths are available locally:", truths)
    run_dir = client.download_zip_to_cache_directory(run_id=run_id, dataset=dataset, task=task, team=team)
    print("Run is available locally:", run_dir)

    eval_results = execute_monitored(lambda i: client.evaluate(run_dir, dataset, i))
    software_id = "fooo"
    persist_tira_metadata_for_job(
        eval_results, f"{get_tira_id()}-evaluates-{run_id}", run_id, software_id, dataset, task
    )
    ret: Path = zip_dir(eval_results)

    return ret.read_bytes()


get_admin_client()
