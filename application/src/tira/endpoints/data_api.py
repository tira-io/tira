import logging
import json
from tira.forms import *
import tira.tira_model as model
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.views import add_context

from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from tira.git_runner import yield_all_running_pipelines

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
    role = context["role"]

    ev_keys, evaluations = model.get_evaluations_with_keys_by_dataset(dataset_id, True if role == "admin" else None)

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
    return JsonResponse({'status': 0, 'role': context['role']})


@check_resources_exist("json")
@add_context
def get_user(request, context, task_id, user_id):
    software = model.get_software_with_runs(task_id, user_id)
    upload = model.get_upload_with_runs(task_id, user_id)
    docker = model.load_docker_data(task_id, user_id, cache, force_cache_refresh=False)

    context["task"] = model.get_task(task_id)
    context["user_id"] = user_id
    context["vm"] = model.get_vm(user_id)
    context["software"] = software
    context["datasets"] = model.get_datasets_by_task(task_id)
    context["upload"] = upload
    context["docker"] = docker
    context["is_default"] = user_id.endswith("default")

    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_running_software(request, context, task_id, user_id):
    context['running_software'] = []
    
    evaluators_for_task = model.get_evaluators_for_task(task_id, cache)
    repositories = set([i['git_repository_id'] for i in evaluators_for_task if i['is_git_runner'] and i['git_repository_id']])


    for git_repository_id in sorted(list(repositories)):
        context['running_software'] += list(yield_all_running_pipelines(int(git_repository_id), user_id, cache))
        context['running_software_last_refresh'] = model.load_refresh_timestamp_for_cache_key(cache, 'all-running-pipelines-repo-' + str(i['git_repository_id']))
    for software in context['running_software']:
        if 'pipeline' in software:
            del software['pipeline']

    return JsonResponse({'status': 0, "context": context})

