from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
import logging

from .grpc_client import GrpcClient
from .tira_model import FileDatabase
from .authentication import Authentication
from .checks import Check
from .forms import *
from django.core.exceptions import PermissionDenied
from pathlib import Path
from google.protobuf.json_format import MessageToDict
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
import uuid
from http import HTTPStatus

from .grpc_client import GrpcClient

model = FileDatabase()
include_navigation = True if settings.DEPLOYMENT == "legacy" else False
auth = Authentication(authentication_source=settings.DEPLOYMENT,
                      users_file=settings.LEGACY_USER_FILE)
check = Check(model, auth)

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


# ---------------------------------------------------------------------
#   Review actions
# ---------------------------------------------------------------------


def publish(request, vm_id, dataset_id, run_id, value):
    check.has_access(request, ["tira", "admin"])
    value = (True if value == 'true' else False)
    if request.method == 'GET':
        status = model.update_review(dataset_id, vm_id, run_id, published=value)
        if status:
            context = {"status": "success", "published": value}
        else:
            context = {"status": "fail", "published": (not value)}

        return JsonResponse(context)


def blind(request, vm_id, dataset_id, run_id, value):
    check.has_access(request, ["tira", "admin"])
    value = (False if value == 'false' else True)

    if request.method == 'GET':
        status = model.update_review(dataset_id, vm_id, run_id, blinded=value)
        if status:
            context = {"status": "success", "blinded": value}
        else:
            context = {"status": "fail", "blinded": (not value)}
        return JsonResponse(context)


# ---------------------------------------------------------------------
#   Admin actions
# ---------------------------------------------------------------------


def admin_reload_data(request):
    check.has_access(request, ["tira", "admin"])

    if request.method == 'GET':
        # post_id = request.GET['post_id']
        model.build_model()
        return HttpResponse("Success!")


def admin_create_vm(request):
    """ Hook for create_vm posts. Responds with json objects indicating the state of the create process. """
    check.has_access(request, ["tira", "admin"])

    context = {
        "complete": [],
        'failed': []
    }

    def parse_create_string(create_string: str):
        for line in create_string.split("\n"):
            line = line.split(",")
            yield line[0], line[1], line[2]

    if request.method == "POST":
        form = CreateVmForm(request.POST)
        if form.is_valid():
            try:
                bulk_create = list(parse_create_string(form.cleaned_data["bulk_create"]))
            except IndexError:
                context["create_vm_form_error"] = "Error Parsing input. Are all lines complete?"
                return JsonResponse(context)

            # TODO dummy code talk to Nikolay!
            # TODO check semantics downstream (vm exists, host/ova does not exist)
            # for create_command in parse_create_string(form.cleaned_data["bulk_create"]):
            #     if create_vm(*create_command):
            #         model.add_ongoing_execution(*create_command)
            return bulk_vm_create(request, bulk_create)
            # context['bulkCommandId'] = bulk_id
        else:
            context["create_vm_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


def admin_get_command_queue():
    return get_bulk_command_status()


def admin_archive_vm():
    return None


def admin_modify_vm():
    return None


def admin_create_task(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """
    check.has_access(request, ["tira", "admin"])

    context = {}

    if request.method == "POST":
        form = CreateTaskForm(request.POST)
        if form.is_valid():
            # sanity checks
            if not check.vm_exists(form.cleaned_data["master_vm_id"]):
                context["status"] = "fail"
                context[
                    "create_task_form_error"] = f"Master VM with ID {form.cleaned_data['master_vm_id']} does not exist"
                return JsonResponse(context)

            if not check.organizer_exists(form.cleaned_data["organizer"]):
                context["status"] = "fail"
                context["create_task_form_error"] = f"Organizer with ID {form.cleaned_data['organizer']} does not exist"
                return JsonResponse(context)

            if check.task_exists(form.cleaned_data["task_id"]):
                context["status"] = "fail"
                context["create_task_form_error"] = f"Task with ID {form.cleaned_data['task_id']} already exist"
                return JsonResponse(context)

            if model.create_task(form.cleaned_data["task_id"], form.cleaned_data["task_name"],
                                 form.cleaned_data["task_description"], form.cleaned_data["master_vm_id"],
                                 form.cleaned_data["organizer"], form.cleaned_data["website"]):
                context["status"] = "success"
                context["created"] = {
                    "task_id": form.cleaned_data["task_id"], "task_name": form.cleaned_data["task_name"],
                    "task_description": form.cleaned_data["task_description"],
                    "master_vm_id": form.cleaned_data["master_vm_id"],
                    "organizer": form.cleaned_data["organizer"], "website": form.cleaned_data["website"]}
            else:
                context["status"] = "fail"
                context["create_task_form_error"] = f"Could not create {form.cleaned_data['task_id']}. Contact Admin."
                return JsonResponse(context)
        else:
            context["status"] = "fail"
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


def admin_add_dataset(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """
    check.has_access(request, ["tira", "admin"])

    context = {}

    if request.method == "POST":
        form = AddDatasetForm(request.POST)
        if form.is_valid():
            # TODO should be calculated from dataset_name
            dataset_id_prefix = form.cleaned_data["dataset_id_prefix"]
            dataset_name = form.cleaned_data["dataset_name"]
            master_vm_id = form.cleaned_data["master_vm_id"]
            task_id = form.cleaned_data["task_id"]
            command = form.cleaned_data["command"]
            working_directory = form.cleaned_data["working_directory"]
            measures = [line.split(',') for line in form.cleaned_data["measures"].split('\n')]

            # sanity checks
            if not check.vm_exists(master_vm_id):
                context["status"] = "fail"
                context["add_dataset_form_error"] = f"Master VM with ID {master_vm_id} does not exist"
                return JsonResponse(context)

            if not check.task_exists(task_id):
                context["status"] = "fail"
                context["add_dataset_form_error"] = f"Task with ID {task_id} does not exist"
                return JsonResponse(context)

            if check.dataset_exists(dataset_id_prefix):
                context["status"] = "fail"
                context["add_dataset_form_error"] = f"Task with ID {dataset_id_prefix} already exist"
                return JsonResponse(context)

            try:
                new_paths = []
                if form.cleaned_data["create_training"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "training", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "training", command,
                                        working_directory, measures)

                if form.cleaned_data["create_test"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "test", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "test", command, working_directory,
                                        measures)

                if form.cleaned_data["create_dev"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "dev", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "dev", command, working_directory,
                                        measures)

                context["status"] = "success"
                context["created"] = {"dataset_id": dataset_id_prefix, "new_paths": new_paths}

            except KeyError as e:
                logger.error(e)
                context["status"] = "fail"
                context["create_task_form_error"] = f"Could not create {dataset_id_prefix}: {e}"
                return JsonResponse(context)
        else:
            context["status"] = "fail"
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


# ---------------------------------------------------------------------
#   VM actions
# ---------------------------------------------------------------------


def vm_create(request, hostname, user_id, ova_file, bulk_id=None):
    grpc_client = GrpcClient(hostname)
    response = grpc_client.vm_create(ova_file, user_id, bulk_id)
    return JsonResponse({'status': 'Accepted', 'message': response}, status=HTTPStatus.ACCEPTED)


def vm_start(request, user_id, vm_id):
    vm = model.get_vm_by_id(user_id)
    grpc_client = GrpcClient(vm.host)
    response = grpc_client.vm_start(vm.vmName)
    return JsonResponse({'status': 'Accepted', 'message': response}, status=HTTPStatus.ACCEPTED)


def vm_stop(request, user_id, vm_id):
    vm = model.get_vm_by_id(user_id)
    grpc_client = GrpcClient(vm.host)
    response = grpc_client.vm_stop(vm.vmName)
    return JsonResponse({'status': 'Accepted', 'message': response}, status=HTTPStatus.ACCEPTED)


def run_execute(request, user_id, vm_id):
    vm = model.get_vm_by_id(user_id)
    grpc_client = GrpcClient(vm.host)
    response = grpc_client.run_execute(submission_file="",
                                       input_dataset_name="",
                                       input_run_path="",
                                       output_dir_name="",
                                       sandboxed="",
                                       optional_parameters="")
    return JsonResponse({'status': 'Accepted', 'message': response}, status=HTTPStatus.ACCEPTED)


def run_eval(request, user_id, vm_id):
    vm = model.get_vm_by_id(user_id)
    grpc_client = GrpcClient(vm.host)
    response = grpc_client.run_execute(submission_file="",
                                       input_dataset_name="",
                                       input_run_path="",
                                       output_dir_name="",
                                       sandboxed="",
                                       optional_parameters="")
    return JsonResponse({'status': 'Accepted', 'message': response}, status=HTTPStatus.ACCEPTED)


# ---------------------------------------------------------------------
#   Management actions
# ---------------------------------------------------------------------


def command_status(request, command_id):
    command = model.get_command(command_id)
    if not command:
        return JsonResponse({"status": 'NOT_FOUND'}, status=HTTPStatus.NOT_FOUND)

    return JsonResponse({"status": 'OK', 'message': {'command': MessageToDict(command)}}, status=HTTPStatus.OK)


def bulk_vm_create(request, vm_list):
    bulk_id = uuid.uuid4().hex
    for host, vm_id, ova_id in vm_list:
        vm_create(request, host, vm_id, ova_id, bulk_id=bulk_id)

    return JsonResponse({'status': 'Accepted', 'message': {'bulkCommandId': bulk_id}}, status=HTTPStatus.ACCEPTED)
    # return bulk_id


def get_bulk_command_status(request, bulk_id):
    commands = model.get_commands_bulk(bulk_id)
    return JsonResponse({'status': 'OK', 'message': {'commands': commands}}, status=HTTPStatus.OK)