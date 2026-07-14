import logging

from django.http import HttpResponseNotAllowed, JsonResponse

from .. import tira_model as model
from ..authentication import auth
from ..checks import check_conditional_permissions, check_permissions, check_resources_exist

include_navigation = False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")

# ---------------------------------------------------------------------
#   Review actions
# ---------------------------------------------------------------------


@check_permissions
@check_resources_exist("json")
def publish(request, vm_id, dataset_id, run_id, value):
    value = True if value == "true" else False
    if request.method == "GET":
        status = model.update_review(dataset_id, vm_id, run_id, published=value)
        if status:
            context = {"status": "0", "published": value, "message": f"Published is now: {value}"}
        else:
            context = {"status": "1", "published": (not value), "message": f"Published is now: {value}"}
        return JsonResponse(context)


@check_conditional_permissions(restricted=True)
@check_resources_exist("json")
def blind(request, vm_id, dataset_id, run_id, value):
    value = False if value == "false" else True

    if request.method == "GET":
        status = model.update_review(dataset_id, vm_id, run_id, blinded=value)
        if status:
            context = {"status": "0", "blinded": value, "message": f"Blinded is now: {value}"}
        else:
            context = {"status": "1", "blinded": (not value), "message": f"Blinded is now: {value}"}
        return JsonResponse(context)


@check_permissions
@check_resources_exist("json")
def get_count_of_missing_reviews(request, task_id):
    context = {"count_of_missing_reviews": model.get_count_of_missing_reviews(task_id)}
    return JsonResponse({"status": 0, "context": context})


@check_permissions
@check_resources_exist("json")
def get_count_of_team_submissions(request, task_id):
    context = {"count_of_team_submissions": model.get_count_of_team_submissions(task_id)}
    return JsonResponse({"status": 0, "context": context})


@check_resources_exist("json")
def get_count_of_team_software(request, task_id):
    role = auth.get_role(request, user_id=auth.get_user_id(request))
    if role not in (auth.ROLE_ADMIN, auth.ROLE_TIRA):
        return HttpResponseNotAllowed("Access forbidden.")

    context = {"count_of_team_software": model.get_count_of_team_software(task_id)}
    return JsonResponse({"status": 0, "context": context})


@check_resources_exist("json")
def get_count_of_team_software_executions(request, task_id):
    role = auth.get_role(request, user_id=auth.get_user_id(request))
    if role not in (auth.ROLE_ADMIN, auth.ROLE_TIRA):
        return HttpResponseNotAllowed("Access forbidden.")

    context = {"count_of_team_software_executions": model.get_count_of_team_software_executions(task_id)}
    return JsonResponse({"status": 0, "context": context})
