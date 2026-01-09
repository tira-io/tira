import html
import io
import json
import logging
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from django.conf import settings
from django.core.cache import cache
from django.http import FileResponse, HttpResponse, HttpResponseServerError, JsonResponse
from django.urls import path
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from tira.check_format import _fmt, check_format
from tira.evaluators import unsandboxed_evaluation_is_allowed
from tira.io_utils import zip_dir
from tira.third_party_integrations import temporary_directory
from werkzeug.utils import secure_filename

from ... import tira_model as model
from ...checks import check_conditional_permissions
from ..vm_api import _run_evaluation


@check_conditional_permissions(restricted=True)
def upload_response(request: Request, dataset_id: str, vm_id: str) -> Response:
    if request.method != "POST":
        return HttpResponseServerError(json.dumps({"status": 1, "message": "Only Post allowed."}))

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
        run_id = archive.open("run.prototext", "r").read().decode("utf-8").split('runId: "')[1].split('"')[0]
        target_directory = model.model.runs_dir_path / dataset_id / vm_id / run_id
        target_directory.mkdir(parents=True, exist_ok=True)
        archive.extractall(target_directory)
        model.add_run(dataset_id, vm_id, run_id)
        if "-evaluates-" not in run_id:
            _run_evaluation(vm_id, dataset["task"], run_id, dataset_id)

    return JsonResponse({"status": 0, "message": "ok"})


endpoints = [
    path("upload-response/<str:dataset_id>/<str:vm_id>", upload_response),
]
