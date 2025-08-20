from celery import Celery
from tira.rest_api_client import Client as RestClient
from tira.rest_api_client import TiraClient

from .settings import QUEUE_BROKER_URL, QUEUE_RESULTS_BACKEND_URL, TIRA_API_KEY

app = Celery("tira-tasks", backend=QUEUE_RESULTS_BACKEND_URL, broker=QUEUE_BROKER_URL)


@app.task
def evaluate(runid: str) -> None:
    # TODO: init RestClient from configuration
    client: "TiraClient" = RestClient(base_url=None, api_key=TIRA_API_KEY, base_url_api="")
    # TODO: load values using REST-API / Client from runid.
    raise NotImplementedError
    client.submit_code(
        path=None,  # TODO
        task_id=None,  # TODO
        command=None,  # TODO
        dataset_id=None,  # TODO
        user_id=None,  # TODO
        docker_file=None,  # TODO
        dry_run=False,
        allow_network=False,
        mount_hf_model=None,  # TODO
    )
