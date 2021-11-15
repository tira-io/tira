from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.template.loader import render_to_string
from django.db.utils import IntegrityError
import logging

from .grpc_client import GrpcClient
from grpc import RpcError, StatusCode
from .tira_model import FileDatabase
from .authentication import auth
from .checks import actions_check_permissions, check_resources_exist
from .forms import *
from django.core.exceptions import PermissionDenied
from pathlib import Path
from google.protobuf.json_format import MessageToDict
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
import uuid
from http import HTTPStatus

from .transitions import TransitionLog, EvaluationLog, TransactionLog
from .grpc_client import GrpcClient
from .grpc_server import TiraApplicationService
from .tira_model import model
from .util import get_tira_id, reroute_host
from functools import wraps

include_navigation = True if settings.DEPLOYMENT == "legacy" else False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


def host_call(func):
    @wraps(func)
    def func_wrapper(request, *args, **kwargs):
        try:
            response = func(request, *args, **kwargs)
        except RpcError as e:
            ex_message = "FAILED"
            try:
                logger.exception(f"{request.get_full_path()}: connection failed with {e}")
                if e.code() == StatusCode.UNAVAILABLE:  # .code() is implemented by the _channel._InteractiveRpcError
                    logger.exception(f"Connection Unavailable: {e.debug_error_string()}")
                    ex_message = "UNAVAILABLE"  # This happens if the GRPC Server is not running
                if e.code() == StatusCode.INVALID_ARGUMENT:
                    logger.exception(f"Invalid Argument: {e.debug_error_string()}")
                    ex_message = "The VM was not found on this host."  #
            except Exception as e2:  # There is a RpcError but not an Interactive one. This should not happen
                logger.exception(f"{request.get_full_path()}: Unexpected Execption occured: {e2}")
            return JsonResponse({'status': "1", 'message': ex_message}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception(f"{request.get_full_path()}: Server Error: {e}")
            return JsonResponse({'status': "1", 'message': "SERVER_ERROR"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if response.status == 0:
            return JsonResponse({'status': response.status, 'message': response.transactionId},
                                status=HTTPStatus.ACCEPTED)
        return JsonResponse(
            {'status': response.status, 'message': f"{response.transactionId} was rejected by the host"},
            status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return func_wrapper

# ---------------------------------------------------------------------
#   Review actions
# ---------------------------------------------------------------------


@actions_check_permissions({"tira", "admin"})
@check_resources_exist('json')
def publish(request, vm_id, dataset_id, run_id, value):
    value = (True if value == 'true' else False)
    if request.method == 'GET':
        status = model.update_review(dataset_id, vm_id, run_id, published=value)
        if status:
            context = {"status": "0", "published": value,  "message": f"Published is now: {value}"}
        else:
            context = {"status": "1", "published": (not value),  "message": f"Published is now: {value}"}

        return JsonResponse(context)


@actions_check_permissions({"tira", "admin"})
@check_resources_exist('json')
def blind(request, vm_id, dataset_id, run_id, value):
    value = (False if value == 'false' else True)

    if request.method == 'GET':
        status = model.update_review(dataset_id, vm_id, run_id, blinded=value)
        if status:
            context = {"status": "0", "blinded": value,  "message": f"Blinded is now: {value}"}
        else:
            context = {"status": "1", "blinded": (not value),  "message": f"Blinded is now: {value}"}
        return JsonResponse(context)


# ---------------------------------------------------------------------
#   Admin actions
# ---------------------------------------------------------------------


@actions_check_permissions({"tira", "admin"})
def admin_reload_data(request):
    if request.method == 'GET':
        # post_id = request.GET['post_id']
        try:
            model.build_model()
            if auth.get_auth_source() == 'legacy':
                auth.load_legacy_users()
            return JsonResponse({'status': 0, 'message': "Success"}, status=HTTPStatus.OK)
        except Exception as e:
            logger.exception(f"/admin/reload_data failed with {e}", e)
            return JsonResponse({'status': 1, 'message': f"Failed with {e}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return JsonResponse({'status': 1, 'message': f"{request.method} is not allowed."}, status=HTTPStatus.FORBIDDEN)


@actions_check_permissions({"tira", "admin"})
def admin_create_vm(request):  # TODO implement
    """ Hook for create_vm posts. Responds with json objects indicating the state of the create process. """

    context = {
        "complete": [],
        'failed': []
    }
    return JsonResponse(context)

    # def parse_create_string(create_string: str):
    #     for line in create_string.split("\n"):
    #         line = line.split(",")
    #         yield line[0], line[1], line[2]
    #
    # if request.method == "POST":
    #     form = CreateVmForm(request.POST)
    #     if form.is_valid():
    #         try:
    #             bulk_create = list(parse_create_string(form.cleaned_data["bulk_create"]))
    #         except IndexError:
    #             context["create_vm_form_error"] = "Error Parsing input. Are all lines complete?"
    #             return JsonResponse(context)
    #
    #         # TODO dummy code talk to Nikolay!
    #         # TODO check semantics downstream (vm exists, host/ova does not exist)
    #         # for create_command in parse_create_string(form.cleaned_data["bulk_create"]):
    #         #     if create_vm(*create_command):
    #         #         model.add_ongoing_execution(*create_command)
    #         return bulk_vm_create(request, bulk_create)
    #     else:
    #         context["create_vm_form_error"] = "Form Invalid (check formatting)"
    #         return JsonResponse(context)
    # else:
    #     HttpResponse("Permission Denied")
    #
    # return JsonResponse(context)


@actions_check_permissions({"tira", "admin"})
def admin_archive_vm():
    return JsonResponse({'status': 1, 'message': f"Not implemented"}, status=HTTPStatus.NOT_IMPLEMENTED)


@actions_check_permissions({"tira", "admin"})
def admin_modify_vm():
    return JsonResponse({'status': 1, 'message': f"Not implemented"}, status=HTTPStatus.NOT_IMPLEMENTED)


@actions_check_permissions({"tira", "admin"})
def admin_create_task(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """

    context = {}

    if request.method == "POST":
        form = CreateTaskForm(request.POST)
        if form.is_valid():
            # sanity checks
            context["status"] = "fail"
            master_vm_id = form.cleaned_data["master_vm_id"]
            task_id = form.cleaned_data["task_id"]
            organizer = form.cleaned_data["organizer"]

            try:
                model.get_vm(master_vm_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Master VM with ID {master_vm_id} does not exist"
                return JsonResponse(context)

            try:
                model.get_task(task_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Task with ID {task_id} does not exist"
                return JsonResponse(context)

            try:
                model.get_organizer(organizer)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Task with ID {organizer} does not exist"
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
                context["create_task_form_error"] = f"Could not create {form.cleaned_data['task_id']}. Contact Admin."
                return JsonResponse(context)
        else:
            context["status"] = "fail"
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


@actions_check_permissions({"tira", "admin"})
def admin_add_dataset(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """

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
            context["status"] = "fail"
            try:
                model.get_vm(master_vm_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Master VM with ID {master_vm_id} does not exist"
                return JsonResponse(context)

            try:
                model.get_task(task_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Task with ID {task_id} does not exist"
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
                context["create_task_form_error"] = f"Could not create {dataset_id_prefix}: {e}"
                return JsonResponse(context)
        else:
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


# ---------------------------------------------------------------------
#   VM actions
# ---------------------------------------------------------------------

@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
def vm_state(request, vm_id):
    try:
        state = TransitionLog.objects.get_or_create(vm_id=vm_id, defaults={'vm_state': 0})[0].vm_state
    except IntegrityError as e:
        logger.warning(f"failed to read state for vm {vm_id} with {e}")
        state = 0
    return JsonResponse({'state': state}, status=HTTPStatus.ACCEPTED)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
def vm_running_evaluations(request, vm_id):
    results = EvaluationLog.objects.filter(vm_id=vm_id)
    return JsonResponse({'running_evaluations': True if results else False}, status=HTTPStatus.ACCEPTED)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
@host_call
def vm_create(request, hostname, vm_id, ova_file):
    uid = auth.get_user_id(request)
    host = reroute_host(hostname)
    return GrpcClient(host).vm_create(vm_id, ova_file, uid, host)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
@host_call
def vm_start(request, vm_id):
    vm = model.get_vm(vm_id)
    # NOTE vm_id is different from vm.vmName (latter one includes the 01-tira-ubuntu-...
    return GrpcClient(reroute_host(vm.host)).vm_start(vm_id)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
@host_call
def vm_shutdown(request, vm_id):
    vm = model.get_vm(vm_id)
    return GrpcClient(reroute_host(vm.host)).vm_shutdown(vm_id)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
@host_call
def vm_stop(request, vm_id):
    vm = model.get_vm(vm_id)
    return GrpcClient(reroute_host(vm.host)).vm_stop(vm_id)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
def vm_info(request, vm_id):
    # TODO when vm_id is no-vm-assigned

    vm = model.get_vm(vm_id)
    host = reroute_host(vm.host)
    try:
        grpc_client = GrpcClient(host)
        response_vm_info = grpc_client.vm_info(vm_id)
        # _ = TransitionLog.objects.update_or_create(vm_id=vm_id, defaults={'vm_state': response_vm_info.state})
        del grpc_client
    except RpcError as e:
        ex_message = "FAILED"
        try:
            if e.code() == StatusCode.UNAVAILABLE:  # .code() is implemented by the _channel._InteractiveRpcError
                ex_message = "UNAVAILABLE"  # This happens if the GRPC Server is not running
        except Exception as e2:  # There is a RpcError but not an Interactive one. This should not happen
            logger.exception(f"/grpc/{vm_id}/vm-info: Unexpected Execption occured: {e2}")

        logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed with {e}")
        return JsonResponse({'status': 'Rejected', 'message': ex_message}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed with {e}")
        return JsonResponse({'status': 'Rejected', 'message': "SERVER_ERROR"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

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
    }}, status=HTTPStatus.ACCEPTED)


# ---------------------------------------------------------------------
#   Software actions
# ---------------------------------------------------------------------


@actions_check_permissions({"tira", "admin", "participant", "user"})
@check_resources_exist('json')
def software_add(request, task_id, vm_id):
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


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
def software_save(request, task_id, vm_id, software_id):
    software = model.update_software(task_id, vm_id, software_id,
                                     request.POST.get("command"),
                                     request.POST.get("working_dir"),
                                     request.POST.get("input_dataset"),
                                     request.POST.get("input_run"))

    if software:
        return JsonResponse({'status': 'Accepted', 'last_edit': software.lastEditDate}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse({'status': 'Failed'}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
def software_delete(request, task_id, vm_id, software_id):
    delete_ok = model.delete_software(task_id, vm_id, software_id)

    if delete_ok:
        return JsonResponse({'status': 'Accepted'}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse({'status': 'Failed', 'message': 'Software not found. Cannot delete.'},
                            status=HTTPStatus.INTERNAL_SERVER_ERROR)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
@host_call
def run_execute(request, task_id, vm_id, software_id):
    vm = model.get_vm(vm_id)
    software = model.get_software(task_id, vm_id, software_id=software_id)
    # TODO get input_run data. This is not supported right now, I suggest solving this via website (better selector)

    host = reroute_host(vm.host)
    future_run_id = get_tira_id()
    grpc_client = GrpcClient(host)
    response = grpc_client.run_execute(vm_id=vm_id,
                                       dataset_id=software["dataset"],
                                       run_id=future_run_id,
                                       input_run_vm_id="",
                                       input_run_dataset_id="",
                                       input_run_run_id=software["run"],
                                       task_id=task_id,
                                       software_id=software_id)
    del grpc_client
    return response


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
@host_call
def run_eval(request, vm_id, dataset_id, run_id):
    """ Get the evaluator for dataset_id from the model.
     Then, send a GRPC-call to the host running the evaluator with the run data.
     Then, log vm_id and run_id to the evaluation log as ongoing.
    """
    # check if evaluation already exists
    if EvaluationLog.objects.filter(vm_id=vm_id):
        return JsonResponse({'status': '1', 'message': "An evaluation is already in progress."},
                            status=HTTPStatus.PRECONDITION_FAILED)

    evaluator = model.get_evaluator(dataset_id)
    host = reroute_host(evaluator["host"])
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
    return response


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
def run_delete(request, dataset_id, vm_id, run_id):
    # TODO just delete it with model.delete_run()
    # TODO should also call a grpc:run_delete to delete host-side data
    model.update_run(dataset_id, vm_id, run_id, deleted=True)
    return JsonResponse({'status': 'Accepted'}, status=HTTPStatus.ACCEPTED)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('json')
@host_call
def run_abort(request, vm_id):
    """ """
    vm = model.get_vm(vm_id)
    host = reroute_host(vm.host)

    grpc_client = GrpcClient(host)
    response = grpc_client.run_abort(vm_id)
    del grpc_client
    return response
