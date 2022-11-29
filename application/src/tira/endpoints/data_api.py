import logging
import json
from tira.forms import *
import tira.tira_model as model
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.tira_data import get_run_runtime, get_run_file_list, get_stderr, get_stdout, get_tira_log
from tira.views import add_context, _add_user_vms_to_context
from tira.authentication import auth

from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from tira.git_runner import yield_all_running_pipelines
import datetime

include_navigation = True if settings.DEPLOYMENT == "legacy" else False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


@check_resources_exist('json')
@add_context
def get_dataset_for_task(request, context, task_id):
    if request.method == 'GET':
        try:
            datasets = model.get_datasets_by_task(task_id)

            context['datasets'] = json.dumps({ds['dataset_id']: ds for ds in datasets}, cls=DjangoJSONEncoder)
            context['selected_dataset_id'] = ''
            context['test_dataset_ids'] = json.dumps([ds['dataset_id'] for ds in datasets if ds['is_confidential']], cls=DjangoJSONEncoder)
            context['training_dataset_ids'] = json.dumps([ds['dataset_id'] for ds in datasets if not ds['is_confidential']], cls=DjangoJSONEncoder)
            return JsonResponse({"status": "0", "context": context})
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"status": "0", "message": f"Encountered an exception: {e}"})


@check_resources_exist('json')
@add_context
def get_evaluations_by_dataset(request, context, task_id, dataset_id):
    """ Return all evaluation results for all submission to a dataset
    The frontend calls this to build the leaderboard
    in the task page when a task is selected from the dropdown

    @param request:
    @param context:
    @param task_id:
    @param dataset_id:
    @return: {
    ...
    ev_keys: a list of the keys of the evaluation measures (different for each task/dataset)
    evaluations: a list of dicts {vm_id, run_id, input_run_id, published, blinded, measures} , one for each vm
                 measures is a list sorted by the keys in ev_keys
    }
    """
    role = context["role"]

    ev_keys, evaluations = model.get_evaluations_with_keys_by_dataset(dataset_id, True if role == "admin" else None)

    context["task_id"] = task_id
    context["dataset_id"] = dataset_id
    context["ev_keys"] = ev_keys
    context["evaluations"] = evaluations

    return JsonResponse({'status': 1, "context": context})


@check_permissions
@add_context
def get_evaluation(request, context, run_id, vm_id):
    run = model.get_run(None, None, run_id)
    review = model.get_run_review(None, None, run_id)
    
    if not run['is_evaluation'] or not vm_id:
        # We need the vm_id to get the check working, otherwise we have no direct link to the vm.
        return JsonResponse({'status': 1, "message": f"Run {run_id} is not an evaluation run."})

    dataset = model.get_dataset(run['dataset'])
    
    if context['role'] != 'admin' and review["blinded"] and dataset['is_confidential']:
        return JsonResponse({'status': 1, "message": f"Run {run_id} is not unblinded."})

    context["evaluation"] = model.get_evaluation(run_id)

    return JsonResponse({'status': 0, "context": context})


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
    context["user_is_registered"] = model.user_is_registered(task_id, request)
    context["remaining_team_names"] = model.remaining_team_names(task_id)
    _add_user_vms_to_context(request, context, task_id)
    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_dataset(request, context, dataset_id):
    context["dataset"] = model.get_dataset(dataset_id)
    context["evaluator"] = model.get_evaluator(dataset_id)

    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_organizer(request, context, organizer_id):
    org = model.get_organizer(organizer_id)
    return JsonResponse({'status': 0, "context": org})


@add_context
def get_role(request, context):
    return JsonResponse({'status': 0, 'role': context['role'], 'organizer_teams': auth.get_organizer_ids(request)})


@check_resources_exist("json")
@add_context
def update_docker_images(request, context, task_id, user_id):
    docker = model.load_docker_data(task_id, user_id, cache, force_cache_refresh=True)
    context["docker"] = docker

    return JsonResponse({'status': 0, "context": context})

@check_resources_exist("json")
@add_context
def get_user(request, context, task_id, user_id):
    software = model.get_software_with_runs(task_id, user_id)
    upload = model.get_upload_with_runs(task_id, user_id)
    docker = model.load_docker_data(task_id, user_id, cache, force_cache_refresh=False)
    vm = model.get_vm(user_id)

    context["task"] = model.get_task(task_id)
    context["user_id"] = user_id
    context["vm"] = vm
    context["software"] = software
    context["datasets"] = model.get_datasets_by_task(task_id)
    context["upload"] = upload
    context["docker"] = docker
    
    # is_default indicates whether the user has a docker-only team, i.e., no virtual machine.
    # This is the case if the user-vm ends with default or if no host or admin name is configured.
    context["is_default"] = user_id.endswith("default") or not vm['host'] or not vm['admin_name']

    _add_user_vms_to_context(request, context, task_id)

    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_running_software(request, context, task_id, user_id, force_cache_refresh):
    context['running_software'] = []
    
    evaluators_for_task = model.get_evaluators_for_task(task_id, cache)
    repositories = set([i['git_repository_id'] for i in evaluators_for_task if i['is_git_runner'] and i['git_repository_id']])

    for git_repository_id in sorted(list(repositories)):
        context['running_software'] += list(yield_all_running_pipelines(int(git_repository_id), user_id, cache, force_cache_refresh=eval(force_cache_refresh)))
        context['running_software_last_refresh'] = model.load_refresh_timestamp_for_cache_key(cache, 'all-running-pipelines-repo-' + str(git_repository_id))
        context['running_software_next_refresh'] = str(context['running_software_last_refresh'] + datetime.timedelta(seconds=15))
        context['running_software_last_refresh'] = str(context['running_software_last_refresh'])

    for software in context['running_software']:
        if 'pipeline' in software:
            del software['pipeline']

    return JsonResponse({'status': 0, "context": context})


@check_permissions
@check_resources_exist("json")
@add_context
def get_review(request, context, dataset_id, vm_id, run_id):
    context["dataset"] = model.get_dataset(dataset_id)
    context["run"] = model.get_run(None, None, run_id)
    context["review"] = model.get_run_review(dataset_id, vm_id, run_id)
    context["runtime"] = get_run_runtime(dataset_id, vm_id, run_id)
    context["files"] = get_run_file_list(dataset_id, vm_id, run_id)
    if context['role'] == 'admin':
        context["files"]["file_list"][0] = "output/"
        context["stdout"] = get_stdout(dataset_id, vm_id, run_id)
        context["stderr"] = get_stderr(dataset_id, vm_id, run_id)
        context["tira_log"] = get_tira_log(dataset_id, vm_id, run_id)
    elif (context['role'] == auth.ROLE_PARTICIPANT) and not context['dataset'].get('is_confidential', True):
        context["files"]["file_list"][0] = "output/"
        context["stdout"] = get_stdout(dataset_id, vm_id, run_id)
        context["stderr"] = get_stderr(dataset_id, vm_id, run_id)
        context["review"]['blinded'] = False
        context["tira_log"] = "hidden"
    else:
        context["files"]["file_list"] = []
        context["stdout"] = "hidden"
        context["stderr"] = "hidden"
        context["tira_log"] = "hidden"

    return JsonResponse({'status': 0, "context": context})


@add_context
def add_registration(request, context, task_id, vm_id):
    """ get the registration of a user on a task. If there is none """

    data = json.loads(request.body)
    data['initial_owner'] = context['user_id']
    data['task_id'] = task_id
    model.add_registration(data)

    auth.create_docker_group(data['group'], data['initial_owner'])
    auth.notify_organizers_of_new_participants(data, task_id)

    context['user_is_registered'] = True
    context['vm_id'] = data['group']
    context['user_vms_for_task'] = [data['group']]

    return JsonResponse({'status': 0, "context": context})

