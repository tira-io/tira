from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.template.loader import render_to_string
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
from .transitions import TransitionLog, EvaluationLog

from .grpc_client import GrpcClient

from .views import model
from .util import get_tira_id

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

def vm_state(request, vm_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    state = TransitionLog.objects.get(vm_id=vm_id)
    print(state.vm_id, state.vm_state)
    return JsonResponse({'state': state.vm_state}, status=HTTPStatus.ACCEPTED)


def vm_running_evaluations(request, vm_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    results = EvaluationLog.objects.get(vm_id=vm_id)
    return True if results else False


def vm_create(request, hostname, vm_id, ova_file, bulk_id=None):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    grpc_client = GrpcClient('localhost') if settings.GRPC_HOST == 'local' else GrpcClient(hostname)
    response = grpc_client.vm_create(ova_file, vm_id, bulk_id)
    return JsonResponse({'status': response.status, 'message': response.transactionId}, status=HTTPStatus.ACCEPTED)


def vm_start(request, vm_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    vm = model.get_vm(vm_id)
    grpc_client = GrpcClient('localhost') if settings.GRPC_HOST == 'local' else GrpcClient(vm.host)
    response = grpc_client.vm_start(
        vm_id)  # NOTE vm_id is different from vm.vmName (latter one includes the 01-tira-ubuntu-...
    # when status = 0, the host accepts the transaction. We shift our state to 3 - "powering on"
    if response.status == 0:
        t = TransitionLog(vm_id=vm_id, vm_state=3)
        t.save()
        return JsonResponse({'status': response.status, 'message': response.transactionId}, status=HTTPStatus.ACCEPTED)
    return JsonResponse({'status': response.status, 'message': f"{response.transactionId} was rejected by the host"},
                        status=HTTPStatus.INTERNAL_SERVER_ERROR)


def vm_shutdown(request, vm_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    vm = model.get_vm(vm_id)
    grpc_client = GrpcClient('localhost') if settings.GRPC_HOST == 'local' else GrpcClient(vm.host)
    response = grpc_client.vm_shutdown(vm_id)
    return JsonResponse({'status': response.status, 'message': response.transactionId}, status=HTTPStatus.ACCEPTED)


def vm_stop(request, vm_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    vm = model.get_vm(vm_id)
    grpc_client = GrpcClient('localhost') if settings.GRPC_HOST == 'local' else GrpcClient(vm.host)
    response = grpc_client.vm_stop(vm.vmName)
    return JsonResponse({'status': response.status, 'message': response.transactionId}, status=HTTPStatus.ACCEPTED)


def vm_info(request, vm_id):
    try:
        check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    except Exception as e:
        logger.exception(f"unauthorized request to /grpc/{vm_id}/vm-info", e)
        return JsonResponse({'status': 'Rejected', 'message': 'Not Authorized'}, status=HTTPStatus.UNAUTHORIZED)

    logger.info(f"get info for {vm_id}")
    vm = model.get_vm(vm_id)
    host = 'localhost' if settings.GRPC_HOST == 'local' else vm.host
    try:
        grpc_client = GrpcClient(host)
        response_vm_info = grpc_client.vm_info(vm_id)
        del grpc_client
    except Exception as e:
        logger.exception(f"/grpc/{vm_id}/vm-info to {host} failed with {e}")
        return JsonResponse({'status': 'Rejected', 'message': "Server Error"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    t = TransitionLog(vm_id=vm_id, vm_state=response_vm_info.state)
    t.save()

    return JsonResponse({'status': 'Accepted', 'message': {
        "guestOs": response_vm_info.guestOs,
        "memorySize": response_vm_info.memorySize,
        "numberOfCpus": response_vm_info.numberOfCpus,
        "sshPort": response_vm_info.sshPort,
        "rdpPort": response_vm_info.rdpPort,
        "host": response_vm_info.host,
        "sshPortStatus": response_vm_info.sshPortStatus,
        "rdpPortStatus": response_vm_info.rdpPortStatus,
        "state": response_vm_info.state,
    }
                         }, status=HTTPStatus.ACCEPTED)


# ---------------------------------------------------------------------
#   Software actions
# ---------------------------------------------------------------------
def software_add(request, task_id, vm_id):
    check.has_access(request, ["tira", "admin", "participant", "user"], on_vm_id=vm_id)

    # 0. Early return a dummy page, if the user has no vm assigned on this task
    # TODO: If the user has no VM, give him a request form
    if auth.get_role(request, user_id=auth.get_user_id(request), vm_id=vm_id) == auth.ROLE_USER or \
            vm_id == "no-vm-assigned":
        context = {
            "include_navigation": include_navigation,
            "task": model.get_task(task_id),
            "vm_id": "no-vm-assigned",
            "role": auth.get_role(request)
        }

    software = model.add_software(task_id, vm_id)
    if not software:
        return JsonResponse({'status': 'Failed'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    context = {
        "user_id": auth.get_user_id(request),
        "include_navigation": include_navigation,
        "task": task_id,
        "vm_id": vm_id,
        "datasets": model.get_datasets_by_task(task_id),
        "software": {
            "id": software.id,
            "command": software.command,
            "working_dir": software.workingDirectory,
            "dataset": software.dataset,
            "creation_date": software.creationDate,
            "last_edit": software.lastEditDate
        }
    }
    html = render_to_string('tira/software_form.html', context=context, request=request)
    return JsonResponse({'html': html, 'software_id': context["software"]['id']}, status=HTTPStatus.ACCEPTED)


def software_save(request, task_id, vm_id, software_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)

    software = model.update_software(task_id, vm_id, software_id,
                                     request.POST.get("command"),
                                     request.POST.get("working_dir"),
                                     request.POST.get("input_dataset"),
                                     request.POST.get("input_run"))

    if software:
        return JsonResponse({'status': 'Accepted', 'last_edit': software.lastEditDate}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse({'status': 'Failed'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def software_delete(request, task_id, vm_id, software_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)

    delete_ok = model.delete_software(task_id, vm_id, software_id)

    if delete_ok:
        return JsonResponse({'status': 'Accepted'}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse({'status': 'Failed', 'message': 'Software not found. Cannot delete.'},
                            status=HTTPStatus.INTERNAL_SERVER_ERROR)


def run_execute(request, task_id, vm_id, software_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)

    vm = model.get_vm(vm_id)
    software = model.get_software(task_id, vm_id, software_id=software_id)
    # TODO get input_run data. This is not supported right now, I suggest solving this via website (better selector)

    host = 'localhost' if settings.GRPC_HOST == 'local' else vm.host
    try:
        grpc_client = GrpcClient(host)
        response = grpc_client.run_execute(vm_id=vm_id,
                                           dataset_id=software["dataset"],
                                           run_id=get_tira_id(),
                                           working_dir=software["working_directory"],
                                           command=software["command"],
                                           input_run_vm_id="",
                                           input_run_dataset_id="",
                                           input_run_run_id=software["run"],
                                           optional_parameters="")
        del grpc_client
    except Exception as e:
        logger.exception(f"/grpc/{vm_id}/run_abort to {host} failed with {e}")
        return JsonResponse({'status': 'Rejected', 'message': "Server Error"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return JsonResponse({'status': 'Accepted', 'message': response}, status=HTTPStatus.ACCEPTED)


def run_eval(request, vm_id, dataset_id, run_id):
    """ Get the evaluator for dataset_id from the model.
     Then, send a GRPC-call to the host running the evaluator with the run data.
     Then, log vm_id and run_id to the evaluation log as ongoing.
    """
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)

    evaluator = model.get_evaluator(dataset_id)

    host = 'localhost' if settings.GRPC_HOST == 'local' else evaluator["host"]
    try:
        grpc_client = GrpcClient(host)
        response = grpc_client.run_eval(vm_id=evaluator["vm_id"],
                                        dataset_id=dataset_id,
                                        run_id=get_tira_id(),
                                        working_dir=evaluator["working_dir"],
                                        command=evaluator["command"],
                                        input_run_vm_id=vm_id,
                                        input_run_dataset_id=dataset_id,
                                        input_run_run_id=run_id,
                                        optional_parameters="")
        del grpc_client
    except Exception as e:
        logger.exception(f"/grpc/{vm_id}/run_eval/{dataset_id}/{run_id} to {host} failed with {e}")
        return JsonResponse({'status': 'Rejected', 'message': "Server Error"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    if response.status == 0:
        t = EvaluationLog(vm_id=vm_id, run_id=run_id)
        t.save()
        return JsonResponse({'status': response.status, 'message': response.transactionId}, status=HTTPStatus.ACCEPTED)

    return JsonResponse({'status': 'Accepted', 'message': response}, status=HTTPStatus.ACCEPTED)


def run_delete(request, dataset_id, vm_id, run_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    # TODO just delete it with model.delete_run()
    # TODO should also call a grpc:run_delete to delete host-side data
    model.update_run(dataset_id, vm_id, run_id, deleted=True)
    return JsonResponse({'status': 'Accepted'}, status=HTTPStatus.ACCEPTED)


def run_abort(request, vm_id):
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    vm = model.get_vm(vm_id)

    host = 'localhost' if settings.GRPC_HOST == 'local' else vm.host
    try:
        grpc_client = GrpcClient(host)
        response = grpc_client.run_abort(vm_id)
        del grpc_client
    except Exception as e:
        logger.exception(f"/grpc/{vm_id}/run_abort to {host} failed with {e}")
        return JsonResponse({'status': 'Rejected', 'message': "Server Error"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

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
    check.has_access(request, ["tira", "admin"])

    bulk_id = uuid.uuid4().hex
    for host, vm_id, ova_id in vm_list:
        vm_create(request, host, vm_id, ova_id, bulk_id=bulk_id)

    return JsonResponse({'status': 'Accepted', 'message': {'bulkCommandId': bulk_id}}, status=HTTPStatus.ACCEPTED)
    # return bulk_id


def get_bulk_command_status(request, bulk_id):
    commands = model.get_commands_bulk(bulk_id)
    return JsonResponse({'status': 'OK', 'message': {'commands': commands}}, status=HTTPStatus.OK)
