import logging

from tira.authentication import auth
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.forms import *
from django.http import HttpResponse, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from http import HTTPStatus
import json

import tira.tira_model as model

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


def handle_get_model_exceptions(func):
    def decorate(request, *args, **kwargs):
        if request.method == 'GET':
            try:
                msg = func(*args, **kwargs)
                return JsonResponse({'status': 0, 'message': msg}, status=HTTPStatus.OK)
            except Exception as e:
                logger.exception(f"{func.__name__} failed with {e}", e)
                return JsonResponse({'status': 1, 'message': f"{func.__name__} failed with {e}"},
                                    status=HTTPStatus.INTERNAL_SERVER_ERROR)

        return JsonResponse({'status': 1, 'message': f"{request.method} is not allowed."}, status=HTTPStatus.FORBIDDEN)

    return decorate


@check_permissions
@handle_get_model_exceptions
def admin_reload_data():
    model.build_model()
    if auth.get_auth_source() == 'legacy':
        auth.load_legacy_users()
    return "Model data was reloaded successfully"


@check_permissions
@handle_get_model_exceptions
def admin_reload_vms():
    model.reload_vms()
    return "VM data was reloaded successfully"


@check_permissions
@handle_get_model_exceptions
def admin_reload_datasets():
    model.reload_datasets()
    return "Dataset data was reloaded successfully"


@check_permissions
@handle_get_model_exceptions
def admin_reload_tasks():
    model.reload_tasks()
    return "Task data was reloaded successfully"


@check_conditional_permissions(restricted=True)
@handle_get_model_exceptions
def admin_reload_runs(vm_id):
    model.reload_runs(vm_id)
    return "Runs data was reloaded for {} on {} successfully"


@check_permissions
def admin_create_vm(request):  # TODO implement
    """ Hook for create_vm posts. Responds with json objects indicating the state of the create process. """

    if request.method == "POST":
        data = json.loads(request.body)

        return JsonResponse({'status': 0, 'message': f"Not implemented yet, received: {data}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for vm create"})


@check_permissions
def admin_archive_vm():
    return JsonResponse({'status': 1, 'message': f"Not implemented"}, status=HTTPStatus.NOT_IMPLEMENTED)


@check_permissions
def admin_modify_vm(request):
    if request.method == "POST":
        data = json.loads(request.body)

        return JsonResponse({'status': 0, 'message': f"Not implemented yet, received: {data}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for modify vm"})


@check_permissions
def admin_create_task(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """

    if request.method == "POST":
        data = json.loads(request.body)

        task_id = data["task_id"]
        organizer = data["organizer"]

        if not model.organizer_exists(organizer):
            return JsonResponse({'status': 1, 'message': f"Organizer with ID {organizer} does not exist"})
        if model.task_exists(task_id):
            return JsonResponse({'status': 1, 'message': f"Task with ID {task_id} already exist"})

        new_task = model.create_task(task_id, data["name"], data["description"], data["master_id"],
                                     organizer, data["website"],
                                     help_command=data["help_command"], help_text=data["help_text"])
        new_task = json.dumps(new_task, cls=DjangoJSONEncoder)
        return JsonResponse({'status': 0, 'context': new_task,
                             'message': f"Created Task with Id: {data['task_id']}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for vm create"},
                        status=HTTPStatus.NOT_IMPLEMENTED)


@check_permissions
def admin_edit_task(request):
    """ Edit a task. Expects a POST message with all task data. """
    if request.method == "POST":
        data = json.loads(request.body)

        task_id = data["task_id"]
        organizer = data["organizer"]

        if not model.organizer_exists(organizer):
            return JsonResponse({'status': 1, 'message': f"Organizer with ID {organizer} does not exist"})
        if not model.task_exists(task_id):
            return JsonResponse({'status': 1, 'message': f"Task with ID {task_id} does not exist and can't be edited"})

        task = model.edit_task(task_id, data["name"], data["description"], data["master_id"],
                               organizer, data["website"], help_command=data["help_command"],
                               help_text=data["help_text"])

        return JsonResponse({'status': 0, 'context': json.dumps(task, cls=DjangoJSONEncoder),
                             'message': f"Edited Task with Id: {data['task_id']}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit task"})


@check_permissions
def admin_delete_task(request, task_id):
    model.delete_task(task_id)
    return JsonResponse({'status': 0, 'message': f"Deleted task {task_id}"})


@check_permissions
def admin_add_dataset(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """

    context = {}

    if request.method == "POST":
        data = json.loads(request.body)

        dataset_id_prefix = data["dataset_id"]
        dataset_name = data["name"]
        master_vm_id = data["master_id"]
        task_id = data["task"]
        command = data["evaluator_command"]
        working_directory = data["evaluator_working_directory"]
        measures = [line.split(',') for line in data["evaluation_measures"].split('\n')]

        if master_vm_id and not model.vm_exists(master_vm_id):
            return JsonResponse({'status': 1, "message": f"Master VM with ID {master_vm_id} does not exist"})
        if not model.task_exists(task_id):
            return JsonResponse({'status': 1, "message": f"Task with ID {task_id} does not exist"})

        new_datasets = []
        new_paths = []
        if data['training']:
            ds, paths = model.add_dataset(task_id, dataset_id_prefix, "training", dataset_name)
            new_datasets.append(ds)
            new_paths += paths
        if data['dev']:
            ds, paths = model.add_dataset(task_id, dataset_id_prefix, "dev", dataset_name)
            new_datasets.append(ds)
            new_paths += paths
        if data['test']:
            ds, paths = model.add_dataset(task_id, dataset_id_prefix, "test", dataset_name)
            new_datasets.append(ds)
            new_paths += paths

        if master_vm_id and command and measures:
            for nds in new_datasets:
                model.add_evaluator(master_vm_id, task_id, nds['dataset_id'], command, working_directory, measures)
        else:
            return JsonResponse(
                {'status': 0, 'context': new_datasets,
                 'message': f"Created {len(new_datasets)} new datasets, but did not create evaluators (please provide command, master vm, and measures)"})

        return JsonResponse(
            {'status': 0, 'context': new_datasets, 'message': f"Created {len(new_datasets)} new datasets"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for add dataset"},
                        status=HTTPStatus.NOT_IMPLEMENTED)


# @check_conditional_permissions(restricted=True)
# @check_resources_exist('json')
# def admin_create_group(request, vm_id):
#     """ This is the form endpoint to grant a user permissions on a vm"""
#     context = {"status": 0, "message": ""}
#     if request.method == "POST":
#         form = AdminCreateGroupForm(request.POST)
#         if form.is_valid():
#             vm_id = form.cleaned_data["vm_id"]
#         else:
#             context["create_vm_form_error"] = "Form Invalid (check formatting)"
#             return JsonResponse(context)
#
#     vm = model.get_vm(vm_id)
#     context = auth.create_group(vm)
#
#     return JsonResponse(context)


@check_conditional_permissions(restricted=True)
@check_resources_exist('json')
def admin_create_group(request, vm_id):
    """ this is a rest endpoint to grant a user permissions on a vm"""
    vm = model.get_vm(vm_id)
    message = auth.create_group(vm)
    return JsonResponse({'status': 0, 'message': message})
