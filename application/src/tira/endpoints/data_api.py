import logging
from tira.forms import *
import tira.tira_model as model
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.views import add_context

from django.http import JsonResponse
from django.conf import settings

include_navigation = True if settings.DEPLOYMENT == "legacy" else False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


@check_resources_exist('json')
def get_dataset_for_task(request, task_id):
    if request.method == 'GET':
        try:
            datasets = model.get_datasets_by_task(task_id)
            return JsonResponse({"status": "0", "datasets": datasets, "message": f"Encountered an exception: {e}"})
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"status": "0", "message": f"Encountered an exception: {e}"})


@check_resources_exist('json')
@add_context
def get_evaluations_by_dataset(request, context, task_id, dataset_id):
    role = context["role"]
    ev_keys, evaluations = model.get_evaluations_with_keys_by_dataset(dataset_id, True if role == "admin" else None)

    context["task_id"] = task_id
    context["dataset_id"] = dataset_id     # probably unnecessary since given by call
    context["task_id"] = task_id
    context["dataset_id"] = dataset_id
    context["ev_keys"] = ev_keys
    context["evaluations"] = evaluations

    return JsonResponse({'status': 1, "context": context})


@check_resources_exist("json")
@add_context
def get_submissions_by_dataset(request, context, task_id, dataset_id):
    role = context["role"]
    vms = model.get_vms_with_reviews(dataset_id) if role == "admin" else None

    context["task_id"] = task_id
    context["dataset_id"] = dataset_id
    context["vms"] = vms

    return JsonResponse({'status': 1, "context": context})


@check_permissions
@check_resources_exist("json")
@add_context
def get_ova_list(request, context):
    context["ova_list"] = model.get_ova_list()
    return JsonResponse({'status': 0, "context": context})


@check_permissions
@check_resources_exist("json")
@add_context
def get_host_list(request, context):
    context["host_list"] = model.get_host_list()
    return JsonResponse({'status': 0, "context": context})


@check_permissions
@check_resources_exist("json")
@add_context
def get_organizer_list(request, context):
    context["organizer_list"] = model.get_organizer_list()
    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_task_list(request, context):
    context["task_list"] = model.get_tasks()
    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_task(request, context, task_id):
    context["task"] = model.get_task(task_id)
    return JsonResponse({'status': 0, "context": context})