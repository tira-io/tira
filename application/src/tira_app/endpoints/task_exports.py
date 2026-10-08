"""Server-side functions backing the task's custom "export buttons" (see Task.export_buttons / EditTask.vue).

Each export function is registered in TASK_EXPORT_FUNCTIONS under the "value" key that admins can select for a
task's export buttons (see model.SUPPORTED_TASK_EXPORT_FUNCTIONS, which must be kept in sync with this registry).
"""

import io
import logging
import zipfile
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable, Dict

from django.http import HttpResponse, JsonResponse

from .. import tira_model as model
from ..checks import check_permissions, check_resources_exist

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger("tira")


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


TASK_EXPORT_FUNCTIONS: "Dict[str, Callable[[str, dict], HttpResponse]]" = {
    "example-zip-export": _example_zip_export,
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

    return export_function(task_id, task)
