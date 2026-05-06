import io
import json
import logging
import zipfile
from time import gmtime, strftime

from django.http import HttpResponseServerError, JsonResponse
from django.urls import path
from rest_framework.request import Request
from rest_framework.response import Response
from tira.third_party_integrations import temporary_directory

from ... import tira_model as model
from ...checks import check_conditional_permissions
from ...model import RunningProcesses
from ..vm_api import _run_evaluation

logger = logging.getLogger("tira")


@check_conditional_permissions(restricted=True)
def upload_response(request: Request, vm_id: str, job_id: str) -> Response:
    if request.method != "POST":
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Only Post allowed."}))

    try:
        job = RunningProcesses.objects.get(uuid=job_id)
    except Exception:
        return HttpResponseServerError(json.dumps({"status": 1, "message": f"Job with ID {job_id} does not exist."}))

    dataset_id = job.dataset_id
    vm_id = job.vm_id

    if not dataset_id or dataset_id is None or dataset_id == "None":
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Please specify the associated dataset."}))

    dataset = model.get_dataset(dataset_id)
    if not dataset or "format" not in dataset or not dataset["format"] or "task" not in dataset or not dataset["task"]:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Uploads are not allowed for the dataset."}))

    task = model.get_task(dataset["task"], False)
    if not task or not task["featured"]:
        return HttpResponseServerError(
            json.dumps(
                {
                    "status": 1,
                    "message": "The dataset is deprecated and therefore allows no uploads.",
                }
            )
        )

    uploaded_file = request.FILES["file"]
    result_dir = temporary_directory()
    with open(result_dir / "upload.zip", "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    with zipfile.ZipFile(io.BytesIO((result_dir / "upload.zip").read_bytes())) as archive:
        try:
            run_id = archive.open("run.prototext", "r").read().decode("utf-8").split('runId: "')[1].split('"')[0]
            target_directory = model.model.runs_dir_path / dataset_id / vm_id / run_id
            target_directory.mkdir(parents=True, exist_ok=True)
            archive.extractall(target_directory)
            model.add_run(dataset_id, vm_id, run_id)
        except Exception as e:
            logger.exception(e)
            logger.warning(f"Could not store run: {e}")
            raise e

        if "-evaluates-" not in run_id:
            try:
                _run_evaluation(vm_id, dataset["task"], run_id, dataset_id)
            except Exception as e:
                logger.exception(e)
                logger.warning(f"Could not start evaluator: {e}")
                raise e

    RunningProcesses.objects.get(uuid=job_id).delete()

    return JsonResponse({"status": 0, "message": "ok"})


@check_conditional_permissions(restricted=True)
def update_running_process_output(request: Request, vm_id: str, job_id: str) -> Response:
    if request.method != "POST":
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Only Post allowed."}))

    try:
        job = RunningProcesses.objects.get(uuid=job_id)
    except:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Job does not exist."}))

    try:
        data = json.loads(request.body) if request.body else request.POST.dict()
    except json.JSONDecodeError:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Could not parse request body as JSON."}))

    if "output" not in data:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "A field output is expected."}))

    details = json.loads(job.details) if job.details else {}

    if (
        "execution" in details
        and "scheduling" in details["execution"]
        and details["execution"]["scheduling"] == "running"
    ):
        details["execution"]["scheduling"] = "done"
        details["execution"]["running"] = "running"
        details["started_at"] = strftime("%d.%m. at %H:%M:%S", gmtime())

    details["stdOutput"] = data.get("output")
    job.details = json.dumps(details)
    job.save(update_fields=["details"])

    return JsonResponse({"status": 0, "message": "ok", "killing": job.killing})


@check_conditional_permissions(restricted=True)
def registered_workers(request: Request, vm_id: str) -> Response:
    ret = []
    try:
        from celery.app.control import Inspect
        from tira_worker import app

        inspect: Inspect = app.control.inspect()
        stats = inspect.stats()
        workers = inspect.active()
        active_queues = inspect.active_queues()
        for name, tasks in workers.items():
            worker_stats = stats.get(name)
            worker_queues = active_queues.get(name)
            running_tasks = []
            for t in tasks:
                running_tasks.append({i: t[i] for i in ["id", "name", "args", "kwargs", "time_start"]})

            ret.append(
                {
                    "name": name,
                    "uptime": worker_stats["uptime"],
                    "tasks": running_tasks,
                    "queues": json.dumps([i["name"] for i in worker_queues]),
                    "total": json.dumps(worker_stats["total"]),
                }
            )
    except Exception:
        pass
    return JsonResponse({"status": 0, "context": {"active_workers": ret}})


@check_conditional_permissions(restricted=True)
def active_jobs(request: Request, vm_id: str, task_id: str) -> Response:
    ret = []
    for i in RunningProcesses.objects.filter(task=task_id):
        ret.append({"uuid": i.uuid, "task": i.task, "vm_id": i.vm_id, "dataset_id": i.dataset_id, "details": i.details})

    return JsonResponse({"status": 0, "context": {"jobs": ret}})


def validate_docker_image(request: Request) -> Response:
    if request.method != "POST":
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Only Post allowed."}))

    try:
        data = json.loads(request.body) if request.body else request.POST.dict()
    except json.JSONDecodeError:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Could not parse request body as JSON."}))

    if "image" not in data or not data["image"]:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "A field image is expected."}))

    if "repository_name" not in data or not data["repository_name"]:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "A field repository_name is expected."}))

    git_runner = model.get_git_integration("webis", None)

    try:
        ret = git_runner.get_manifest_of_docker_image_image_repository(
            data["repository_name"], data["image"], cache=None, force_cache_refresh=False
        )
    except Exception as e:
        logger.exception(e)
        logger.warning(f"Could not validate docker image: {e}")
        ret = {}

    return JsonResponse({"status": 0, "message": "ok", "context": ret})


endpoints = [
    path("upload-response/<str:vm_id>/<str:job_id>", upload_response),
    path("update-running-process-output/<str:vm_id>/<str:job_id>", update_running_process_output),
    path("registered-workers/<str:vm_id>", registered_workers),
    path("active-jobs/<str:vm_id>/<str:task_id>", active_jobs),
    path("validate-docker-image", validate_docker_image),
]
