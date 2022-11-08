import logging

from tira.authentication import auth
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.forms import *
from django.http import HttpResponse, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from http import HTTPStatus
import json
from datetime import datetime as dt

import tira.tira_model as model
import tira.git_runner as git_runner

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
        featured = data["featured"]
        master_vm_id = data["master_vm_id"]
        require_registration = data['require_registration']
        require_groups = data['require_groups']
        restrict_groups = data['restrict_groups']

        if not model.organizer_exists(organizer):
            return JsonResponse({'status': 1, 'message': f"Organizer with ID {organizer} does not exist"})
        if model.task_exists(task_id):
            return JsonResponse({'status': 1, 'message': f"Task with ID {task_id} already exist"})
        if not model.vm_exists(master_vm_id):
            return JsonResponse({'status': 1, 'message': f"VM with ID {master_vm_id} does not exist"})

        new_task = model.create_task(task_id, data["name"], data["description"], featured, master_vm_id,
                                     organizer, data["website"],
                                     require_registration, require_groups, restrict_groups,
                                     help_command=data["help_command"], help_text=data["help_text"])

        new_task = json.dumps(new_task, cls=DjangoJSONEncoder)
        return JsonResponse({'status': 0, 'context': new_task,
                             'message': f"Created Task with Id: {data['task_id']}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for vm create"},
                        status=HTTPStatus.NOT_IMPLEMENTED)


@check_permissions
@check_resources_exist('json')
def admin_edit_task(request, task_id):
    """ Edit a task. Expects a POST message with all task data. """
    if request.method == "POST":
        data = json.loads(request.body)
        organizer = data["organizer"]
        featured = data["featured"]
        master_vm_id = data["master_vm_id"]
        require_registration = data['require_registration']
        require_groups = data['require_groups']
        restrict_groups = data['restrict_groups']

        if not model.organizer_exists(organizer):
            return JsonResponse({'status': 1, 'message': f"Organizer with ID {organizer} does not exist"})
        if not model.vm_exists(master_vm_id):
            return JsonResponse({'status': 1, 'message': f"VM with ID {master_vm_id} does not exist"})

        task = model.edit_task(task_id, data["name"], data["description"], featured, master_vm_id,
                               organizer, data["website"], require_registration, require_groups, restrict_groups,
                               help_command=data["help_command"], help_text=data["help_text"])

        return JsonResponse({'status': 0, 'context': json.dumps(task, cls=DjangoJSONEncoder),
                             'message': f"Edited Task with Id: {task_id}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit task"})


@check_permissions
@check_resources_exist('json')
def admin_delete_task(request, task_id):
    model.delete_task(task_id)
    return JsonResponse({'status': 0, 'message': f"Deleted task {task_id}"})


@check_permissions
def admin_add_dataset(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """
    if request.method == "POST":
        data = json.loads(request.body)

        if not all(k in data.keys() for k in ['dataset_id', 'name', 'task']):
            return JsonResponse({'status': 1, 'message': f"Error: Task, dataset name, and dataset ID must be set."})

        dataset_id_prefix = data["dataset_id"]
        dataset_name = data["name"]
        task_id = data["task"]

        upload_name = data.get("upload_name", "predictions.jsonl")
        command = data.get("evaluator_command", "")
        working_directory = data.get("evaluator_working_directory", "")
        measures = data.get("evaluation_measures", "")

        is_git_runner = data.get("is_git_runner", False)
        git_runner_image = data.get("git_runner_image", "")
        git_runner_command = data.get("git_runner_command", "")
        git_repository_id = data.get("git_repository_id", "")

        if not data.get("use_existing_repository", True):
            git_repository_id = git_runner.create_task_repository(task_id)

        master_vm_id = model.get_task(task_id)["master_vm_id"]

        if not model.task_exists(task_id):
            return JsonResponse({'status': 1, "message": f"Task with ID {task_id} does not exist"})
        if data['type'] not in {'test', 'training'}:
            return JsonResponse({'status': 1, "message": f"Dataset type must be 'test' or 'training'"})

        try:
            if data['type'] == 'training':
                ds, paths = model.add_dataset(task_id, dataset_id_prefix, "training", dataset_name, upload_name)
            elif data['type'] == 'test':
                ds, paths = model.add_dataset(task_id, dataset_id_prefix, "test", dataset_name, upload_name)

            model.add_evaluator(master_vm_id, task_id, ds['dataset_id'], command, working_directory, not measures,
                                is_git_runner, git_runner_image, git_runner_command, git_repository_id)
            path_string = '\n '.join(paths)
            return JsonResponse(
                {'status': 0, 'context': ds, 'message': f"Created new dataset with id {ds['dataset_id']}. "
                                                        f"Store your datasets in the following Paths:\n"
                                                        f"{path_string}"})
        except FileExistsError as e:
            logger.exception(e)
            return JsonResponse({'status': 1, 'message': f"A Dataset with this id already exists."})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for add dataset"})


@check_permissions
@check_resources_exist('json')
def admin_edit_dataset(request, dataset_id):
    """ Edit a dataset with the given dataset_id
    Send the new data of the dataset via POST. All these keys must be given and will be set:

    - name: New display name of the dataset
    - task: The associated task
    - master_id: ID of the vm that runs the evaluator for this dataset
    - type: 'training' or 'test'
    - evaluator_working_directory: working directory of the evaluator on the master vm
    - evaluator_command: command to be run on the master vm to evaluate the output of runs on the dataset
    - evaluation_measures: (str) the measures output by the evaluator. Sent as a string with:
        `
        Display Name of Measure1,key_of_measure_1\n
        Display Name of Measure2,key_of_measure_2\n
        ...
        `
    - is_git_runner
    - git_runner_image
    - git_runner_command
    - git_repository_id
    """
    if request.method == "POST":
        data = json.loads(request.body)

        dataset_name = data["name"]
        task_id = data["task"]
        is_confidential = not data['publish']

        command = data["evaluator_command"]
        working_directory = data["evaluator_working_directory"]
        measures = "" # here for legacy reasons. TIRA uses the measures provided by the evaluator

        is_git_runner = data["is_git_runner"]
        git_runner_image = data["git_runner_image"]
        git_runner_command = data["git_runner_command"]
        git_repository_id = data["git_repository_id"]

        print(data["use_existing_repository"])
        print(data["git_repository_id"])
        if not data["use_existing_repository"]:
            git_repository_id = git_runner.create_task_repository(task_id)

        upload_name = data["upload_name"]

        if not model.task_exists(task_id):
            return JsonResponse({'status': 1, "message": f"Task with ID {task_id} does not exist"})

        ds = model.edit_dataset(task_id, dataset_id, dataset_name, command, working_directory,
                                measures, upload_name, is_confidential, is_git_runner, git_runner_image,
                                git_runner_command, git_repository_id)

        return JsonResponse(
            {'status': 0, 'context': ds, 'message': f"Updated Dataset {ds['dataset_id']}."})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for add dataset"})


@check_permissions
@check_resources_exist('json')
def admin_delete_dataset(request, dataset_id):
    model.delete_dataset(dataset_id)
    return JsonResponse({'status': 0, 'message': f"Deleted dataset {dataset_id}"})


@check_permissions
def admin_add_organizer(request, organizer_id):
    if request.method == "POST":
        data = json.loads(request.body)

        name = data["name"]
        years = data["years"]
        web = data["web"]

        model.edit_organizer(organizer_id, name, years, web)
        return JsonResponse({'status': 0, 'message': f"Added Organizer {organizer_id}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for add organizer"})


@check_permissions
@check_resources_exist('json')
def admin_edit_organizer(request, organizer_id):
    if request.method == "POST":
        data = json.loads(request.body)

        name = data["name"]
        years = data["years"]
        web = data["web"]

        model.edit_organizer(organizer_id, name, years, web)
        return JsonResponse({'status': 0, 'message': f"Updated Organizer {organizer_id}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit organizer"})


@check_conditional_permissions(restricted=True)
@check_resources_exist('json')
def admin_create_group(request, vm_id):
    """ this is a rest endpoint to grant a user permissions on a vm"""
    vm = model.get_vm(vm_id)
    message = auth.create_group(vm)
    return JsonResponse({'status': 0, 'message': message})


@check_conditional_permissions(restricted=True)
@check_resources_exist('json')
def admin_edit_review(request, dataset_id, vm_id, run_id):
    if request.method == "POST":
        data = json.loads(request.body)
        no_errors = data["no_errors"]
        output_error = data["output_error"]
        software_error = data["software_error"]
        comment = data["comment"]

        # sanity checks
        if no_errors and (output_error or software_error):
            JsonResponse({'status': 1, 'message': f"Error type is not clearly selected."})

        username = auth.get_user_id(request)
        has_errors = output_error or software_error
        has_no_errors = (not has_errors)

        s = model.update_review(dataset_id, vm_id, run_id, username, str(dt.utcnow()),
                                has_errors, has_no_errors, no_errors=no_errors,
                                invalid_output=output_error,
                                has_error_output=output_error, other_errors=software_error, comment=comment
                                )
        return JsonResponse({'status': 0, 'message': f"Updated review for run {run_id}"})

    return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit organizer"})
