import logging
import json
from tira.forms import *
import tira.tira_model as model
from tira.checks import check_permissions, check_resources_exist, check_conditional_permissions
from tira.tira_data import get_run_runtime, get_run_file_list, get_stderr, get_stdout, get_tira_log
from tira.views import add_context, _add_user_vms_to_context
from tira.authentication import auth

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from http import HTTPStatus
import datetime
import csv
from io import StringIO
from copy import deepcopy
from tira.util import link_to_discourse_team

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


def __normalize_run(i, ev_keys, is_admin, user_vms_for_task, task_id, is_ir_task, is_training_dataset=False):
    i = deepcopy(i)
    i['link_to_team'] = link_to_discourse_team(i['vm_id'])
    eval_run_id = i["run_id"]
    for k, v in [('input_run_id', 'run_id')]:
        i[v] = i[k]
        del i[k]

    if is_admin or i['published'] or is_training_dataset:
        for j in range(len(ev_keys)):
            i[ev_keys[j]] = i['measures'][j]

    for j in ['measures']:
        del i[j]

    i['selectable'] = False
    i['owned_by_user'] = is_admin or i['vm_id'] in user_vms_for_task

    if not i['blinded'] and (i['owned_by_user'] or i['published'] or is_training_dataset):
        i[
            'link_results_download'] = f'/task/{task_id}/user/{i["vm_id"]}/dataset/{i["dataset_id"]}/download/{eval_run_id}.zip'
        i[
            'link_run_download'] = f'/task/{task_id}/user/{i["vm_id"]}/dataset/{i["dataset_id"]}/download/{i["run_id"]}.zip'
        if is_ir_task:
            i['link_serp'] = f'/serp/{task_id}/user/{i["vm_id"]}/dataset/{i["dataset_id"]}/10/{i["run_id"]}'
            i['selectable'] = True
    return i


def __inject_user_vms_for_task(request, context, task_id):
    _add_user_vms_to_context(request, context, task_id, include_docker_details=False)
    return context['user_vms_for_task'] if 'user_vms_for_task' in context else []


@add_context
def get_configuration_of_evaluation(request, context, task_id, dataset_id):
    dataset = model.get_dataset(dataset_id)

    context['dataset'] = {
        "display_name": dataset['display_name'],
        "evaluator_id": dataset['evaluator_id'],
        "dataset_id": dataset['dataset_id'],
        "evaluator_git_runner_image": dataset['evaluator_git_runner_image'],
        "evaluator_git_runner_command": dataset['evaluator_git_runner_command'],
    }

    return JsonResponse({'status': 0, "context": context})


@add_context
@check_resources_exist('json')
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
    task = model.get_task(task_id, False)
    is_ir_task = 'is_ir_task' in task and task['is_ir_task']
    is_admin = context["role"] == "admin"
    show_only_unreviewed = request.GET.get('show_only_unreviewed', 'false').lower() == 'true'
    print(show_only_unreviewed)
    ev_keys, evaluations = model.get_evaluations_with_keys_by_dataset(dataset_id, is_admin, show_only_unreviewed)
    user_vms_for_task = __inject_user_vms_for_task(request, context, task_id)

    context["task_id"] = task_id
    context["dataset_id"] = dataset_id
    context["ev_keys"] = ev_keys
    context["evaluations"] = sorted(evaluations, key=lambda r: r['run_id'])
    headers = [{'title': 'Team', 'key': 'vm_id'}, {'title': 'Approach', 'key': 'input_software_name'},
               {'title': 'Run', 'key': 'run_id'}]
    evaluation_headers = [{'title': k, 'key': k} for k in ev_keys]

    context["table_headers"] = headers + evaluation_headers + [{'title': '', 'key': 'actions', 'sortable': False}]
    context["table_headers_small_layout"] = [headers[1]] + evaluation_headers[:1]

    context["table_sort_by"] = [{'key': ev_keys[0], 'order': 'desc'}] if ev_keys else []

    runs = []
    for i in evaluations:
        runs += [__normalize_run(i, ev_keys, is_admin, user_vms_for_task, task_id, is_ir_task)]

    context["runs"] = runs

    return JsonResponse({'status': 0, "context": context})


@add_context
@check_permissions
def get_evaluations_by_vm(request, context, task_id, vm_id):
    task = model.get_task(task_id, False)
    is_ir_task = 'is_ir_task' in task and task['is_ir_task']
    is_admin = context["role"] == "admin"
    user_vms_for_task = __inject_user_vms_for_task(request, context, task_id)

    docker_software_id = request.GET.get('docker_software_id', '')
    upload_id = request.GET.get('upload_id', '')

    if not docker_software_id and not upload_id or (docker_software_id and upload_id):
        return JsonResponse({'status': 1, "message": 'Please pass either a docker_software_id or a upload_id. Got: ' +
                                          f'upload_id = "{upload_id}" docker_software_id = "{docker_software_id}".'})

    ev_keys, evaluations = model.get_runs_for_vm(vm_id, docker_software_id, upload_id)

    context["task_id"] = task_id
    context["ev_keys"] = ev_keys
    headers = [{'title': 'Dataset', 'key': 'dataset_id'}, {'title': 'Run', 'key': 'run_id'}]

    context["table_sort_by"] = [{'key': 'run_id', 'order': 'desc'}]

    runs = []
    covered_evaluation_headers = set()

    for i in evaluations:
        if 'dataset_id' not in i or not i['dataset_id']:
            continue
        dataset_id = i['dataset_id']
        is_training_dataset = dataset_id.endswith('-training')
        i = __normalize_run(i, ev_keys, is_admin, user_vms_for_task, task_id, is_ir_task, is_training_dataset)
        i['dataset_id'] = dataset_id
        for k in ev_keys:
            if k in i:
                covered_evaluation_headers.add(k)
        runs += [i]
    context["runs"] = runs

    evaluation_headers = [{'title': k, 'key': k} for k in ev_keys if k in covered_evaluation_headers]

    context["table_headers"] = headers + evaluation_headers + [{'title': '', 'key': 'actions', 'sortable': False}]
    context["table_headers_small_layout"] = headers

    return JsonResponse({'status': 0, "context": context})


@add_context
@check_permissions
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
def get_evaluations_of_run(request, context, vm_id, run_id):
    context['evaluations'] = model.get_evaluations_of_run(vm_id, run_id)
    return JsonResponse({'status': 0, "context": context})


@check_permissions
@check_resources_exist("json")
@add_context
def get_ova_list(request, context):
    context["ova_list"] = model.get_ova_list()
    return JsonResponse({'status': 0, "context": context})


@add_context
def runs(request, context, task_id, dataset_id, vm_id, software_id):
    context["runs"] = model.runs(task_id, dataset_id, vm_id, software_id)
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
    organizer_list = model.get_organizer_list()
    is_admin = context and 'role' in context and context['role'] == 'admin'
    orga_groups_of_user = set(auth.get_organizer_ids(request))
    
    context["organizer_list"] = [i for i in organizer_list if is_admin or ('organizer_id' in i and i['organizer_id'] in orga_groups_of_user)]
    
    
    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_task_list(request, context):
    context["task_list"] = model.get_tasks()
    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_registration_formular(request, context, task_id):
    context["remaining_team_names"] = model.remaining_team_names(task_id)

    return JsonResponse({'status': 0, "context": context})


@check_resources_exist("json")
@add_context
def get_task(request, context, task_id):
    context["task"] = model.get_task(task_id)
    context["user_is_registered"] = model.user_is_registered(task_id, request)
    # TODO: remove this when vuetify frontend is active
    context["remaining_team_names"] = []
    context["datasets"] = model.get_datasets_by_task(task_id, return_only_names=True)
    context["datasets"] = sorted(context["datasets"], key=lambda i: i['display_name'])
    for d in context["datasets"]:
        if not d['display_name']:
            d['display_name'] = d['dataset_id']

    _add_user_vms_to_context(request, context, task_id, include_docker_details=False)
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
    docker = model.load_docker_data(task_id, user_id, cache, force_cache_refresh=False)
    vm = model.get_vm(user_id)
    context["task"] = model.get_task(task_id)
    context["user_id"] = user_id
    context["vm"] = vm
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
    git_runner = model.get_git_integration(task_id=task_id)

    for git_repository_id in sorted(list(repositories)):
        context['running_software'] += list(git_runner.yield_all_running_pipelines(int(git_repository_id), user_id, cache, force_cache_refresh=eval(force_cache_refresh)))
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
    elif (context['role'] == auth.ROLE_PARTICIPANT) and ((not context['dataset'].get('is_confidential', True)) or not context["review"]['blinded']):
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
    try:
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
    except Exception as e:
        logger.warning(e)
        logger.exception(e)
        return JsonResponse({'status': 0, "message": f"Encountered an exception: {e}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@add_context
def tirex_components(request, context):
    context['tirex_components'] = settings.TIREX_COMPONENTS
    return JsonResponse({'status': 0, 'context': context})


@add_context
def reranking_datasets(request, context, task_id):
    context['re_ranking_datasets'] = model.get_all_reranking_datasets_for_task(task_id)
    return JsonResponse({'status': 0, 'context': context})


@add_context
@check_permissions
def submissions_of_user(request, context, vm_id):
    try:
        context['submissions_of_user'] = model.submissions_of_user(vm_id)
        return JsonResponse({'status': 0, 'context': context})
    except:
        return JsonResponse({'status': 1})


@add_context
@check_permissions
def import_submission(request, context, task_id, vm_id, submission_type, s_id):
    try:
        model.import_submission(task_id, vm_id, submission_type, s_id)
        return JsonResponse({'status': 0, 'context': context})
    except:
        return JsonResponse({'status': 1})


@add_context
@check_permissions
@check_resources_exist('json')
def submissions_for_task(request, context, task_id, user_id, submission_type):
    context["datasets"] = model.get_datasets_by_task(task_id, return_only_names=True)
    cloned_submissions = model.cloned_submissions_of_user(user_id, task_id)
    if submission_type == "upload":
        context["all_uploadgroups"] = model.get_uploads(task_id, user_id)
        context["all_uploadgroups"] += [i for i in cloned_submissions if i['type'] == 'upload']
    elif submission_type == "docker":
        context["docker"] = {"docker_softwares": model.get_docker_softwares(task_id, user_id)}
        context["docker"]['docker_softwares'] += [i for i in cloned_submissions if i['type'] == 'docker']
        context["resources"] = settings.GIT_CI_AVAILABLE_RESOURCES
    elif submission_type == "vm":
        context["message"] = "This option is not active for this shared task. " \
                             "Please contact the organizers to enable submissions via virtual machines."

    return JsonResponse({'status': 0, "context": context})


@check_permissions
@check_resources_exist("json")
@add_context
def export_registrations(request, context, task_id):
    ret = StringIO()

    fieldnames = ['team_name', 'initial_owner', 'team_members', 'registered_on_task', 'name', 'email', 'affiliation',
                  'country', 'employment', 'participates_for', 'instructor_name', 'instructor_email', 'questions',
                  'created', 'last_modified'
                  ]

    writer = csv.DictWriter(ret, fieldnames=fieldnames)

    writer.writeheader()
    for i in model.all_registrations(task_id):
        writer.writerow(i)

    return HttpResponse(ret.getvalue())
