import html
import io
import json
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, HttpResponse, HttpResponseServerError
from django.urls import path
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from tira.check_format import _fmt, check_format
from tira.evaluators import unsandboxed_evaluation_is_allowed
from tira.io_utils import zip_dir
from tira.third_party_integrations import temporary_directory
from werkzeug.utils import secure_filename

from tira_app.endpoints.vm_api import load_notebook

from ... import model as modeldb
from ... import tira_model as model
from ...checks import check_permissions, check_resources_exist
from ..vm_api import run_eval, run_unsandboxed_eval

if TYPE_CHECKING:
    from typing import Any, Iterable

# TODO: this file needs to be refactored to use ModelSerializer and ModelViewSet


@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
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
        ret_serialized = {
            "uuid": ret.uuid,
            "dataset_id": ret.dataset.dataset_id,
            "created": ret.created,
            "has_metadata": ret.has_metadata,
            "metadata_git_repo": ret.metadata_git_repo,
            "metadata_has_notebook": ret.metadata_has_notebook,
        }
        if not ret_serialized["has_metadata"]:
            del ret_serialized["metadata_git_repo"]
            del ret_serialized["metadata_has_notebook"]

        if ret_serialized["has_metadata"]:
            try:
                ret_serialized["available_metadata"] = json.loads(ret.valid_formats)["ir_metadata"]
            except:
                pass

        return Response(ret_serialized)
    except Exception as e:
        return HttpResponseServerError(
            json.dumps({"status": 1, "message": f"Run with uuid {html.escape(submission_uuid)} does not exist."})
        )


@api_view(["GET"])
@permission_classes([])
@authentication_classes([])
def download_anonymous_submission(request: Request, submission_uuid: str) -> Response:
    """Download an anonymous submission identified by the ownership uuid.

    Args:
        request (Request): The request that triggered the REST API call.
        submission_uuid (str): The ownership uuid of the anonymous submission

    Returns:
        Response: The uploaded data
    """
    submission_uuid = secure_filename(submission_uuid).replace(".zip", "")
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
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Unexpected format."}))

    result_dir = Path(settings.TIRA_ROOT) / "data" / "anonymous-uploads" / submission_uuid

    ret = io.BytesIO()
    with zipfile.ZipFile(ret, "w") as zipf:
        for f in result_dir.rglob("*"):
            zipf.write(f, arcname=f.relative_to(result_dir.parent))

    ret.seek(0)
    return FileResponse(ret, as_attachment=True, filename=f"{submission_uuid}.zip")


def check_format_for_dataset(directory, dataset):
    format = json.loads(dataset.format)
    format_configuration = None
    if dataset and dataset.format_configuration:
        try:
            format_configuration = json.loads(dataset.format_configuration)
        except:
            pass
    return check_format(directory, format, format_configuration)


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
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Unexpected format."}))

    body = request.body.decode("utf-8")
    body = json.loads(body)
    result_dir = Path(settings.TIRA_ROOT) / "data" / "anonymous-uploads" / submission_uuid

    status_code, message = check_format_for_dataset(result_dir, upload.dataset)
    if status_code != _fmt.OK:
        return HttpResponseServerError(json.dumps({"status": 1, "message": message}))

    task_id = upload.dataset.default_task.task_id
    dataset_id = upload.dataset.dataset_id

    if "upload_group" not in body:
        body["upload_group"] = model.add_upload(task_id, vm_id)["id"]
        model.model.update_upload_metadata(
            task_id, vm_id, body["upload_group"], body["display_name"], body["description"], body["paper_link"]
        )

    zipped_result_dir = zip_dir(result_dir)

    class MockedResponse:
        name = zipped_result_dir.name

        def chunks(self):
            with open(zipped_result_dir, "rb") as f:
                all_bytes = f.read()

            return [all_bytes]

    new_run = model.model.add_uploaded_run(task_id, vm_id, dataset_id, body["upload_group"], MockedResponse())

    if unsandboxed_evaluation_is_allowed(model.model._dataset_to_dict(upload.dataset)):
        run_unsandboxed_eval(vm_id=vm_id, dataset_id=dataset_id, run_id=new_run["run"]["run_id"])
    elif model.git_pipeline_is_enabled_for_task(task_id, cache):
        run_eval(request=request, vm_id=vm_id, dataset_id=dataset_id, run_id=new_run["run"]["run_id"])

    return Response({"upload_group": body["upload_group"], "status": "0"})


def reorganize_metadata(all_metadata, metadata):
    ret = all_metadata[metadata].copy()
    ret = {i: ret[i] for i in ["method", "platform", "schema version"] if i in ret}
    if (
        "platform" in ret
        and "hardware" in ret["platform"]
        and "frequency" in ret["platform"]["hardware"].get("cpu", {})
    ):
        del ret["platform"]["hardware"]["cpu"]["frequency"]

    if "resources" in all_metadata[metadata] and "runtime" in all_metadata[metadata]["resources"]:
        ret["resources"] = {"runtime": all_metadata[metadata]["resources"]["runtime"]}

    if "implementation" in all_metadata[metadata] and "source" in all_metadata[metadata]["implementation"]:
        ret["implementation"] = {"source": all_metadata[metadata]["implementation"]["source"]}
        if "script" in all_metadata[metadata]["implementation"]:
            ret["implementation"]["script"] = all_metadata[metadata]["implementation"]["script"]

    raw_metadata = yaml.dump(ret)

    if "resources" in all_metadata[metadata]:
        tmp = {}

        for prefix in ["", "vram "]:
            for i in ["cpu", "gpu", "ram"]:
                if i not in all_metadata[metadata]["resources"]:
                    continue
                v = {}
                for c in ["system", "process"]:
                    if f"{prefix}used {c}" not in all_metadata[metadata]["resources"][i]:
                        continue
                    if "timeseries" not in all_metadata[metadata]["resources"][i][f"{prefix}used {c}"]:
                        continue
                    if "values" not in all_metadata[metadata]["resources"][i][f"{prefix}used {c}"]["timeseries"]:
                        continue
                    if "timestamps" not in all_metadata[metadata]["resources"][i][f"{prefix}used {c}"]["timeseries"]:
                        continue

                    timestamps = all_metadata[metadata]["resources"][i][f"{prefix}used {c}"]["timeseries"]["timestamps"]
                    timestamps = [int(i.split("ms")[0].strip()) for i in timestamps]
                    vals: Iterable[tuple[Any, int]] = zip(
                        all_metadata[metadata]["resources"][i][f"{prefix}used {c}"]["timeseries"]["values"],
                        timestamps,
                    )
                    if prefix == "vram ":
                        vals = [(i[0] * 1024, i[1]) for i in vals]
                    v[c] = [{"x": i[1], "y": i[0]} for i in vals]

                if len(v.keys()) == 0:
                    continue

                name = i
                if prefix:
                    name += " (" + prefix.strip() + ")"
                tmp[name] = v

        ret["resources"] = tmp
    return {"metadata": ret, "raw_metadata": raw_metadata, "status": "0"}


@api_view(["GET"])
def render_metadata_of_submission(request: "Request", submission_uuid: str, metadata: str) -> Response:
    try:
        upload = modeldb.AnonymousUploads.objects.get(uuid=submission_uuid)
    except:
        return HttpResponseServerError(
            json.dumps({"status": 1, "message": f"Run with uuid {html.escape(submission_uuid)} does not exist."})
        )
    all_metadata = upload.ir_metadata_record(metadata)
    if metadata in all_metadata:
        return Response(reorganize_metadata(all_metadata, metadata))
    else:
        return HttpResponseServerError(
            json.dumps({"status": 1, "message": f"Metadata with name {html.escape(metadata)} does not exist."})
        )


@api_view(["GET"])
def render_notebook_of_submission(request: Request, submission_uuid: str) -> Response:
    """Read information about an anonymous submission identified by the ownership uuid.

    Args:
        request (Request): The request that triggered the REST API call.
        submission_uuid (str): The ownership uuid of the anonymous submission

    Returns:
        Response: The rendered jupyter notebook.
    """
    try:
        upload = modeldb.AnonymousUploads.objects.get(uuid=submission_uuid)
    except:
        return HttpResponseServerError(
            json.dumps({"status": 1, "message": f"Run with uuid {html.escape(submission_uuid)} does not exist."})
        )

    if not upload.has_metadata or not upload.metadata_has_notebook:
        return HttpResponseServerError(
            json.dumps(
                {"status": 1, "message": f"Run with uuid {html.escape(submission_uuid)} has no jupyter notebook."}
            )
        )
    metadata = load_notebook(upload.get_path_in_file_system())

    if not metadata or "notebook_html" not in metadata:
        return HttpResponseServerError(
            json.dumps(
                {
                    "status": 1,
                    "message": f"Could not render Jupyter Notebook of run with uuid {html.escape(submission_uuid)}.",
                }
            )
        )

    return HttpResponse(metadata["notebook_html"])


endpoints = [
    path("claim/<str:vm_id>/<str:submission_uuid>", claim_submission),
    path("view/<str:submission_uuid>/jupyter-notebook.html", render_notebook_of_submission),
    path("view/<str:submission_uuid>/metadata/<str:metadata>", render_metadata_of_submission),
    path("<str:submission_uuid>.zip", download_anonymous_submission),
    path("<str:submission_uuid>", read_anonymous_submission),
]
