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

    # For all users: compile the results table from the evaluations
    vm_ids = model.get_vms_by_dataset(dataset_id)
    # This enforces an order to the measures, since they differ between datasets and are rendered dynamically
    vm_reviews = {vm_id: model.get_vm_reviews_by_dataset(dataset_id, vm_id) for vm_id in vm_ids}

    # If an admin views the page, we also show all runs
    vms = model.get_vms_with_reviews(vm_ids, dataset_id, vm_reviews) if role == "admin" else None
    ev_keys, evaluations = model.get_evaluations_with_keys_by_dataset(vm_ids, dataset_id,
                                                                      vm_reviews if role == "admin" else None)

    context["dataset_id"] = dataset_id
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
    softwares = model.get_software_by_task(task_id, vm_id)
    runs = model.get_vm_runs_by_task(task_id, vm_id)
    datasets = model.get_datasets_by_task(task_id)

    # Construct a dictionary that has the software as a key and as value a list of runs with that software
    # Note that we order the list in such a way, that evaluations of a run are right behind that run in the list
    #   (based on the input_run)
    runs_with_input = {}  # get the runs which have an input_run_id
    for r in runs:
        # if we loop once, might as well get the review-info here.
        r['review'] = model.get_run_review(r.get("dataset"), vm_id, r.get("run_id"))
        if r.get("input_run_id") == 'none':
            continue
        runs_with_input.setdefault(r.get("input_run_id"), []).append(r)

    runs_without_input = [r for r in runs if r.get("input_run_id") == "none"]
    runs_by_software = {}
    for r in runs_without_input:
        runs_by_software.setdefault(r.get("software"), []).append(r)
        runs_by_software.setdefault(r.get("software"), []).extend(runs_with_input.pop(r.get("run_id"), []))

    for k, v in runs_with_input.items():  # left-over runs_with_input, where the input-run does not exist anymore
        for r in v:
            runs_by_software.setdefault(r.get("software"), []).append(r)

    software = [{
        "software": sw,
        "runs": runs_by_software.get(sw["id"])
    } for sw in softwares]

    vm = model.get_vm(vm_id)

    context["task"] = model.get_task(task_id)
    context["vm_id"] = vm_id
    context["vm"] = {"host": vm.host, "user": vm.userName, "password": vm.userPw, "ssh": vm.portSsh, "rdp": vm.portRdp}
    context["software"] = software
    context["datasets"] = datasets

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


def _zip_dir(path):
    if os.path.isdir(path):
        zip_handle = zipfile.ZipFile(path.with_suffix(".zip"), "w")
        for root, dirs, files in os.walk(path):
            for file in files:
                zip_handle.write(os.path.join(root, file),
                                 os.path.relpath(os.path.join(root, file),
                                                 os.path.join(path, '..')
                                                 )
                                 )
        zip_handle.close()

        zip_path = path.with_suffix(".zip")
        return zip_path
    else:
        return None


@actions_check_permissions({"tira", "admin"})
@check_resources_exist('json')
def download_rundir(request, task_id, dataset_id, vm_id, run_id):
    path = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id
    zip_handle = zipfile.ZipFile(path.with_suffix(".zip"), "w")
    for root, dirs, files in os.walk(path):
        for file in files:
            zip_handle.write(os.path.join(root, file),
                             os.path.relpath(os.path.join(root, file),
                                             os.path.join(path, '..')
                                             )
                             )
    zip_handle.close()

    zip_path = path.with_suffix(".zip")
    if os.path.exists(zip_path):
        response = FileResponse(open(zip_path, "rb"), as_attachment=True,
                                filename=run_id + "-" + os.path.basename(zip_path))
        os.remove(zip_path)
        return response
    else:
        return JsonResponse({'status': 'Failed', 'reason': f'File does not exist: {zip_path}'},
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