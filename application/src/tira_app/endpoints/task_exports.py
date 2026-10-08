"""Server-side functions backing the task's custom "export buttons" (see Task.export_buttons / EditTask.vue).

Each export function is registered in TASK_EXPORT_FUNCTIONS under the "value" key that admins can select for a
task's export buttons (see model.SUPPORTED_TASK_EXPORT_FUNCTIONS, which must be kept in sync with this registry).
"""

import hashlib
import io
import logging
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import yaml
from django.conf import settings
from django.http import HttpResponse, JsonResponse

from .. import tira_model as model
from ..checks import check_permissions, check_resources_exist

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger("tira")


class ExportError(Exception):
    """Raised by an export function when the requested export cannot be produced (e.g., it would be empty).
    The exception's message is returned to and shown by the client."""


# Datasets considered by the "trec-auto-judge" export, mapped to the short directory name used inside the
# per-software export zip (see _trec_auto_judge_export).
TREC_AUTO_JUDGE_DATASETS = {
    "rag26-20260827_1-test": "rag26",
    "ragtime26-20260827-test": "ragtime26",
}


def _example_zip_export(task_id: str, task: "dict") -> "HttpResponse":
    """Scaffold export function that returns a zip containing a single small file. Serves as a working example
    for implementing further task export functions."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zipf:
        content = (
            f"Task: {task.get('task_name', task_id)} ({task_id})\n"
            f"Exported: {datetime.now(timezone.utc).isoformat()}\n"
        )
        zipf.writestr("export.txt", content)

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{task_id}-export.zip"'
    return response


def _priority_of_submission(metadata: "Optional[Dict[str, Any]]") -> "Optional[int]":
    """Parse the submission's 'priority' metadata property (case-insensitive key match) as an int, or None if it
    is missing or not parseable as an integer."""
    if not metadata:
        return None

    for key, value in metadata.items():
        if str(key).strip().lower() == "priority":
            try:
                return int(str(value).strip())
            except (TypeError, ValueError):
                return None

    return None


def _is_included_in_trec_auto_judge(metadata: "Optional[Dict[str, Any]]") -> bool:
    """A submission is included in the trec-auto-judge export iff its 'priority' metadata property parses to an
    integer between 1 and 10 (inclusive)."""
    priority = _priority_of_submission(metadata)
    return priority is not None and 1 <= priority <= 10


def _run_output_files(dataset_id: str, vm_id: str, run_id: str) -> "List[Path]":
    """Return the list of output files of a run. Extracted as its own function so that it can be mocked in
    tests instead of requiring real files on disk."""
    run_output_dir = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id / "output"
    if not run_output_dir.is_dir():
        return []

    return [f for f in sorted(run_output_dir.rglob("*")) if f.is_file()]


def _add_run_to_zip(zipf: "zipfile.ZipFile", dataset_id: str, vm_id: str, run_id: str, arc_prefix: str) -> None:
    run_output_dir = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id / "output"
    for f in _run_output_files(dataset_id, vm_id, run_id):
        zipf.write(f, arcname=f"{arc_prefix}/{run_id}/{f.relative_to(run_output_dir)}")


def _trec_auto_judge_export(task_id: str, task: "dict", vm_id: str) -> "HttpResponse":
    """Export for the 'trec-auto-judge' task: for every code submission (docker software) of the team ``vm_id``
    whose 'priority' metadata property parses to an integer between 1 and 10 (inclusive), bundle the outputs of
    all its runs on the TREC_AUTO_JUDGE_DATASETS datasets into a zip named after the software, plus a sibling
    yaml file with metadata about that zip (size, md5sum) and the submission itself. All these per-software
    zip/yaml pairs are collected into one zip that is returned to the caller."""
    docker_softwares = model.get_docker_softwares_with_runs(task_id, vm_id, return_code_submissions=True)

    buffer = io.BytesIO()
    included_any = False
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as outer_zip:
        for software in docker_softwares:
            if not _is_included_in_trec_auto_judge(software.get("metadata")):
                continue
            included_any = True

            display_name = software.get("display_name") or f"software-{software.get('docker_software_id')}"

            software_buffer = io.BytesIO()
            with zipfile.ZipFile(software_buffer, "w", zipfile.ZIP_DEFLATED) as software_zip:
                for run in software.get("runs") or []:
                    if run.get("is_evaluation"):
                        continue
                    arc_prefix = TREC_AUTO_JUDGE_DATASETS.get(run.get("dataset"))
                    if arc_prefix is None:
                        continue
                    _add_run_to_zip(software_zip, run["dataset"], vm_id, run["run_id"], arc_prefix)

            software_zip_bytes = software_buffer.getvalue()
            metadata_yaml = yaml.safe_dump(
                {
                    "zip_size_bytes": len(software_zip_bytes),
                    "zip_md5sum": hashlib.md5(software_zip_bytes).hexdigest(),
                    "submission": software,
                },
                sort_keys=False,
                default_flow_style=False,
            )

            outer_zip.writestr(f"{display_name}.zip", software_zip_bytes)
            outer_zip.writestr(f"{display_name}.yaml", metadata_yaml)

    if not included_any:
        raise ExportError(
            f"No code submission of team '{vm_id}' for task '{task_id}' has a 'priority' metadata property "
            "between 1 and 10, so the trec-auto-judge export would be empty."
        )

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{task_id}-trec-auto-judge-export.zip"'
    return response


TASK_EXPORT_FUNCTIONS: "Dict[str, Callable[[str, dict, str], HttpResponse]]" = {
    "example-zip-export": lambda task_id, task, vm_id: _example_zip_export(task_id, task),
    "trec-auto-judge": _trec_auto_judge_export,
}


@check_permissions
@check_resources_exist("json")
def task_export(request: "HttpRequest", task_id: str, vm_id: str, value: str) -> "HttpResponse":
    """Serve a task's configured custom export button. The requested value must both be registered in
    TASK_EXPORT_FUNCTIONS and configured for the task via its export_buttons admin setting."""
    task = model.get_task(task_id)
    configured_values = {button["value"] for button in (task.get("export_buttons") or [])}
    if value not in configured_values:
        return JsonResponse(
            {"status": 1, "message": f"Export '{value}' is not configured for task {task_id}."}, status=404
        )

    export_function = TASK_EXPORT_FUNCTIONS.get(value)
    if export_function is None:
        logger.error(f"Export function '{value}' is configured for task {task_id} but not implemented.")
        return JsonResponse({"status": 1, "message": f"Export '{value}' is not implemented."}, status=501)

    try:
        return export_function(task_id, task, vm_id)
    except ExportError as e:
        return JsonResponse({"status": 1, "message": str(e)}, status=400)
