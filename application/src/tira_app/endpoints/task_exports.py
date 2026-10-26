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

# Submission (docker software) fields excluded from the "tira_code_submission" metadata embedded in the
# trec-auto-judge export's per-submission yaml file, e.g. because they are internal/irrelevant to judges or
# would bloat the file (the full per-dataset run list is already contained in the sibling zip).
TREC_AUTO_JUDGE_EXCLUDED_SUBMISSION_FIELDS = {
    "user_image_name",
    "tira_image_name",
    "input_docker_software",
    "input_docker_software_id",
    "input_upload_id",
    "ir_re_ranker",
    "public_image_name",
    "ir_re_ranking_input",
    "previous_stages",
    "tira_image_workdir",
    "link_code",
    "mount_hf_model",
    "workflow_configuration",
    "allow_network_access_on_request",
    "try_run_metadata",
    "runs",
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


def _runs_on_required_datasets(
    runs: "Optional[List[Dict[str, Any]]]",
) -> "Dict[str, List[Dict[str, Any]]]":
    """Extract the submission's (non-evaluation) runs on the datasets required by the trec-auto-judge export
    (TREC_AUTO_JUDGE_DATASETS), grouped by dataset. This is only a first, metadata-based filtering step; whether
    a dataset actually counts as "covered" is decided afterwards by checking the file system for actual run
    output (see _trec_auto_judge_export)."""
    grouped: "Dict[str, List[Dict[str, Any]]]" = {dataset: [] for dataset in TREC_AUTO_JUDGE_DATASETS}
    for run in runs or []:
        if run.get("is_evaluation"):
            continue
        dataset = run.get("dataset")
        if dataset in grouped:
            grouped[dataset].append(run)
    return grouped


def _sanitized_trec_auto_judge_submission(
    submission: "dict", excluded_fields: "Optional[set]" = None
) -> "dict[str, Any]":
    """Return a copy of the submission dict with the given fields removed (defaulting to
    TREC_AUTO_JUDGE_EXCLUDED_SUBMISSION_FIELDS, which is tailored to docker software submissions), for embedding
    in the trec-auto-judge export's per-submission yaml file. The raw per-run 'runs' list is always dropped,
    since the actual runs are already contained in the sibling zip."""
    if excluded_fields is None:
        excluded_fields = TREC_AUTO_JUDGE_EXCLUDED_SUBMISSION_FIELDS
    return {k: v for k, v in submission.items() if k not in excluded_fields}


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


def _bundle_trec_auto_judge_submission(
    outer_zip: "zipfile.ZipFile",
    vm_id: str,
    name: str,
    runs: "Optional[List[Dict[str, Any]]]",
    sanitized_submission: "dict[str, Any]",
    submission_key: str,
) -> bool:
    """Bundle a single trec-auto-judge submission (either a docker software's code submission or an uploaded-run
    submission) into ``outer_zip``, iff, after checking the file system for actual run output
    (see _run_output_files), both TREC_AUTO_JUDGE_DATASETS datasets have at least one run with output on disk.

    Writes a "{name}.zip" (bundling the on-disk run outputs) and a sibling "{name}.yaml" (with zip
    size/md5sum and ``sanitized_submission`` under ``submission_key``) into ``outer_zip``.

    Returns whether the submission was included (i.e., whether both required datasets had output on disk).
    """
    runs_by_dataset = _runs_on_required_datasets(runs)

    software_buffer = io.BytesIO()
    datasets_with_output_on_disk = set()
    with zipfile.ZipFile(software_buffer, "w", zipfile.ZIP_DEFLATED) as software_zip:
        for dataset, arc_prefix in TREC_AUTO_JUDGE_DATASETS.items():
            for run in runs_by_dataset.get(dataset, []):
                if not _run_output_files(dataset, vm_id, run["run_id"]):
                    continue
                datasets_with_output_on_disk.add(dataset)
                _add_run_to_zip(software_zip, dataset, vm_id, run["run_id"], arc_prefix)

    if not set(TREC_AUTO_JUDGE_DATASETS).issubset(datasets_with_output_on_disk):
        return False

    software_zip_bytes = software_buffer.getvalue()
    metadata_yaml = yaml.safe_dump(
        {
            "run_id": name,
            "zip_file": f"{name}.zip",
            "zip_size_bytes": len(software_zip_bytes),
            "zip_md5sum": hashlib.md5(software_zip_bytes).hexdigest(),
            submission_key: sanitized_submission,
        },
        sort_keys=False,
        default_flow_style=False,
    )

    outer_zip.writestr(f"{name}.zip", software_zip_bytes)
    outer_zip.writestr(f"{name}.yaml", metadata_yaml)
    return True


def _trec_auto_judge_export(task_id: str, task: "dict", vm_id: str) -> "HttpResponse":
    """Export for the 'trec-auto-judge' task: for every submission of the team ``vm_id`` -- a code submission
    (docker software) or an uploaded-run submission -- whose 'priority' metadata property parses to an integer
    between 1 and 10 (inclusive), the runs on the TREC_AUTO_JUDGE_DATASETS datasets are first extracted from its
    metadata (see _runs_on_required_datasets). The submission is only included in the export if, after checking
    the file system for actual run output (see _run_output_files), both required datasets have at least one run
    with output on disk (see _bundle_trec_auto_judge_submission). Included submissions are bundled into a zip
    named after the submission, plus a sibling yaml file with metadata about that zip (size, md5sum) and the
    submission itself. All these per-submission zip/yaml pairs are collected into one zip that is returned to
    the caller."""
    docker_softwares = model.get_docker_softwares_with_runs(task_id, vm_id, return_code_submissions=True)
    uploads = model.get_uploads_with_runs(task_id, vm_id)

    buffer = io.BytesIO()
    included_any = False
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as outer_zip:
        for software in docker_softwares:
            if not _is_included_in_trec_auto_judge(software.get("metadata")):
                continue

            name = software.get("display_name") or f"software-{software.get('docker_software_id')}"
            included_any = (
                _bundle_trec_auto_judge_submission(
                    outer_zip,
                    vm_id,
                    name,
                    software.get("runs"),
                    _sanitized_trec_auto_judge_submission(software),
                    "tira_code_submission",
                )
                or included_any
            )

        for upload in uploads:
            if not _is_included_in_trec_auto_judge(upload.get("upload_metadata")):
                continue

            display_name = upload.get("display_name") or f"upload-{upload.get('id')}"
            # Suffixed to avoid clashing with a docker software's zip/yaml of the same display name.
            name = f"{display_name} (upload)"
            included_any = (
                _bundle_trec_auto_judge_submission(
                    outer_zip,
                    vm_id,
                    name,
                    upload.get("runs"),
                    _sanitized_trec_auto_judge_submission(upload, excluded_fields={"runs"}),
                    "tira_upload_submission",
                )
                or included_any
            )

    if not included_any:
        raise ExportError(
            f"No submission of team '{vm_id}' for task '{task_id}' has both a 'priority' metadata property "
            "between 1 and 10 and run output on disk for both "
            f"{' and '.join(TREC_AUTO_JUDGE_DATASETS)}, so the trec-auto-judge export would be empty."
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
