from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder
import logging

import tira.tira_model as model
from .tira_data import get_run_runtime, get_run_file_list, get_stderr, get_stdout, get_tira_log
from .authentication import auth
from .checks import check_permissions, check_resources_exist, check_conditional_permissions
from .forms import *
from pathlib import Path
from datetime import datetime as dt
import os
import zipfile
import json
from http import HTTPStatus

logger = logging.getLogger("tira")
logger.info("Views: Logger active")


def add_context(func):
    def func_wrapper(request, *args, **kwargs):
        uid = auth.get_user_id(request)
        vm_id = None

        if args and 'vm_id' in args:
            vm_id = args['vm_id']
        elif kwargs and 'vm_id' in kwargs:
            vm_id = kwargs['vm_id']

        context = {
            "include_navigation": True if settings.DEPLOYMENT == "legacy" else False,
            "user_id": uid,
            "role": auth.get_role(request, user_id=uid, vm_id=vm_id),
            "organizer_teams": mark_safe(json.dumps(auth.get_organizer_ids(request)))
        }
        return func(request, context, *args, **kwargs, )

    return func_wrapper


@add_context
def index(request, context):
    context["tasks"] = model.get_tasks(include_dataset_stats=True)
    context["organizer_teams"] = auth.get_organizer_ids(request)
    context["vm_ids"] = auth.get_vm_ids(request, None)
    
    
    if context["role"] != auth.ROLE_GUEST:
        context["vm_id"] = auth.get_vm_id(request, context["user_id"])

    return render(request, 'tira/index.html', context)


@check_permissions
@add_context
def background_jobs(request, context, task_id, job_id):
    context['task'] = task_id
    context['job'] = model.get_job_details(task_id, None, job_id)

    return render(request, 'tira/background_jobs.html', context)


@add_context
def veutify_page(request, context, **kwargs):
    return render(request, 'tira/veutify_page.html', context)


@add_context
def login(request, context):
    """ Hand out the login form 
    Note that this is only called in legacy deployment. Disraptor is supposed to catch the route to /login
    """

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            # read form data, do auth.login(request, user_id, password)
            valid = auth.login(request, user_id=form.cleaned_data["user_id"], password=form.cleaned_data["password"])
            if valid:
                return redirect('tira:index')
            else:
                context["form_error"] = "Login Invalid"
    else:
        form = LoginForm()

    context["form"] = form
    return render(request, 'tira/login.html', context)


def logout(request):
    auth.logout(request)
    return redirect('tira:index')


def _add_task_to_context(context, task_id, dataset_id):
    datasets = model.get_datasets_by_task(task_id)

    context["datasets"] = json.dumps({ds['dataset_id']: ds for ds in datasets}, cls=DjangoJSONEncoder)
    context['selected_dataset_id'] = dataset_id
    context['test_dataset_ids'] = json.dumps([ds['dataset_id'] for ds in datasets if ds['is_confidential']],
                                            cls=DjangoJSONEncoder)
    context['training_dataset_ids'] = json.dumps([ds['dataset_id'] for ds in datasets if not ds['is_confidential']],
                                                cls=DjangoJSONEncoder)
    task = model.get_task(task_id)
    context["task_id"] = task['task_id']
    context["task_name"] = json.dumps(task['task_name'], cls=DjangoJSONEncoder)
    context["organizer"] = json.dumps(task['organizer'], cls=DjangoJSONEncoder)
    context["task_description"] = json.dumps(task['task_description'], cls=DjangoJSONEncoder)
    context["web"] = json.dumps(task['web'], cls=DjangoJSONEncoder)


def _add_user_vms_to_context(request, context, task_id, include_docker_details=True):
    if context["role"] != auth.ROLE_GUEST:
        allowed_vms_for_task = model.all_allowed_task_teams(task_id)
        vm_id = auth.get_vm_id(request, context["user_id"])
        vm_ids = []
    
        if allowed_vms_for_task is None or vm_id in allowed_vms_for_task:
            context["vm_id"] = vm_id
        
        if getattr(auth, "get_vm_ids", None):
            vm_ids = [i for i in auth.get_vm_ids(request, context["user_id"]) if allowed_vms_for_task is None or i in allowed_vms_for_task]
        
        context['user_vms_for_task'] = vm_ids

        docker = ['Your account has no docker registry. Please contact an organizer.']

        if include_docker_details and len(vm_ids) > 0:
            docker = model.load_docker_data(task_id, vm_ids[0], cache, force_cache_refresh=False)

            if not docker:
                docker = ['Docker is not enabled for this task.']
            else:
                docker = docker['docker_software_help'].split('\n')
                docker = [i for i in docker if 'docker login' in i or 'docker push' in i or 'docker build -t' in i]
                docker = [i.replace('/my-software:0.0.1', '/<YOUR-IMAGE-NAME>').replace('<code>', '').replace('</code>', '').replace('<p>', '').replace('</p>', '') for i in docker]
                docker = [i if 'docker build -t' not in i else 'docker tag <YOUR-IMAGE-NAME> ' + i.split('docker build -t')[-1].split(' -f ')[0].strip() for i in docker]

        context['docker_documentation'] = docker


def zip_run(dataset_id, vm_id, run_id):
    """ Zip the given run and hand it out for download. Deletes the zip on the server again. """
    path_to_be_zipped = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id
    zipped = Path(f"{path_to_be_zipped.stem}.zip")

    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in path_to_be_zipped.rglob('*'):
            zipf.write(f, arcname=f.relative_to(path_to_be_zipped.parent))

    return zipped

def zip_runs(vm_id, dataset_ids_and_run_ids, name):
    """ Zip the given run and hand it out for download. Deletes the zip on the server again. """
    
    zipped = Path(f"{path_to_be_zipped.stem}.zip")

    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_DEFLATED) as zipf:
        for dataset_id, run_id in dataset_ids_and_run_ids:
            path_to_be_zipped = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id
            for f in path_to_be_zipped.rglob('*'):
                zipf.write(f, arcname=f.relative_to(path_to_be_zipped.parent))

    return zipped

@check_conditional_permissions(public_data_ok=True)
@check_resources_exist('json')
def download_rundir(request, task_id, dataset_id, vm_id, run_id):
    """ Zip the given run and hand it out for download. Deletes the zip on the server again. """
    zipped = zip_run(dataset_id, vm_id, run_id)

    if zipped.exists():
        response = FileResponse(open(zipped, "rb"), as_attachment=True, filename=f"{run_id}-{zipped.stem}.zip")
        os.remove(zipped)
        return response
    else:
        return JsonResponse({'status': 1, 'reason': f'File does not exist: {zipped}'},
                            status=HTTPStatus.INTERNAL_SERVER_ERROR)


@check_conditional_permissions(public_data_ok=True)
@check_resources_exist('json')
def download_input_rundir(request, task_id, dataset_id, vm_id, run_id):
    return download_rundir(request, task_id, dataset_id, vm_id, input_run_id)

@check_permissions
def download_datadir(request, dataset_type, input_type, dataset_id):
    input_type = input_type.lower().replace('input', '')
    input_type = '' if len(input_type) < 2 else input_type
    task_id = model.get_dataset(dataset_id)['task']

    path = model.model.data_path / f'{dataset_type}-datasets{input_type}' / task_id / dataset_id

    if not path.exists():
        return JsonResponse({'status': 1, 'reason': f'File does not exist: {path}'},
                            status=HTTPStatus.INTERNAL_SERVER_ERROR)

    zipped = Path(f"{path.stem}.zip")
    with zipfile.ZipFile(zipped, "w") as zipf:
        for f in path.rglob('*'):
            zipf.write(f, arcname=f.relative_to(path.parent))

    if zipped.exists():
        response = FileResponse(open(zipped, "rb"), as_attachment=True, filename=f"{dataset_id}-{dataset_type}{input_type}.zip")
        os.remove(zipped)
        return response

