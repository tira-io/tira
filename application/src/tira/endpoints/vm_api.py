from django.template.loader import render_to_string
from django.db.utils import IntegrityError
from django.core.cache import cache
import logging

from grpc import RpcError, StatusCode
from tira.authentication import auth
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.forms import *
from django.http import JsonResponse
from django.conf import settings
from http import HTTPStatus

from tira.model import TransitionLog, EvaluationLog, TransactionLog
from tira.grpc_client import GrpcClient
import tira.tira_model as model
from tira.util import get_tira_id, reroute_host
from tira.views import add_context
from functools import wraps
import json

include_navigation = True if settings.DEPLOYMENT == "legacy" else False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


def host_call(func):
    """ This is a decorator for methods that connect to a host. It handles all exceptions that can occur
     in the grpc communication. It also adds a reply consistent with the return status of the grpc call. """

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
                    ex_message = f"The requested host is unavailable. If you think this is a mistake, please contact " \
                                 "your task organizer."  # This happens if the GRPC Server is not running
                if e.code() == StatusCode.INVALID_ARGUMENT:
                    logger.exception(f"Invalid Argument: {e.debug_error_string()}")
                    ex_message = f"Response returned with an invalid argument: {e.debug_error_string()}"  #
            except Exception as e2:  # There is a RpcError but not an Interactive one. This should not happen
                logger.exception(f"{request.get_full_path()}: Unexpected Exception occurred: {e2}")
                ex_message = f"An unexpected exception occurred: {e2}"
            return JsonResponse({'status': "2", 'message': ex_message}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"{request.get_full_path()}: Server Error: {e}")
            return JsonResponse({'status': "1", 'message': f"An unexpected exception occurred: {e}"},
                                status=HTTPStatus.INTERNAL_SERVER_ERROR)

        if response.status == 0:
            return JsonResponse({'status': 0,
                                 'message': response.transactionId},
                                status=HTTPStatus.ACCEPTED)
        if response.status == 2:
            return JsonResponse({'status': 2,
                                 'message': f"Virtual machine not found on host: {response.message}"},
                                status=HTTPStatus.NOT_FOUND)
        if response.status == 3:
            return JsonResponse({'status': 1,
                                 'message': f"Virtual machine is in the wrong state for your request: {response.message}"},
                                status=HTTPStatus.BAD_REQUEST)
        if response.status == 4:
            return JsonResponse({'status': 1,
                                 'message': f"VM is archived: {response.message}"},
                                status=HTTPStatus.NOT_FOUND)
        if response.status == 5:
            return JsonResponse({'status': 2,
                                 'message': f"VM is not accessible: {response.message}"},
                                status=HTTPStatus.NOT_FOUND)
        if response.status == 6:
            return JsonResponse({'status': 1,
                                 'message': f"Requested input run was not found: {response.message}"},
                                status=HTTPStatus.NOT_FOUND)
        if response.status == 7:
            return JsonResponse({'status': 1,
                                 'message': f"Evaluation failed due to malformed run output: {response.message}"},
                                status=HTTPStatus.BAD_REQUEST)
        if response.status == 8:
            return JsonResponse({'status': 1,
                                 'message': f"Input malformed: {response.message}"},
                                status=HTTPStatus.BAD_REQUEST)
        if response.status == 9:
            return JsonResponse({'status': 2,
                                 'message': f"Host ist busy: {response.message}"},
                                status=HTTPStatus.SERVICE_UNAVAILABLE)

        return JsonResponse(
            {'status': 2,
             'message': f"{response.transactionId} was rejected by the host: {response.message}"},
            status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return func_wrapper


# ---------------------------------------------------------------------
#   VM actions
# ---------------------------------------------------------------------

@check_permissions
@check_resources_exist('json')
def vm_state(request, vm_id):
    try:
        state = TransitionLog.objects.get_or_create(vm_id=vm_id, defaults={'vm_state': 0})[0].vm_state
    except IntegrityError as e:
        logger.warning(f"failed to read state for vm {vm_id} with {e}")
        state = 0
    return JsonResponse({'status': 0, 'state': state})


@check_permissions
@check_resources_exist('json')
def vm_running_evaluations(request, vm_id):
    results = EvaluationLog.objects.filter(vm_id=vm_id)
    return JsonResponse({'status': 0, 'running_evaluations': True if results else False})


@check_permissions
@check_resources_exist('json')
def get_running_evaluations(request, vm_id):
    results = EvaluationLog.objects.filter(vm_id=vm_id)
    return JsonResponse({'status': 0, 'running_evaluations': [{"vm_id": r.vm_id, "run_id": r.run_id,
                                                  "running_on": r.running_on, "last_update": r.last_update}
                                                 for r in results]})


@check_conditional_permissions(restricted=True)
@host_call
def vm_create(request, hostname, vm_id, ova_file):
    uid = auth.get_user_id(request)
    host = reroute_host(hostname)
    return GrpcClient(host).vm_create(vm_id=vm_id, ova_file=ova_file, user_id=uid, hostname=host)


@check_permissions
@check_resources_exist('json')
@host_call
def vm_start(request, vm_id):
    vm = model.get_vm(vm_id)
    # NOTE vm_id is different from vm.vmName (latter one includes the 01-tira-ubuntu-...
    return GrpcClient(reroute_host(vm['host'])).vm_start(vm_id=vm_id)


@check_permissions
@check_resources_exist('json')
@host_call
def vm_shutdown(request, vm_id):
    vm = model.get_vm(vm_id)
    return GrpcClient(reroute_host(vm['host'])).vm_shutdown(vm_id=vm_id)


@check_permissions
@check_resources_exist('json')
@host_call
def vm_stop(request, vm_id):
    vm = model.get_vm(vm_id)
    return GrpcClient(reroute_host(vm['host'])).vm_stop(vm_id=vm_id)


@check_permissions
@check_resources_exist('json')
def vm_info(request, vm_id):
    vm = model.get_vm(vm_id)
    host = reroute_host(vm['host'])
    if not host:
        logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed, because host is empty")
        return JsonResponse({'status': 'Rejected', 'message': "SERVER_ERROR"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    try:
        grpc_client = GrpcClient(host)
        response_vm_info = grpc_client.vm_info(vm_id=vm_id)
        _ = TransitionLog.objects.update_or_create(vm_id=vm_id, defaults={'vm_state': response_vm_info.state})
        del grpc_client
    except RpcError as e:
        ex_message = "FAILED"
        try:
            if e.code() == StatusCode.UNAVAILABLE:  # .code() is implemented by the _channel._InteractiveRpcError
                logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed with {e}")
                ex_message = "Host Unavailable"  # This happens if the GRPC Server is not running
            if e.code() == StatusCode.INVALID_ARGUMENT:  # .code() is implemented by the _channel._InteractiveRpcError
                ex_message = "VM is archived"  # If there is no VM with the requested name on the host.
                _ = TransitionLog.objects.update_or_create(vm_id=vm_id, defaults={'vm_state': 8})
        except Exception as e2:  # There is a RpcError but not an Interactive one. This should not happen
            logger.exception(f"/grpc/{vm_id}/vm-info: Unexpected Execption occured: {e2}")
        return JsonResponse({'status': 1, 'message': ex_message}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed with {e}")
        return JsonResponse({'status': 1, 'message': "SERVER_ERROR"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return JsonResponse({'status': 0, 'context': {
        "guestOs": response_vm_info.guestOs,
        "memorySize": response_vm_info.memorySize,
        "numberOfCpus": response_vm_info.numberOfCpus,
        "sshPort": response_vm_info.sshPort,
        "rdpPort": response_vm_info.rdpPort,
        "host": response_vm_info.host,
        "sshPortStatus": response_vm_info.sshPortStatus,
        "rdpPortStatus": response_vm_info.rdpPortStatus,
        "state": response_vm_info.state,
    }})


# ---------------------------------------------------------------------
#   Software actions
# ---------------------------------------------------------------------
@check_permissions
@check_resources_exist("json")
def software_add(request, task_id, vm_id):
    if request.method == "GET":
        if not task_id or task_id is None or task_id == 'None':
            return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})
        
        software = model.add_software(task_id, vm_id)
        if not software:
            return JsonResponse({'status': 1, 'message': 'Failed to create a new Software.'},
                                status=HTTPStatus.INTERNAL_SERVER_ERROR)

        context = {
            "task": task_id,
            "vm_id": vm_id,
            "software": {
                "id": software['id'],
                "command": software['command'],
                "working_dir": software['working_directory'],
                "dataset": software['dataset'],
                "creation_date": software['creation_date'],
                "last_edit": software['last_edit']
            }
        }
        return JsonResponse({"status": 0, "message": "ok", "context": context})
    else:
        return JsonResponse({"status": 1, "message": "POST is not allowed here."})

@check_permissions
@check_resources_exist('json')
def software_save(request, task_id, vm_id, software_id):
    if request.method == "POST":
        data = json.loads(request.body)
        new_dataset = data.get("input_dataset")
        if not model.dataset_exists(new_dataset):
            return JsonResponse({'status': 1, 'message': f"Cannot save, the dataset {new_dataset} does not exist."})

        software = model.update_software(task_id, vm_id, software_id,
                                         data.get("command"),
                                         data.get("working_dir"),
                                         data.get("input_dataset"),
                                         data.get("input_run"))

        message = "failed to save software for an unknown reasons"
        try:
            if software:
                return JsonResponse({'status': 0, "message": f"Saved {software_id}", 'last_edit': software.lastEditDate},
                                    status=HTTPStatus.ACCEPTED)
        except Exception as e:
            message = str(e)

        return JsonResponse({'status': 1, "message": message}, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse({'status': 1, 'message': f"GET is not implemented for add dataset"})


@check_permissions
@check_resources_exist('json')
def software_delete(request, task_id, vm_id, software_id):
    delete_ok = model.delete_software(task_id, vm_id, software_id)

    if delete_ok:
        return JsonResponse({'status': 0}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse({'status': 1, 'message': 'Cannot delete software, because it has a valid '
                                                     'evaluation assigned (or it does not exist.)'},
                            status=HTTPStatus.INTERNAL_SERVER_ERROR)


@check_permissions
@check_resources_exist('json')
@host_call
def run_execute(request, task_id, vm_id, software_id):
    vm = model.get_vm(vm_id)
    software = model.get_software(task_id, vm_id, software_id=software_id)
    if not model.dataset_exists(software["dataset"]):
        return JsonResponse({'status': 1, 'message': f'The dataset {software["dataset"]} does not exist'})
    host = reroute_host(vm['host'])
    future_run_id = get_tira_id()
    grpc_client = GrpcClient(host)
    response = grpc_client.run_execute(vm_id=vm_id,
                                       dataset_id=software["dataset"],
                                       run_id=future_run_id,
                                       input_run_vm_id="",
                                       input_run_dataset_id="",
                                       input_run_run_id=software["run"],
                                       optional_parameters="",
                                       task_id=task_id,
                                       software_id=software_id)
    del grpc_client
    return response


@host_call
def _master_vm_eval_call(vm_id, dataset_id, run_id, evaluator):
    """ Called when the evaluation is done via master vm.
     This method calls the grpc client """
    host = reroute_host(evaluator["host"])
    grpc_client = GrpcClient(host)
    response = grpc_client.run_eval(vm_id=evaluator["vm_id"],
                                    dataset_id=dataset_id,
                                    run_id=get_tira_id(),
                                    input_run_vm_id=vm_id,
                                    input_run_dataset_id=dataset_id,
                                    input_run_run_id=run_id,
                                    optional_parameters="")
    del grpc_client
    return response


def _git_runner_vm_eval_call(vm_id, dataset_id, run_id, evaluator):
    """ called when the evaluation is done via git runner.
     This method calls the git utilities in git_runner.py to start the git CI
     """
    try:
        transaction_id = model.get_git_integration(dataset_id=dataset_id)\
                              .run_evaluate_with_git_workflow(evaluator['task_id'], dataset_id, vm_id, run_id,
                                                        evaluator['git_runner_image'], evaluator['git_runner_command'],
                                                        evaluator['git_repository_id'], evaluator['evaluator_id'])
    except Exception as e:
        return JsonResponse({'status': 1, 'message': str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return JsonResponse({'status': 0, 'message': transaction_id}, status=HTTPStatus.ACCEPTED)


@check_conditional_permissions(private_run_ok=True)
@check_resources_exist('json')
def run_eval(request, vm_id, dataset_id, run_id):
    """ Get the evaluator for dataset_id from the model.
     Then, send a GRPC-call to the host running the evaluator with the run data.
     Then, log vm_id and run_id to the evaluation log as ongoing.
    """
    # check if evaluation already exists
    if EvaluationLog.objects.filter(run_id=run_id):
        return JsonResponse({'status': '1', 'message': "An evaluation is already in progress."},
                            status=HTTPStatus.PRECONDITION_FAILED)

    evaluator = model.get_evaluator(dataset_id)
    if 'is_git_runner' in evaluator and evaluator['is_git_runner']:
        ret = _git_runner_vm_eval_call(vm_id, dataset_id, run_id, evaluator)
        git_runner = model.get_git_integration(dataset_id=dataset_id)
        running_pipelines = git_runner.all_running_pipelines_for_repository(
            evaluator['git_repository_id'],
            cache,
            force_cache_refresh=True
        )
        
        return ret

    return _master_vm_eval_call(vm_id, dataset_id, run_id, evaluator)


@check_conditional_permissions(private_run_ok=True)
def run_delete(request, dataset_id, vm_id, run_id):
    delete_ok = model.delete_run(dataset_id, vm_id, run_id)
    if delete_ok:
        return JsonResponse({'status': 0}, status=HTTPStatus.ACCEPTED)
    return JsonResponse({'status': 1, 'message': f"Can not delete run {run_id} since it is used as an input run."}, status=HTTPStatus.ACCEPTED)


@check_permissions
@check_resources_exist('json')
@host_call
def run_abort(request, vm_id):
    """ """
    vm = model.get_vm(vm_id)
    host = reroute_host(vm['host'])

    grpc_client = GrpcClient(host)
    response = grpc_client.run_abort(vm_id=vm_id)
    del grpc_client
    return response


@check_permissions
@check_resources_exist("json")
def upload(request, task_id, vm_id, dataset_id):
    if request.method == 'POST':
        if not dataset_id or dataset_id is None or dataset_id == 'None':
            return JsonResponse({"status": 1, "message": "Please specify the associated dataset."})

        uploaded_file = request.FILES['file']
        new_run = model.add_uploaded_run(task_id, vm_id, dataset_id, uploaded_file)
        if model.git_pipeline_is_enabled_for_task(task_id, cache):
            run_eval(request=request, vm_id=vm_id, dataset_id=dataset_id, run_id=new_run["run"]["run_id"])

            return JsonResponse({"status": 0, "message": "ok", "new_run": new_run, "started_evaluation": True})
        return JsonResponse({"status": 0, "message": "ok", "new_run": new_run, "started_evaluation": False})
    else:
        return JsonResponse({"status": 1, "message": "GET is not allowed here."})


@check_permissions
@check_resources_exist("json")
def docker_software_add(request, task_id, vm_id):
    if request.method == 'POST':
        if not task_id or task_id is None or task_id == 'None':
            return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})
        
        if not request.POST.get('image'):
            return JsonResponse({"status": 1, "message": "Please specify the associated docker image."})

        if not request.POST.get('command'):
            return JsonResponse({"status": 1, "message": "Please specify the associated docker command."})

        new_docker_software = model.add_docker_software(task_id, vm_id,
                                                        request.POST.get('image'), request.POST.get('command'),
                                                        request.POST.get('inputJob', None)
                                                        )
        return JsonResponse({"status": 0, "message": "ok", "context": new_docker_software})
    else:
        return JsonResponse({"status": 1, "message": "GET is not allowed here."})

@check_permissions
@check_resources_exist('json')
def docker_software_save(request, task_id, vm_id, docker_software_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            model.update_docker_software_metadata(docker_software_id,
                                         data.get("display_name"),
                                         data.get("description"),
                                         data.get("paper_link"))
            return JsonResponse({'status': 0, "message": "Software edited successfully"})
        except Exception as e:
            return JsonResponse({'status': 1, 'message': f"Error while editing software: " + str(e)})
    return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit software"})


@check_permissions
@check_resources_exist('json')
def docker_software_delete(request, task_id, vm_id, docker_software_id):
    delete_ok = model.delete_docker_software(task_id, vm_id, docker_software_id)

    if delete_ok:
        return JsonResponse({'status': 0}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse({'status': 1, 'message': 'Cannot delete docker software, because it has a valid '
                                                     'evaluation assigned (or it does not exist.)'},
                            status=HTTPStatus.INTERNAL_SERVER_ERROR)

@check_permissions
@check_resources_exist('json')
def run_execute_docker_software(request, task_id, vm_id, dataset_id, docker_software_id, docker_resources):
    if not task_id or task_id is None or task_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})

    if not vm_id or vm_id is None or vm_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated vm_id."})

    if not dataset_id or dataset_id is None or dataset_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated dataset_id."})

    evaluator = model.get_evaluator(dataset_id)
    
    if not evaluator or 'is_git_runner' not in evaluator or not evaluator['is_git_runner'] or 'git_runner_image' not in evaluator or not evaluator['git_runner_image'] or 'git_runner_command' not in evaluator or not evaluator['git_runner_command'] or 'git_repository_id' not in evaluator or not evaluator['git_repository_id']:
        return JsonResponse({"status": 1, "message": "The dataset is misconfigured. Docker-execute only available for git-evaluators"})

    if not docker_software_id or docker_software_id is None or docker_software_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated docker_software_id."})

    docker_software = model.get_docker_software(docker_software_id)
    
    if not docker_software:
        return JsonResponse({"status": 1, "message": f"There is no docker image with id {docker_software_id}"})

    input_run = None
    if 'input_docker_software_id' in docker_software and docker_software['input_docker_software_id']:
        input_run = model.latest_output_of_software_on_dataset(task_id, None, None, docker_software_id, dataset_id)
        if not input_run or not input_run.get('dataset_id', None) or not input_run.get('vm_id', None) or not input_run.get('run_id', None):
            return JsonResponse({"status": 1, "message":
                f"The execution of your software depends on the execution of {docker_software['input_docker_software']}"
                f", but {docker_software['input_docker_software']} was never executed on this dataset."
                f"Please execute first {docker_software['input_docker_software']} on your specified dataset."})


    git_runner = model.get_git_integration(task_id=task_id)
    git_runner.run_docker_software_with_git_workflow(
        task_id, dataset_id, vm_id, get_tira_id(), evaluator['git_runner_image'],
        evaluator['git_runner_command'], evaluator['git_repository_id'], evaluator['evaluator_id'],
        docker_software['tira_image_name'], docker_software['command'],
        'docker-software-' + docker_software_id, docker_resources,
        input_run
    )

    running_pipelines = git_runner.all_running_pipelines_for_repository(
        evaluator['git_repository_id'],
        cache,
        force_cache_refresh=True
    )
    print('Refreshed Cache for repo ' + str(evaluator['git_repository_id']) + ' with ' +
          str(len(running_pipelines)) + ' jobs.')
    
    return JsonResponse({'status': 0}, status=HTTPStatus.ACCEPTED)

@check_permissions
@check_resources_exist('json')
def stop_docker_software(request, task_id, user_id, run_id):
    if not request.method == 'GET':
        return JsonResponse({"status": 1, "message": "Only GET is allowed here"})
    else:
        datasets = model.get_datasets_by_task(task_id)
        git_runner = model.get_git_integration(task_id=task_id)

        if not git_runner:
            return JsonResponse({"status": 1, "message": f"No git integration found for task {task_id}"})

        for dataset in datasets:
            git_runner.stop_job_and_clean_up(
                model.get_evaluator(dataset["dataset_id"])["git_repository_id"],
                user_id, run_id, cache
            )

        return JsonResponse({"status": 0, "message": "Run successfully stopped"})

