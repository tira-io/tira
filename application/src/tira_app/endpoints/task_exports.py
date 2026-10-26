"""Server-side functions backing the task's custom "export buttons" (see Task.export_buttons / EditTask.vue).

Each export function is registered in TASK_EXPORT_FUNCTIONS under the "value" key that admins can select for a
task's export buttons (see model.SUPPORTED_TASK_EXPORT_FUNCTIONS, which must be kept in sync with this registry).
"""

import hashlib
import io
import logging
import re
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


_TREC_RUN_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def valid_trec_run_id(run_id: "Optional[str]") -> bool:
    """Return True iff ``run_id`` is a valid run identifier for the trec-auto-judge export, i.e., it is a string
    that is longer than 3 and shorter than 20 characters and consists only of the characters a-z, A-Z, 0-9, '-',
    and '_'. Used to guard against malformed/unsafe run ids (e.g., containing path separators) ending up as
    directory names inside the exported zip (see _bundle_trec_auto_judge_submission)."""
    if not isinstance(run_id, str):
        return False
    if not (3 < len(run_id) < 20):
        return False
    return bool(_TREC_RUN_ID_PATTERN.fullmatch(run_id))


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
    task_id: str,
    vm_id: str,
    name: str,
    runs: "Optional[List[Dict[str, Any]]]",
    sanitized_submission: "dict[str, Any]",
    submission_key: str,
    evalbase_team_id: str,
    allow_incomplete: bool = False,
) -> None:
    """Bundle a single trec-auto-judge submission (either a docker software's code submission or an uploaded-run
    submission) into ``outer_zip``. Runs whose run_id is not a valid_trec_run_id are skipped and do not count
    towards a dataset's coverage. Unless ``allow_incomplete`` is True (see
    _allow_incomplete_trec_auto_judge_names), raises an ExportError if, after checking the file system for
    actual run output (see _run_output_files), the submission does not have at least one qualifying run for
    every TREC_AUTO_JUDGE_DATASETS dataset (i.e., it does not have one submission per target dataset).

    Writes a "{name}.zip" (bundling the on-disk run outputs for whichever required datasets are covered) and a
    sibling "{name}.yaml" (with zip size/md5sum, ``sanitized_submission`` under ``submission_key``, and an
    "evalbase.team_id" set to ``evalbase_team_id``) into ``outer_zip``.
    """
    runs_by_dataset = _runs_on_required_datasets(runs)

    software_buffer = io.BytesIO()
    datasets_with_output_on_disk = set()
    with zipfile.ZipFile(software_buffer, "w", zipfile.ZIP_DEFLATED) as software_zip:
        for dataset, arc_prefix in TREC_AUTO_JUDGE_DATASETS.items():
            for run in runs_by_dataset.get(dataset, []):
                run_id = run.get("run_id")
                if not valid_trec_run_id(run_id):
                    continue
                if not _run_output_files(dataset, vm_id, run_id):
                    continue
                datasets_with_output_on_disk.add(dataset)
                _add_run_to_zip(software_zip, dataset, vm_id, run_id, arc_prefix)

    missing_datasets = set(TREC_AUTO_JUDGE_DATASETS) - datasets_with_output_on_disk
    if missing_datasets and not allow_incomplete:
        raise ExportError(
            f"Submission '{name}' of team '{vm_id}' for task '{task_id}' does not have a qualifying run with "
            f"output on disk for the following required dataset(s): {', '.join(sorted(missing_datasets))}."
        )

    software_zip_bytes = software_buffer.getvalue()
    metadata_yaml = yaml.safe_dump(
        {
            "run_id": name,
            "zip_file": f"{name}.zip",
            "zip_size_bytes": len(software_zip_bytes),
            "zip_md5sum": hashlib.md5(software_zip_bytes).hexdigest(),
            submission_key: sanitized_submission,
            "evalbase": {"team_id": evalbase_team_id},
        },
        sort_keys=False,
        default_flow_style=False,
    )

    outer_zip.writestr(f"{name}.zip", software_zip_bytes)
    outer_zip.writestr(f"{name}.yaml", metadata_yaml)


def _evalbase_team_id_for_trec_auto_judge(task_id: str, task: "dict", vm_id: str) -> str:
    """Resolve the evalbase team id for team ``vm_id`` from the task's task_export_metadata, which is expected
    to be a dict containing a "trec-teams" dict mapping each vm_id to its evalbase_team_id. Raises an
    ExportError if task_export_metadata is missing/not a dict, if it has no "trec-teams" field, or if
    ``vm_id`` is not a key of that field."""
    task_export_metadata = task.get("task_export_metadata")
    if not isinstance(task_export_metadata, dict) or "trec-teams" not in task_export_metadata:
        raise ExportError(
            f"Task '{task_id}' has no 'trec-teams' field in its task export metadata, so the trec-auto-judge "
            "export cannot determine the evalbase team id."
        )

    trec_teams = task_export_metadata["trec-teams"]
    if not isinstance(trec_teams, dict) or vm_id not in trec_teams:
        raise ExportError(
            f"Team '{vm_id}' is not a key of the 'trec-teams' field in task '{task_id}'s task export metadata, "
            "so the trec-auto-judge export cannot determine the evalbase team id."
        )

    return trec_teams[vm_id]


def _translated_trec_auto_judge_name(task: "dict", vm_id: str, name: str) -> str:
    """Translate a trec-auto-judge submission name (as used for the exported ``run_id``, zip/yaml file names,
    see _bundle_trec_auto_judge_submission) using the "trec-run-id-translation" field of the task's
    task_export_metadata (the same metadata dict that also holds "trec-teams", see
    _evalbase_team_id_for_trec_auto_judge). This field, if present, maps each vm_id to a translation dict of
    {original_name: translated_name} for that team. If the field, the team's translation dict, or an entry for
    ``name`` is missing, ``name`` is returned unchanged."""
    task_export_metadata = task.get("task_export_metadata")
    if not isinstance(task_export_metadata, dict):
        return name

    translation_table = task_export_metadata.get("trec-run-id-translation")
    if not isinstance(translation_table, dict):
        return name

    vm_translations = translation_table.get(vm_id)
    if not isinstance(vm_translations, dict):
        return name

    return vm_translations.get(name, name)


def _allow_incomplete_trec_auto_judge_names(task: "dict", vm_id: str) -> "set":
    """Return the set of (already translated, see _translated_trec_auto_judge_name) trec-auto-judge submission
    names that team ``vm_id`` is allowed to have incomplete dataset coverage for (i.e., skip the "one
    submission per target dataset" check in _bundle_trec_auto_judge_submission), per the "allow-incomplete"
    field of the task's task_export_metadata (the same metadata dict that also holds "trec-teams", see
    _evalbase_team_id_for_trec_auto_judge). This field, if present, maps each vm_id to a list of submission
    names permitted to be incomplete. If the field or the team's entry is missing/not of the expected shape, no
    names are allow-listed (i.e., an empty set is returned)."""
    task_export_metadata = task.get("task_export_metadata")
    if not isinstance(task_export_metadata, dict):
        return set()

    allow_incomplete = task_export_metadata.get("allow-incomplete")
    if not isinstance(allow_incomplete, dict):
        return set()

    names = allow_incomplete.get(vm_id)
    if not isinstance(names, list):
        return set()

    return {name for name in names if isinstance(name, str)}


def _merge_trec_auto_judge_uploads(
    task_id: str, vm_id: str, name: str, group: "List[Dict[str, Any]]"
) -> "Dict[str, Any]":
    """Merge a group of uploaded-run submissions that share the same (translated) trec-auto-judge name into a
    single dict, so that they are checked/bundled as one submission. A team may submit its runs for different
    TREC_AUTO_JUDGE_DATASETS as separate upload entries (e.g. one upload per dataset) that happen to share the
    same display name/run_id; without merging, each such entry would individually fail the "one submission per
    target dataset" check even though the team's submissions jointly cover all required datasets. All entries in
    ``group`` must share the same 'description' and the same 'priority' metadata property (see
    _priority_of_submission); otherwise an ExportError is raised, since merging submissions that disagree on
    these fields would silently hide a likely configuration mistake. The merged dict's 'runs' is the
    concatenation of every entry's runs; all other fields are taken from the most recently edited entry (by
    'last_edit')."""
    descriptions = {upload.get("description") for upload in group}
    priorities = {_priority_of_submission(upload.get("upload_metadata")) for upload in group}
    if len(descriptions) > 1 or len(priorities) > 1:
        raise ExportError(
            f"The uploaded-run submissions sharing the name '{name}' of team '{vm_id}' for task '{task_id}' do "
            "not all have the same 'description' and 'priority' metadata, so the trec-auto-judge export cannot "
            "merge them into a single submission."
        )

    merged_runs = [run for upload in group for run in (upload.get("runs") or [])]
    representative = max(group, key=lambda upload: str(upload.get("last_edit") or ""))
    merged = dict(representative)
    merged["runs"] = merged_runs
    return merged


def _trec_auto_judge_export(task_id: str, task: "dict", vm_id: str) -> "HttpResponse":
    """Export for the 'trec-auto-judge' task: for every submission of the team ``vm_id`` -- a code submission
    (docker software) or an uploaded-run submission -- whose 'priority' metadata property parses to an integer
    between 1 and 10 (inclusive), the runs on the TREC_AUTO_JUDGE_DATASETS datasets are first extracted from its
    metadata (see _runs_on_required_datasets). Submission names (the submission's display name, optionally
    translated via the task's task_export_metadata "trec-run-id-translation" field, see
    _translated_trec_auto_judge_name; used as the exported ``run_id``, see _bundle_trec_auto_judge_submission)
    must be valid_trec_run_id, and no docker-software submission may share its name with an uploaded-run
    submission (both are bundled as "{name}.zip"/"{name}.yaml" into the same outer zip); if any qualifying
    submission's name is invalid or collides across the two kinds, the export fails with an ExportError listing
    all offending names instead of silently skipping/overwriting them. Uploaded-run submissions sharing the
    same (translated) name are merged into a single submission before all further checks/bundling (see
    _merge_trec_auto_judge_uploads), since a team may submit its runs for different datasets as separate upload
    entries that happen to share a name. The team's evalbase team id is resolved
    from the task's task_export_metadata (see _evalbase_team_id_for_trec_auto_judge) and embedded as
    "evalbase.team_id" in every exported yaml file. Every qualifying submission must have, after checking the
    file system for actual run output (see _run_output_files), at least one qualifying run per required dataset
    (see _bundle_trec_auto_judge_submission); if any submission does not (i.e. it lacks one submission per
    target dataset), the export fails with an ExportError listing all such submissions instead of silently
    excluding them, unless the submission's (translated) name is allow-listed as allowed to be incomplete for
    this team via the task's task_export_metadata "allow-incomplete" field (see
    _allow_incomplete_trec_auto_judge_names), in which case it is still bundled with whatever output exists.
    Qualifying submissions are bundled into a zip named after the (possibly translated) submission name, plus a
    sibling yaml file with metadata about that zip (size, md5sum) and the submission itself. All these
    per-submission zip/yaml pairs are collected into one zip that is returned to the caller."""
    evalbase_team_id = _evalbase_team_id_for_trec_auto_judge(task_id, task, vm_id)

    docker_softwares = model.get_docker_softwares_with_runs(task_id, vm_id, return_code_submissions=True)
    uploads = model.get_uploads_with_runs(task_id, vm_id)

    qualifying_docker_softwares = []
    invalid_names = []

    for software in docker_softwares:
        if not _is_included_in_trec_auto_judge(software.get("metadata")):
            continue
        name = software.get("display_name") or f"software-{software.get('docker_software_id')}"
        name = _translated_trec_auto_judge_name(task, vm_id, name)
        if not valid_trec_run_id(name):
            invalid_names.append(name)
            continue
        qualifying_docker_softwares.append((name, software))

    upload_groups: "Dict[str, List[Dict[str, Any]]]" = {}
    for upload in uploads:
        if not _is_included_in_trec_auto_judge(upload.get("upload_metadata")):
            continue
        name = upload.get("display_name") or f"upload-{upload.get('id')}"
        name = _translated_trec_auto_judge_name(task, vm_id, name)
        if not valid_trec_run_id(name):
            invalid_names.append(name)
            continue
        upload_groups.setdefault(name, []).append(upload)

    if invalid_names:
        raise ExportError(
            f"The following submission names of team '{vm_id}' for task '{task_id}' are not valid "
            f"trec-auto-judge run ids (must be between 4 and 19 characters long and consist only of "
            f"a-z, A-Z, 0-9, '-', and '_'): {', '.join(sorted(invalid_names))}."
        )

    # Merge uploaded-run submissions sharing the same name (e.g. one upload per required dataset) into a single
    # submission each, see _merge_trec_auto_judge_uploads.
    qualifying_uploads = [
        (name, _merge_trec_auto_judge_uploads(task_id, vm_id, name, group)) for name, group in upload_groups.items()
    ]

    docker_names = {name for name, _ in qualifying_docker_softwares}
    upload_names = {name for name, _ in qualifying_uploads}
    colliding_names = docker_names & upload_names
    if colliding_names:
        raise ExportError(
            f"The following submission names of team '{vm_id}' for task '{task_id}' are used by both a "
            "docker-software submission and an uploaded-run submission, so the trec-auto-judge export would "
            f"overwrite one with the other: {', '.join(sorted(colliding_names))}."
        )

    if not qualifying_docker_softwares and not qualifying_uploads:
        raise ExportError(
            f"No submission of team '{vm_id}' for task '{task_id}' has a 'priority' metadata property between "
            "1 and 10, so the trec-auto-judge export would be empty."
        )

    allow_incomplete_names = _allow_incomplete_trec_auto_judge_names(task, vm_id)

    buffer = io.BytesIO()
    coverage_errors = []
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as outer_zip:
        for name, software in qualifying_docker_softwares:
            try:
                _bundle_trec_auto_judge_submission(
                    outer_zip,
                    task_id,
                    vm_id,
                    name,
                    software.get("runs"),
                    _sanitized_trec_auto_judge_submission(software),
                    "tira_code_submission",
                    evalbase_team_id,
                    allow_incomplete=name in allow_incomplete_names,
                )
            except ExportError as e:
                coverage_errors.append(str(e))

        for name, upload in qualifying_uploads:
            try:
                _bundle_trec_auto_judge_submission(
                    outer_zip,
                    task_id,
                    vm_id,
                    name,
                    upload.get("runs"),
                    _sanitized_trec_auto_judge_submission(upload, excluded_fields={"runs"}),
                    "tira_upload_submission",
                    evalbase_team_id,
                    allow_incomplete=name in allow_incomplete_names,
                )
            except ExportError as e:
                coverage_errors.append(str(e))

    if coverage_errors:
        raise ExportError(" ".join(coverage_errors))

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
