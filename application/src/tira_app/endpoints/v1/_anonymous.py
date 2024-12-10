import json
from pathlib import Path
import html
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseServerError
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from tira.check_format import _fmt, check_format, lines_if_valid
from tira.third_party_integrations import temporary_directory
from werkzeug.utils import secure_filename

from ... import model as modeldb
from ... import tira_model as model
from ...checks import check_permissions, check_resources_exist
from ..vm_api import run_eval


@api_view(["GET"])
def read_anonymous_submission(request: Request, submission_uuid: str) -> Response:
    """Read information about an anonymous submission identified by the ownership uuid.

    Args:
        request (Request): The request that triggered the REST API call.
        submission_uuid (str): The ownership uuid of the anonymous submission

    Returns:
        Response: The information about the anonymous submission
    """
    try:
        ret = modeldb.AnonymousUploads.objects.get(uuid=submission_uuid)

        return Response({"uuid": ret.uuid, "dataset_id": ret.dataset.dataset_id, "created": ret.created})
    except:
        return HttpResponseServerError(
            json.dumps({"status": 1, "message": f"Run with uuid {html.escape(submission_uuid)} does not exist."})
        )


@api_view(["POST", "GET"])
@check_permissions
def claim_submission(request: Request, vm_id: str, submission_uuid: str) -> Response:

    try:
        upload = modeldb.AnonymousUploads.objects.get(uuid=submission_uuid)
    except:
        return HttpResponseServerError(
            json.dumps({"status": 1, "message": f"Run with uuid {html.escape(submission_uuid)} does not exist."})
        )

    if (
        not upload
        or not upload.dataset
        or not upload.dataset.format
        or not upload.dataset.default_task
        or not upload.dataset.default_task.task_id
    ):
        return HttpResponseServerError(json.dumps({"status": 1, "message": f"Unexpected format."}))

    body = request.body.decode("utf-8")
    body = json.loads(body)
    result_dir = Path(settings.TIRA_ROOT) / "data" / "anonymous-uploads" / submission_uuid
    format = json.loads(upload.dataset.format)[0]
    format = secure_filename(format)
    status_code, message = check_format(result_dir, format)

    if status_code != _fmt.OK:
        HttpResponseServerError(json.dumps({"status": 1, "message": message}))

    task_id = upload.dataset.default_task.task_id
    dataset_id = upload.dataset.dataset_id

    if "upload_group" not in body:
        body["upload_group"] = model.add_upload(task_id, vm_id)["id"]
        model.model.update_upload_metadata(
            task_id, vm_id, body["upload_group"], body["display_name"], body["description"], body["paper_link"]
        )

    tmp_dir = temporary_directory()
    uploaded_file = tmp_dir / format
    with open(uploaded_file, "w") as f:
        for l in lines_if_valid(result_dir, format):
            f.write(l.strip() + "\n")

    status_code, message = check_format(tmp_dir, format)
    if status_code != _fmt.OK:
        HttpResponseServerError(json.dumps({"status": 1, "message": message}))

    class MockedResponse:
        name = uploaded_file.name

        def chunks(self):
            with open(uploaded_file, "rb") as f:
                all_bytes = f.read()

            return [all_bytes]

    new_run = model.model.add_uploaded_run(task_id, vm_id, dataset_id, body["upload_group"], MockedResponse())
    if model.git_pipeline_is_enabled_for_task(task_id, cache):
        run_eval(request=request, vm_id=vm_id, dataset_id=dataset_id, run_id=new_run["run"]["run_id"])

    return Response({"upload_group": body["upload_group"], "status": "0"})


endpoints = [
    path("claim/<str:vm_id>/<str:submission_uuid>", claim_submission),
    path("<str:submission_uuid>", read_anonymous_submission),
]
