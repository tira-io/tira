from django.template.loader import render_to_string
from django.db.utils import IntegrityError
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
import logging

from grpc import RpcError, StatusCode
from tira.authentication import auth
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.forms import *
from django.http import JsonResponse, HttpResponseNotAllowed
from django.conf import settings
from http import HTTPStatus

from tira.model import TransitionLog, EvaluationLog, TransactionLog
from tira.grpc_client import GrpcClient
import tira.tira_model as model
from tira.util import get_tira_id, reroute_host, link_to_discourse_team
from tira.views import add_context
from functools import wraps
import json
from markdown import markdown

include_navigation = True if settings.DEPLOYMENT == "legacy" else False
from discourse_client_in_disraptor.discourse_api_client import get_disraptor_user

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


@add_context
@check_permissions
def docker_software_details(request, context, vm_id, docker_software_id):
    context['docker_software_details'] = model.get_docker_software(int(docker_software_id))

    return JsonResponse({'status': 0, "context": context})


@add_context
@check_permissions
def upload_group_details(request, context, task_id, vm_id, upload_id):
    try:
        context['upload_group_details'] = model.get_upload(task_id, vm_id, upload_id)
    except Exception as e:
        return JsonResponse({'status': "1", 'message': f"An unexpected exception occurred: {e}"})

    return JsonResponse({'status': 0, "context": context})


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
    existing_evaluations = EvaluationLog.objects.filter(run_id=run_id)
    if existing_evaluations and len(existing_evaluations) > 5:
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

@csrf_exempt
@check_permissions
@check_resources_exist("json")
def upload(request, task_id, vm_id, dataset_id, upload_id):
    if request.method == 'POST':
        if not dataset_id or dataset_id is None or dataset_id == 'None':
            return JsonResponse({"status": 1, "message": "Please specify the associated dataset."})

        uploaded_file = request.FILES['file']
        new_run = model.add_uploaded_run(task_id, vm_id, dataset_id, upload_id, uploaded_file)
        if model.git_pipeline_is_enabled_for_task(task_id, cache):
            run_eval(request=request, vm_id=vm_id, dataset_id=dataset_id, run_id=new_run["run"]["run_id"])

            return JsonResponse({"status": 0, "message": "ok", "new_run": new_run, "started_evaluation": True})
        return JsonResponse({"status": 0, "message": "ok", "new_run": new_run, "started_evaluation": False})
    else:
        return JsonResponse({"status": 1, "message": "GET is not allowed here."})


@check_permissions
@check_resources_exist("json")
def delete_upload(request, task_id, vm_id, upload_id):
    try:
        model.delete_upload(task_id, vm_id, upload_id)
        return JsonResponse({"status": 0, "message": "ok"})
    except Exception as e:
        logger.warning('Failed to delete upload: ' + str(e))
        logger.exception(e)
        return JsonResponse({"status": 0, "message": "Failed" + str(e)})


@check_permissions
@check_resources_exist("json")
def add_upload(request, task_id, vm_id):
    if request.method == "GET":
        if not task_id or task_id is None or task_id == 'None':
            return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})
        rename_to = request.GET.get('rename_to', None)
        rename_to = None if not rename_to or not rename_to.strip() else rename_to

        upload = model.add_upload(task_id, vm_id, rename_to)
        if not upload:
            return JsonResponse({'status': 1, 'message': 'Failed to create a new Upload.'},
                                status=HTTPStatus.INTERNAL_SERVER_ERROR)

        context = {
            "task": task_id,
            "vm_id": vm_id,
            "upload": upload
        }
        return JsonResponse({"status": 0, "message": "ok", "context": context})
    else:
        return JsonResponse({"status": 1, "message": "POST is not allowed here."})


@csrf_exempt
@check_permissions
@check_resources_exist("json")
def docker_software_add(request, task_id, vm_id):
    if request.method == 'POST':
        if not task_id or task_id is None or task_id == 'None':
            return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})

        data = json.loads(request.body)
        if not data.get('image'):
            return JsonResponse({"status": 1, "message": "Please specify the associated docker image."})

        if not data.get('command'):
            return JsonResponse({"status": 1, "message": "Please specify the associated docker command."})

        submission_git_repo = None
        build_environment = None
        if data.get('code_repository_id'):
            submission_git_repo = model.model.get_submission_git_repo_or_none(data.get('code_repository_id'), vm_id, True)

            if not submission_git_repo:
                return JsonResponse({"status": 1, "message": f"The code repository '{data.get('code_repository_id'):}' does not exist."})

            if not data.get('build_environment'):
                return JsonResponse({"status": 1, "message": f"Please specify the build_environment for linking the code."})

            build_environment = json.dumps(data.get('build_environment'))

        new_docker_software = model.add_docker_software(task_id, vm_id,
                                                        data.get('image'), data.get('command'),
                                                        data.get('inputJob', None),
                                                        submission_git_repo, build_environment
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
                                         data.get("paper_link"),
                                         data.get("ir_re_ranker", False),
                                         data.get("ir_re_ranking_input", False))
            return JsonResponse({'status': 0, "message": "Software edited successfully"})
        except Exception as e:
            return JsonResponse({'status': 1, 'message': f"Error while editing software: " + str(e)})
    return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit software"})


@check_permissions
def add_software_submission_git_repository(request, task_id, vm_id):
    if request.method != "POST":
        return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit upload"})

    try:
        data = json.loads(request.body)
        external_owner = data['external_owner']
        private = not data.get('allow_public_repo', False)
        disraptor_user = get_disraptor_user(request, allow_unauthenticated_user=False)

        if not disraptor_user or not type(disraptor_user) == str:
            return JsonResponse({'status': 1, 'message': f"Please authenticate."})

        if not model.github_user_exists(external_owner):
            return JsonResponse({'status': 1, 'message': f"The user '{external_owner}' does not exist on Github, maybe a typo?"})

        software_submission_git_repo = model.get_submission_git_repo(vm_id, task_id, disraptor_user, external_owner,
                                                                     private)

        return JsonResponse({'status': 0, "context": software_submission_git_repo})
    except Exception as e:
        logger.exception(e)
        logger.warning('Error while adding your git repository: ' + str(e))
        return JsonResponse({'status': 1, 'message': f"Error while adding your git repository: " + str(e)})

@check_permissions
def get_token(request, vm_id):
    disraptor_user = get_disraptor_user(request, allow_unauthenticated_user=False)

    if not disraptor_user or not type(disraptor_user) == str:
        return JsonResponse({'status': 1, 'message': f"Please authenticate."})

    try:
        return JsonResponse({'status': 0, "context": {'token': model.get_discourse_token_for_user(vm_id, disraptor_user)}})
    except:
        return JsonResponse({'status': 1, 'message': f"Could not extract the discourse/disraptor user, please authenticate."})

@check_permissions
def get_software_submission_git_repository(request, task_id, vm_id):
    try:
        if task_id not in settings.CODE_SUBMISSION_REFERENCE_REPOSITORIES or not model.load_docker_data(task_id, vm_id, cache, force_cache_refresh=False):
            return JsonResponse({'status': 0, "context": {'disabled': True}})

        return JsonResponse({'status': 0, "context": model.get_submission_git_repo(vm_id, task_id)})
    except Exception as e:
        logger.exception(e)
        logger.warning('Error while getting your git repository: ' + str(e))
        return JsonResponse({'status': 1, 'message': f"Error while getting your git repository: " + str(e)})


@check_permissions
@check_resources_exist('json')
def upload_save(request, task_id, vm_id, upload_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            model.update_upload_metadata(task_id, vm_id, upload_id,
                                         data.get("display_name"),
                                         data.get("description"),
                                         data.get("paper_link"))
            return JsonResponse({'status': 0, "message": "Software edited successfully"})
        except Exception as e:
            logger.exception(e)
            logger.warning('Error while editing upload: ' + str(e))
            return JsonResponse({'status': 1, 'message': f"Error while editing upload: " + str(e)})
    return JsonResponse({'status': 1, 'message': f"GET is not implemented for edit upload"})


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


def __normalize_command(cmd, evaluator):
    to_normalize = {'inputRun': '/tira-data/input-run',
                    'outputDir': '/tira-data/output',
                    'inputDataset': '/tira-data/input'
                    }

    if 'inputRun' in cmd and evaluator:
        to_normalize['outputDir'] = '/tira-data/eval_output'
        to_normalize['inputDataset'] = '/tira-data/input_truth'

    for k, v in to_normalize.items():
        cmd = cmd.replace('$' + k, v).replace('${' + k + '}', v)

    return cmd


def construct_verbosity_output(image, command, approach, task, dataset):
    command = __normalize_command(command, '')
    return {
        'tira_run_export': f'tira-run --export-dataset {task}/{dataset} --output-directory tira-dataset',
        'cli_command': 'tira-run \\\n  --input-directory tira-dataset \\\n  --output-directory tira-output \\\n  ' +
                       '--approach \'' + approach + '\'',
        'python_command': f'tira.run("{approach}", "tira-dataset")',
        'docker_command': 'docker run --rm -ti \\\n  -v ${PWD}/tira-dataset:/tira-data/input:ro \\\n  -v '
                          '${PWD}/tira-output:/tira-data/output:rw -\\\n  -entrypoint sh ' + f'\\\n  '
                          f't{image} \\\n  -c \'{command}\'',
        'image': image, 'command': command
    }


def __rendered_references(task_id, vm_id, run):
    task = model.get_task(task_id)
    bib_references = {
        'run': '@Comment {No bib entry specified for the run, please contact the team/organizers for clarification.}',
        'task': '@Comment {No bib entry specified for the task, please contact the organizers for clarification.}',
        'dataset': '@Comment {No bib entry specified for the dataset, please contact the organizers for clarification.}',
    }
    markdown_references = {'run': None, 'task': None, 'dataset': None}

    if run['dataset'] == 'antique-test-20230107-training':
        markdown_references['dataset'] = '[ANTIQUE](https://ir.webis.de/anthology/2020.ecir_conference-20202.21/) ' + \
                                         'is a  non-factoid quesiton answering dataset based on the questions and ' + \
                                         'answers of Yahoo! Webscope L6.'
        bib_references['dataset'] = '''@inproceedings{Hashemi2020Antique,
  title        = {ANTIQUE: A Non-Factoid Question Answering Benchmark},
  author       = {Helia Hashemi and Mohammad Aliannejadi and Hamed Zamani and Bruce Croft},
  booktitle    = {ECIR},
  year         = {2020}
}'''

    if task_id == 'ir-benchmarks':
        markdown_references['task'] = '[TIRA](https://webis.de/publications?q=TIRA#froebe_2023b) ' + \
                                      'respectively [TIREx](https://webis.de/publications#froebe_2023e) ' + \
                                      'is used to enable reprodicible and blinded experiments.'
        bib_references['task'] = '''@InProceedings{froebe:2023b,
  address =                  {Berlin Heidelberg New York},
  author =                   {Maik Fr{\"o}be and Matti Wiegmann and Nikolay Kolyada and Bastian Grahm and Theresa Elstner and Frank Loebe and Matthias Hagen and Benno Stein and Martin Potthast},
  booktitle =                {Advances in Information Retrieval. 45th European Conference on {IR} Research ({ECIR} 2023)},
  doi =                      {10.1007/978-3-031-28241-6_20},
  editor =                   {Jaap Kamps and Lorraine Goeuriot and Fabio Crestani and Maria Maistro and Hideo Joho and Brian Davis and Cathal Gurrin and Udo Kruschwitz and Annalina Caputo},
  month =                    apr,
  pages =                    {236--241},
  publisher =                {Springer},
  series =                   {Lecture Notes in Computer Science},
  site =                     {Dublin, Irland},
  title =                    {{Continuous Integration for Reproducible Shared Tasks with TIRA.io}},
  todo =                     {pages, code},
  url =                      {https://doi.org/10.1007/978-3-031-28241-6_20},
  year =                     2023
}

@InProceedings{froebe:2023e,
  author =                   {Maik Fr{\"o}be and {Jan Heinrich} Reimer and Sean MacAvaney and Niklas Deckers and Simon Reich and Janek Bevendorff and Benno Stein and Matthias Hagen and Martin Potthast},
  booktitle =                {46th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR 2023)},
  month =                    jul,
  publisher =                {ACM},
  site =                     {Taipei, Taiwan},
  title =                    {{The Information Retrieval Experiment Platform}},
  todo =                     {annote, doi, editor, pages, url, videourl},
  year =                     2023
}'''

    if run['software'] == 'MonoT5 3b (tira-ir-starter-gygaggle)':
        markdown_references['run'] = 'The implementation of [MonoT5](https://arxiv.org/abs/2101.05667) in [PyGaggle](https://ir.webis.de/anthology/2021.sigirconf_conference-2021.304/).'
        bib_references['run'] = '''@article{DBLP:journals/corr/abs-2101-05667,
  author       = {Ronak Pradeep and Rodrigo Frassetto Nogueira and Jimmy Lin},
  title        = {The Expando-Mono-Duo Design Pattern for Text Ranking with Pretrained Sequence-to-Sequence Models},
  journal      = {CoRR},
  volume       = {abs/2101.05667},
  year         = {2021},
  url          = {https://arxiv.org/abs/2101.05667},
  eprinttype    = {arXiv},
  eprint       = {2101.05667},
  timestamp    = {Mon, 20 Mar 2023 15:35:34 +0100},
  biburl       = {https://dblp.org/rec/journals/corr/abs-2101-05667.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}

@inproceedings{lin-2021-pyserini,
  author    = {Jimmy Lin and Xueguang Ma and Sheng{-}Chieh Lin and Jheng{-}Hong Yang and Ronak Pradeep and Rodrigo Frassetto Nogueira},
  editor    = {Fernando Diaz and Chirag Shah and Torsten Suel and Pablo Castells and Rosie Jones and Tetsuya Sakai},
  title     = {Pyserini: {A} Python Toolkit for Reproducible Information Retrieval Research with Sparse and Dense Representations},
  booktitle = {{SIGIR} '21: The 44th International {ACM} {SIGIR} Conference on Research and Development in Information Retrieval, Virtual Event, Canada, July 11-15, 2021},
  pages     = {2356--2362},
  publisher = {{ACM}},
  year      = {2021},
  url       = {https://doi.org/10.1145/3404835.3463238},
  doi       = {10.1145/3404835.3463238},
  timestamp = {Mon, 20 Mar 2023 15:35:34 +0100},
  biburl    = {https://dblp.org/rec/conf/sigir/LinMLYPN21.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}'''

    if run['software'] == 'DLH (tira-ir-starter-pyterrier)':
        markdown_references['run'] = 'The implementation of [DLH](https://ir.webis.de/anthology/2006.ecir_conference-2006.3/) in [PyTerrier](https://ir.webis.de/anthology/2021.cikm_conference-2021.533/).'
        bib_references['run'] = '''@inproceedings{amati-2006-frequentist,
  author    = {Giambattista Amati},
  editor    = {Mounia Lalmas and Andy MacFarlane and Stefan M. R{\"{u}}ger and Anastasios Tombros and Theodora Tsikrika and Alexei Yavlinsky},
  title     = {Frequentist and Bayesian Approach to Information Retrieval},
  booktitle = {Advances in Information Retrieval, 28th European Conference on {IR} Research, {ECIR} 2006, London, UK, April 10-12, 2006, Proceedings},
  series    = {Lecture Notes in Computer Science},
  volume    = {3936},
  pages     = {13--24},
  publisher = {Springer},
  year      = {2006},
  url       = {https://doi.org/10.1007/11735106\_3},
  doi       = {10.1007/11735106\_3},
  timestamp = {Tue, 14 May 2019 10:00:37 +0200},
  biburl    = {https://dblp.org/rec/conf/ecir/Amati06.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}       
        
@inproceedings{macdonald-2021-pyterrier,
  author    = {Craig Macdonald and Nicola Tonellotto and Sean MacAvaney and Iadh Ounis},
  editor    = {Gianluca Demartini and Guido Zuccon and J. Shane Culpepper and Zi Huang and Hanghang Tong},
  title     = {PyTerrier: Declarative Experimentation in Python from {BM25} to Dense
               Retrieval},
  booktitle = {{CIKM} '21: The 30th {ACM} International Conference on Information and Knowledge Management, Virtual Event, Queensland, Australia, November 1 - 5, 2021},
  pages     = {4526--4533},
  publisher = {{ACM}},
  year      = {2021},
  url       = {https://doi.org/10.1145/3459637.3482013},
  doi       = {10.1145/3459637.3482013},
  timestamp = {Tue, 02 Nov 2021 12:01:17 +0100},
  biburl    = {https://dblp.org/rec/conf/cikm/MacdonaldTMO21.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}'''


    print(run)
    ret_bib = ''
    ret_markdown = ['Please cite the approach / resources if you use them. Potential candidates are:']
    missing_references = []
    for t in ['run', 'dataset', 'task']:
        ret_bib += bib_references[t] + '\n\n'
        if markdown_references[t]:
            ret_markdown += [markdown_references[t]]
        else:
            missing_references += [t]

    if missing_references:
        ret_markdown += ['There are missing references for ' + (', '.join(missing_references)) + '. ' +
                         'Please contact the organizers ' +
                         f'[{task["organizer"]}](https://www.tira.io/g/tira_org_{task["organizer_id"]}) or the team ' +
                         f'[{vm_id}]({link_to_discourse_team(vm_id)}) for clarification.'
                         ]

    return ret_bib.strip(), markdown('<br>'.join(ret_markdown).strip())

@check_permissions
@check_resources_exist('json')
def run_details(request, task_id, vm_id, run_id):
    run = model.get_run(dataset_id=None, vm_id=vm_id, run_id=run_id)
    software, docker_software, run_upload = None, None, None
    vm_id_from_run = None

    repro_details = {'tira-run-export': None, 'tira-run-cli': None, 'tira-run-python': None, 'docker': None}


    if 'software_id' in run and run['software_id']:
        software = model.get_software(software)
        vm_id_from_run = software['vm']
    elif 'docker_software_id' in run and run['docker_software_id']:
        docker_software = model.get_docker_software(run['docker_software_id'])
        print(docker_software)
        vm_id_from_run = docker_software['vm_id']

        if docker_software['public_image_name']:
            repro_details = construct_verbosity_output(docker_software['public_image_name'], docker_software['command'],
                                                       task_id + '/' + vm_id + '/' + docker_software['display_name'],
                                                       task_id, run['dataset'])

    elif 'upload_id' in run and run['upload_id']:
        import tira.model as modeldb
        run_upload = modeldb.Upload.objects.filter(vm__vm_id=vm_id, id=run['upload_id']).get()
        vm_id_from_run = run_upload.vm.vm_id

    if not vm_id_from_run or vm_id != vm_id_from_run:
        return HttpResponseNotAllowed(f"Access forbidden.")

    ret = {'description': 'No description is available.', 'previous_stage': None,
           'cli_command': None, 'docker_command': None, 'python_command': None
           }

    ret['references_bibtex'], ret['references_markdown'] = __rendered_references(task_id, vm_id, run)

    for k, v in repro_details.items():
        ret[k] = v

    return JsonResponse({'status': 0, 'context': ret})


@check_permissions
@check_resources_exist('json')
def software_details(request, task_id, vm_id, software_name):
    docker_software = model.get_docker_software_by_name(software_name, vm_id, task_id)

    if not docker_software:
        return JsonResponse({'status': 0, 'message': f'Could not find a software with name "{software_name}"'})

    repro_details = {'tira-run-export': None, 'tira-run-cli': None, 'tira-run-python': None, 'docker': None, 'image': None, 'command': None}
    if docker_software['public_image_name']:
        repro_details = construct_verbosity_output(docker_software['public_image_name'], docker_software['command'],
                                                       task_id + '/' + vm_id + '/' + docker_software['display_name'],
                                                       task_id, '<dataset>')

    ret = {'description': 'No description is available.', 'previous_stage': None,
           'cli_command': 'TBD cli.', 'docker_command': 'TBD docker.', 'python_command': 'TBD python.'
           }

    for k, v in repro_details.items():
        ret[k] = v

    return JsonResponse({'status': 0, 'context': ret})


@check_permissions
@check_resources_exist('json')
def run_execute_docker_software(request, task_id, vm_id, dataset_id, docker_software_id, docker_resources, rerank_dataset=None):
    if not task_id or task_id is None or task_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})

    if not vm_id or vm_id is None or vm_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated vm_id."})

    if not docker_software_id or docker_software_id is None or docker_software_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated docker_software_id."})

    docker_software = model.get_docker_software(docker_software_id)

    if not docker_software:
        return JsonResponse({"status": 1, "message": f"There is no docker image with id {docker_software_id}"})

    input_run = None
    if 'ir_re_ranker' in docker_software and docker_software.get('ir_re_ranker', False) and rerank_dataset and rerank_dataset.lower() != 'none':
        reranking_datasets = model.get_all_reranking_datasets()

        if rerank_dataset not in reranking_datasets:
            background_process = None
            try:
                background_process = model.create_re_rank_output_on_dataset(task_id, vm_id, software_id=None,
                                                                            docker_software_id=docker_software_id,
                                                                            dataset_id=dataset_id)
            except Exception as e:
                logger.warning(e)

            visit_job_message = 'Failed to start job.'

            if background_process:
                visit_job_message = f'Please visit https://tira.io/background_jobs/{task_id}/{background_process} ' + \
                                     ' to view the progress of the job that creates the rerank output.'

            return JsonResponse({"status": 1, "message":
                f"The execution of your software depends on the reranking dataset {rerank_dataset}"
                f", but {rerank_dataset} was never executed on the dataset {dataset_id}. "
                f"Please execute first the software on the specified dataset so that you can re-rank it. "
                f"{visit_job_message}"})

        input_run = reranking_datasets[rerank_dataset]
        input_run['replace_original_dataset'] = True

        if dataset_id != input_run['dataset_id']:
            return JsonResponse({"status": 1, "message": "There seems to be a configuration error:" +
                                                         f" The reranking dataset {input_run['dataset_id']} is not" +
                                                         f" the specified dataset {dataset_id}."})

        assert dataset_id == input_run['dataset_id']

    if not dataset_id or dataset_id is None or dataset_id == 'None':
        return JsonResponse({"status": 1, "message": "Please specify the associated dataset_id."})

    evaluator = model.get_evaluator(dataset_id)
    
    if not evaluator or 'is_git_runner' not in evaluator or not evaluator['is_git_runner'] or 'git_runner_image' not in evaluator or not evaluator['git_runner_image'] or 'git_runner_command' not in evaluator or not evaluator['git_runner_command'] or 'git_repository_id' not in evaluator or not evaluator['git_repository_id']:
        return JsonResponse({"status": 1, "message": "The dataset is misconfigured. Docker-execute only available for git-evaluators"})

    input_runs, errors = model.get_ordered_input_runs_of_software(docker_software, task_id, dataset_id, vm_id)

    if errors:
        return JsonResponse({"status": 1, "message": errors[0]})

    git_runner = model.get_git_integration(task_id=task_id)
    git_runner.run_docker_software_with_git_workflow(
        task_id, dataset_id, vm_id, get_tira_id(), evaluator['git_runner_image'],
        evaluator['git_runner_command'], evaluator['git_repository_id'], evaluator['evaluator_id'],
        docker_software['tira_image_name'], docker_software['command'],
        'docker-software-' + docker_software_id, docker_resources,
        input_run if input_run else input_runs
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

