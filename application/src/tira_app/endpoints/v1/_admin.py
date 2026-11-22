from __future__ import annotations

import json
import logging
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from time import gmtime, strftime
from typing import IO

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, HttpResponseServerError, JsonResponse
from django.urls import path
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from ... import tira_model as model
from ...checks import check_conditional_permissions
from ...model import DockerSoftware, DockerSoftwareAutomaticReview, DockerSoftwareReview, Run, RunningProcesses
from ..vm_api import _run_evaluation

logger = logging.getLogger("tira")


def _extract_run_from_archive(file: IO[bytes], dataset_id: str, vm_id: str) -> str:
    with zipfile.ZipFile(file) as archive:
        with archive.open("run.prototext", "r") as f:
            run_id = f.read().decode("utf-8").split('runId: "')[1].split('"')[0]
        target_directory = model.model.runs_dir_path / dataset_id / vm_id / run_id
        target_directory.mkdir(parents=True, exist_ok=True)
        archive.extractall(target_directory)
    model.add_run(dataset_id, vm_id, run_id)
    return run_id


@require_POST
@check_conditional_permissions(restricted=True)
def upload_response(request: Request, vm_id: str, job_id: str) -> Response:
    job = RunningProcesses.objects.filter(uuid=job_id).first()
    if job is None:
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

    try:
        run_id = _extract_run_from_archive(request.FILES["file"], dataset_id, vm_id)
    except Exception as e:
        logger.exception("Could not store run", exc_info=e)
        raise

    dynamic_mounts = json.loads(job.details).get("job_config", {}).get("dynamic_mounts") if job.details else None
    if dynamic_mounts is not None:
        Run.objects.filter(run_id=run_id).update(dynamic_mounts=json.dumps(dynamic_mounts))

    if "-evaluates-" not in run_id:
        try:
            _run_evaluation(vm_id, dataset["task"], run_id, dataset_id)
        except Exception as e:
            logger.exception("Could not start evaluator", exc_info=e)
            raise

    RunningProcesses.objects.get(uuid=job_id).delete()

    return JsonResponse({"status": 0, "message": "ok"})


@require_POST
@check_conditional_permissions(restricted=True)
def update_running_process_output(request: Request, vm_id: str, job_id: str) -> Response:

    try:
        job = RunningProcesses.objects.get(uuid=job_id)
    except Exception:
        return JsonResponse({"status": 0, "message": "ok", "killing": True})

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
        ret.append(
            {
                "uuid": i.uuid,
                "task": i.task,
                "vm_id": i.vm_id,
                "dataset_id": i.dataset_id,
                "details": i.details,
            }
        )

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
            data["repository_name"],
            data["image"],
            cache=None,
            force_cache_refresh=False,
        )
    except Exception as e:
        logger.warning("Could not validate docker image", exc_info=e)
        ret = {}

    return JsonResponse({"status": 0, "message": "ok", "context": ret})


_RUN_ID_TIMESTAMP_FORMAT = "%Y-%m-%d-%H-%M-%S"


def _run_submission_time(run_id: str) -> datetime | None:
    """Run ids start with the creation time (see tira.io_utils.get_tira_id), e.g., 2024-01-31-12-30-00-1a2b3c4d."""
    try:
        return datetime.strptime(run_id[:19], _RUN_ID_TIMESTAMP_FORMAT)
    except ValueError:
        return None


def aggregate_run_statistics(start: datetime, end: datetime) -> list[dict]:
    """Per task: executed code submissions, run uploads, and how many of both have no review yet.
    Evaluation runs are not counted since they have neither a docker software nor an upload."""
    stats: dict[str, dict] = {}
    # Run ids start with their timestamp, so the range can be restricted in the database ('~' sorts after the suffix).
    runs = Run.objects.filter(
        Q(docker_software__isnull=False) | Q(upload__isnull=False),
        deleted=False,
        run_id__gte=start.strftime(_RUN_ID_TIMESTAMP_FORMAT),
        run_id__lte=end.strftime(_RUN_ID_TIMESTAMP_FORMAT) + "~",
    ).select_related("review")
    for run in runs:
        submitted = _run_submission_time(run.run_id)
        if submitted is None or not start <= submitted <= end:
            continue

        task_id = run.task_id or ""
        row = stats.setdefault(
            task_id, {"task": task_id, "executed_code_submissions": 0, "run_uploads": 0, "unreviewed": 0}
        )
        row["executed_code_submissions" if run.docker_software_id else "run_uploads"] += 1
        # Review rows are created together with runs, a run is reviewed only once a verdict is set.
        review = getattr(run, "review", None)
        if review is None or not (review.has_errors or review.has_no_errors or review.has_warnings):
            row["unreviewed"] += 1

    return sorted(stats.values(), key=lambda r: r["task"])


@api_view(["GET"])
@permission_classes([IsAdminUser])
def run_statistics(request: Request) -> Response:
    try:
        start = datetime.fromisoformat(request.GET["start"]).replace(tzinfo=None)
        end = datetime.fromisoformat(request.GET["end"]).replace(tzinfo=None)
    except (KeyError, ValueError):
        return JsonResponse(
            {"status": 1, "message": "Please pass the ISO timestamps 'start' and 'end', e.g., 2024-01-31T12:00:00."},
            status=400,
        )

    return JsonResponse({"status": 0, "context": {"statistics": aggregate_run_statistics(start, end)}})


def _serialize_docker_software_review(docker_software_id: int, review: DockerSoftwareReview | None) -> dict:
    return {
        "docker_software_id": docker_software_id,
        "reviewer_id": review.reviewer_id if review else "",
        "review_date": review.review_date if review else "",
        "code_review": review.code_review if review else DockerSoftwareReview.Status.PENDING,
        "execution_review": review.execution_review if review else DockerSoftwareReview.Status.PENDING,
        "comment": review.comment if review else "",
    }


@api_view(["GET", "PUT"])
@permission_classes([IsAdminUser])
def docker_software_review(request: Request, docker_software_id: int) -> Response:
    if not DockerSoftware.objects.filter(docker_software_id=docker_software_id).exists():
        return JsonResponse({"status": 1, "message": "Unknown docker software."}, status=404)

    review = DockerSoftwareReview.objects.filter(docker_software_id=docker_software_id).first()

    if request.method == "PUT":
        valid = DockerSoftwareReview.Status.values
        code_review = request.data.get("code_review")
        execution_review = request.data.get("execution_review")
        comment = request.data.get("comment", "")
        if code_review not in valid or execution_review not in valid or not isinstance(comment, str):
            return JsonResponse(
                {"status": 1, "message": f"code_review and execution_review must be one of {valid}."}, status=400
            )
        review, _ = DockerSoftwareReview.objects.update_or_create(
            docker_software_id=docker_software_id,
            defaults={
                "reviewer_id": request.user.username,
                "review_date": datetime.utcnow().isoformat(),
                "code_review": code_review,
                "execution_review": execution_review,
                "comment": comment,
            },
        )

    return JsonResponse({"status": 0, "context": _serialize_docker_software_review(docker_software_id, review)})


def _serialize_automatic_review(review: DockerSoftwareAutomaticReview) -> dict:
    return {
        "id": str(review.id),
        "docker_software_id": review.docker_software_id,
        "title": review.title,
        "verdict": review.verdict,
        "comment": review.comment,
        "details": review.details,
        "uploader_id": review.uploader_id,
        "review_date": review.review_date,
    }


@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def docker_software_automatic_reviews(request: Request, docker_software_id: int) -> Response:
    """Lists (GET) or adds (POST, multipart) automatic reviews. A POST has the fields title, verdict, comment,
    details (JSON object, e.g., the LLM that was used) and file (the zip of the complete review)."""
    if not DockerSoftware.objects.filter(docker_software_id=docker_software_id).exists():
        return JsonResponse({"status": 1, "message": "Unknown docker software."}, status=404)

    if request.method == "POST":
        title = str(request.data.get("title", "")).strip()
        verdict = request.data.get("verdict")
        archive = request.FILES.get("file")
        try:
            details = json.loads(request.data.get("details") or "{}")
        except ValueError:
            details = None

        if not title or len(title) > 200 or verdict not in DockerSoftwareAutomaticReview.Verdict.values:
            return JsonResponse(
                {
                    "status": 1,
                    "message": f"A title (<= 200 characters) and a verdict of "
                    f"{DockerSoftwareAutomaticReview.Verdict.values} are required.",
                },
                status=400,
            )
        if not isinstance(details, dict) or archive is None or not zipfile.is_zipfile(archive):
            return JsonResponse(
                {"status": 1, "message": "details must be a JSON object and file must be a zip."}, status=400
            )

        archive.seek(0)
        review = DockerSoftwareAutomaticReview.objects.create(
            docker_software_id=docker_software_id,
            title=title,
            verdict=verdict,
            comment=str(request.data.get("comment", "")),
            details=details,
            uploader_id=request.user.username,
            review_date=datetime.utcnow().isoformat(),
        )
        relative = Path("data") / "software-reviews" / str(docker_software_id) / f"{review.id}.zip"
        target = Path(settings.TIRA_ROOT) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            for chunk in archive.chunks():
                f.write(chunk)
        review.archive_path = str(relative)
        review.save()
        return JsonResponse({"status": 0, "context": _serialize_automatic_review(review)}, status=201)

    reviews = DockerSoftwareAutomaticReview.objects.filter(docker_software_id=docker_software_id)
    reviews = reviews.order_by("-review_date")
    return JsonResponse({"status": 0, "context": {"reviews": [_serialize_automatic_review(r) for r in reviews]}})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def docker_software_automatic_review_archive(
    request: Request, docker_software_id: int, review_id: uuid.UUID
) -> Response:
    reviews = DockerSoftwareAutomaticReview.objects.filter(id=review_id, docker_software_id=docker_software_id)
    review = reviews.first()
    path = Path(settings.TIRA_ROOT) / review.archive_path if review else None
    if not path or not review.archive_path or not path.is_file():
        return JsonResponse({"status": 1, "message": "Unknown review."}, status=404)

    return FileResponse(open(path, "rb"), as_attachment=True, filename=f"review-{review_id}.zip")


endpoints = [
    path("docker-software-automatic-reviews/<int:docker_software_id>", docker_software_automatic_reviews),
    path(
        "docker-software-automatic-reviews/<int:docker_software_id>/<uuid:review_id>/archive",
        docker_software_automatic_review_archive,
    ),
    path("docker-software-review/<int:docker_software_id>", docker_software_review),
    path("run-statistics", run_statistics),
    path("upload-response/<str:vm_id>/<str:job_id>", upload_response),
    path(
        "update-running-process-output/<str:vm_id>/<str:job_id>",
        update_running_process_output,
    ),
    path("registered-workers/<str:vm_id>", registered_workers),
    path("active-jobs/<str:vm_id>/<str:task_id>", active_jobs),
    path("validate-docker-image", validate_docker_image),
]
