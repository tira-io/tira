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


@check_permissions
@check_resources_exist('json')
@add_context
def get_evaluations_by_dataset(request, context, task_id, dataset_id):
    role = context["role"]

    # For all users: compile the results table from the evaluations
    vm_ids = model.get_vms_by_dataset(dataset_id)
    # This enforces an order to the measures, since they differ between datasets and are rendered dynamically
    vm_reviews = {vm_id: model.get_vm_reviews_by_dataset(dataset_id, vm_id) for vm_id in vm_ids}

    ev_keys, evaluations = model.get_evaluations_with_keys_by_dataset(vm_ids, dataset_id,
                                                                      vm_reviews if role == "admin" else None)
    

    context["task_id"] = task_id
    context["dataset_id"] = dataset_id     # probably unnecessary since given by call
    context["ev_keys"] = ev_keys
    context["evaluations"] = evaluations

    # TODO: set status, message
    return JsonResponse({"context": context})


@check_permissions
@check_resources_exist("json")
@add_context
def get_runs_by_dataset(request, context, task_id, dataset_id):
    role = context["role"]

    vm_ids = model.get_vms_by_dataset(dataset_id)
    # This enforces an order to the measures, since they differ between datasets and are rendered dynamically
    vm_reviews = {vm_id: model.get_vm_reviews_by_dataset(dataset_id, vm_id) for vm_id in vm_ids}

    vms = model.get_vms_with_reviews(vm_ids, dataset_id, vm_reviews) if role == "admin" else None

    context["task_id"] = task_id
    context["dataset_id"] = dataset_id
    context["vms"] = vms

    # TODO: set status, message
    return JsonResponse({"context": context})
