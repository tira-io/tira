from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.conf import settings
import logging

import tira.tira_model as model
from .tira_data import get_run_runtime, get_run_file_list, get_stderr, get_stdout, get_tira_log
from .authentication import auth
from .checks import actions_check_permissions, check_resources_exist
from .forms import *
from pathlib import Path
from datetime import datetime as dt
import os
import zipfile
from http import HTTPStatus

logger = logging.getLogger("tira")
logger.info("Views: Logger active")


def add_context(func):
    def func_wrapper(request, *args, **kwargs):
        uid = auth.get_user_id(request)
        context = {
            "include_navigation": True if settings.DEPLOYMENT == "legacy" else False,
            "user_id": uid,
            "role": auth.get_role(request, user_id=uid)
        }
        return func(request, context, *args, **kwargs, )

    return func_wrapper


@actions_check_permissions({"any"})
@add_context
def index(request, context):
    context["tasks"] = model.get_tasks()
    context["vm_id"] = auth.get_vm_id(request, context["user_id"])
    return render(request, 'tira/index.html', context)


@actions_check_permissions({"tira", "admin"})
@add_context
def admin(request, context):
    context["vm_list"] = model.get_vm_list()
    context["host_list"] = model.get_host_list()
    context["ova_list"] = model.get_ova_list()
    context["create_vm_form"] = CreateVmForm()
    context["archive_vm_form"] = ArchiveVmForm()
    context["create_task_form"] = CreateTaskForm()
    context["add_dataset_form"] = AddDatasetForm()
    context["create_group_form"] = AdminCreateGroupForm()
    context["modify_vm_form"] = ModifyVmForm()
    return render(request, 'tira/tira_admin.html', context)


@actions_check_permissions({"any"})
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


@actions_check_permissions({"any"})
def logout(request):
    auth.logout(request)
    return redirect('tira:index')


@actions_check_permissions({"any"})
@check_resources_exist('http')
@add_context
def task_detail(request, context, task_id):
    context["vm_id"] = auth.get_vm_id(request, context["user_id"])
    context["task"] = model.get_task(task_id)
    context["datasets"] = model.get_datasets_by_task(task_id)

    return render(request, 'tira/task_detail.html', context)


@actions_check_permissions({"any"})
@add_context
def dataset_list(request, context):
    context["datasets"] = model.get_datasets()

    return render(request, 'tira/dataset_list.html', context)


@actions_check_permissions({"any"})
@check_resources_exist('http')
@add_context
def dataset_detail(request, context, task_id, dataset_id):
    """ The dataset view. Users, it shows only the public leaderboard right now.
    Admins, it shows all evaluations on the dataset, as well as a list of all runs and the review interface.

     @note maybe later, we can show a consolidated view of all runs the user made on this dataset below.
     """
    role = context["role"]
    vms = model.get_vms_with_reviews(dataset_id) if role == "admin" else None
    ev_keys, evaluations = model.get_evaluations_with_keys_by_dataset(dataset_id, True if role == "admin" else None)

    context["dataset_id"] = dataset_id
    context["datasets"] = model.get_datasets_by_task(task_id)
    context["task"] = model.get_task(task_id)
    context["ev_keys"] = ev_keys
    context["evaluations"] = evaluations
    context["vm_id"] = auth.get_vm_id(request, context["user_id"])
    context["vms"] = vms

    return render(request, 'tira/dataset_detail.html', context)


@actions_check_permissions({"tira", "admin", "participant", "user"})
@check_resources_exist('http')
@add_context
def software_detail(request, context, task_id, vm_id):
    """ render the detail of the user page: vm-stats, softwares, and runs """

    software = model.get_software_with_runs(task_id, vm_id)

    context["task"] = model.get_task(task_id)
    context["vm_id"] = vm_id
    context["vm"] = model.get_vm(vm_id)
    context["software"] = software
    context["datasets"] = model.get_datasets_by_task(task_id)

    return render(request, 'tira/software.html', context)


@actions_check_permissions({"tira", "admin", "participant"})
@check_resources_exist('http')
@add_context
def review(request, context, task_id, vm_id, dataset_id, run_id):
    """
     - no_errors = hasNoErrors
     - output_error -> invalid_output and has_error_output
     - software_error <-> other_error
    """
    role = context["role"]

    review_form_error = None

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            no_errors = form.cleaned_data["no_errors"]
            output_error = form.cleaned_data["output_error"]
            software_error = form.cleaned_data["software_error"]
            comment = form.cleaned_data["comment"]

            try:
                if no_errors and (output_error or software_error):
                    review_form_error = "Either there is an error or there is not."

                username = auth.get_user_id(request)
                has_errors = output_error or software_error
                has_no_errors = (not has_errors)

                s = model.update_review(dataset_id, vm_id, run_id, username, str(dt.utcnow()),
                                        has_errors, has_no_errors, no_errors=no_errors,
                                        invalid_output=output_error,
                                        has_error_output=output_error, other_errors=software_error, comment=comment
                                        )
                if not s:
                    review_form_error = "Failed saving review. Contact Admin."
            except KeyError as e:
                logger.error(f"Failed updating review {task_id}, {vm_id}, {dataset_id}, {run_id} with {e}")
                review_form_error = "Failed updating review. Contact Admin."
        else:
            review_form_error = "Form Invalid (check formatting)"

    run = model.get_run(dataset_id, vm_id, run_id)
    run_review = model.get_run_review(dataset_id, vm_id, run_id)
    runtime = get_run_runtime(dataset_id, vm_id, run_id)
    files = get_run_file_list(dataset_id, vm_id, run_id)
    files["file_list"][0] = "$outputDir"
    stdout = get_stdout(dataset_id, vm_id, run_id)
    stderr = get_stderr(dataset_id, vm_id, run_id)
    tira_log = get_tira_log(dataset_id, vm_id, run_id)

    context["review_form"] = ReviewForm(
        initial={"no_errors": run_review.get("hasNoErrors") or run_review.get("noErrors"),
                 "output_error": run_review.get("hasErrorOutput", False) or run_review.get("invalidOutput", False),
                 "software_error": run_review.get("otherErrors", False),
                 "comment": run_review.get("comment", "")})
    context["review_form_error"] = review_form_error
    context["task_id"] = task_id
    context["dataset_id"] = dataset_id
    context["is_confidential"] = model.get_dataset(dataset_id).get('is_confidential', True)
    context["vm_id"] = vm_id
    context["run_id"] = run_id
    context["run"] = run
    context["review"] = run_review
    context["runtime"] = runtime
    context["files"] = files
    context["stdout"] = stdout
    context["stderr"] = stderr
    context["tira_log"] = tira_log

    return render(request, 'tira/review.html', context)


@actions_check_permissions({"tira", "admin"})
@check_resources_exist('json')
def download_rundir(request, task_id, dataset_id, vm_id, run_id):
    """ Zip the given run and hand it out for download. Deletes the zip on the server again. """
    path_to_be_zipped = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id
    zipped = Path(f"{path_to_be_zipped.stem}.zip")
    with zipfile.ZipFile(zipped, "w") as zipf:
        for f in path_to_be_zipped.rglob('*'):
            zipf.write(f, arcname=f.relative_to(path_to_be_zipped.parent))

    if zipped.exists():
        response = FileResponse(open(zipped, "rb"), as_attachment=True, filename=f"{run_id}-{zipped.stem}.zip")
        os.remove(zipped)
        return response
    else:
        return JsonResponse({'status': 1, 'reason': f'File does not exist: {zipped}'},
                            status=HTTPStatus.INTERNAL_SERVER_ERROR)


@actions_check_permissions({"tira", "admin"})
@add_context
def users(request, context):
    """
    List of all users and virtual machines.
    """
    context["users"] = model.get_users_vms()
    return render(request, 'tira/user_list.html', context)


@actions_check_permissions({"tira", "admin"})
@add_context
def user_detail(request, context, user_id):
    """
    User-virtual machine details and management.
    """
    context["user"] = model.get_vm(user_id)
    return render(request, 'tira/user_detail.html', context)


@actions_check_permissions({"tira", "admin"})
@add_context
def request_vm(request, context):
    return render(request, 'tira/request_vm.html', context)
