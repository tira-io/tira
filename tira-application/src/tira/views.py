from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
import logging

from .grpc_client import GrpcClient
from .tira_model import FileDatabase
from .tira_data import get_run_runtime, get_run_file_list, get_stderr, get_stdout
from .authentication import Authentication
from .checks import Check
from .forms import *
from django.core.exceptions import PermissionDenied
from pathlib import Path
from datetime import datetime as dt

model = FileDatabase()
include_navigation = True if settings.DEPLOYMENT == "legacy" else False
auth = Authentication(authentication_source=settings.DEPLOYMENT,
                      users_file=settings.LEGACY_USER_FILE)
check = Check(model, auth)

logger = logging.getLogger("tira")
logger.info("Views: Logger active")


def index(request):
    check.has_access(request, "any")

    uid = auth.get_user_id(request)
    context = {
        "include_navigation": include_navigation,
        "tasks": model.get_tasks(),
        "user_id": uid,
        "vm_id": auth.get_vm_id(request, uid),
        "role": auth.get_role(request, user_id=uid)
    }
    return render(request, 'tira/index.html', context)


def admin(request):
    check.has_access(request, ["tira", "admin"])

    context = {
        "include_navigation": include_navigation,
        "vm_list": model.get_vm_list(),
        "host_list": model.get_host_list(),
        "ova_list": model.get_ova_list(),
        "create_vm_form": CreateVmForm(),
        "archive_vm_form": ArchiveVmForm(),
        "create_task_form": CreateTaskForm(),
        "add_dataset_form": AddDatasetForm(),
        "modify_vm_form": ModifyVmForm()
    }
    return render(request, 'tira/tira_admin.html', context)


def login(request):
    """ Hand out the login form
    Note that this is only called in legacy deployment. Disraptor is supposed to catch the route to /login
    """
    check.has_access(request, 'any')

    context = {
        "include_navigation": include_navigation,
        "role": auth.get_role(request)
    }
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
    check.has_access(request, 'any')

    auth.logout(request)
    return redirect('tira:index')


def task_detail(request, task_id):
    check.has_access(request, 'any')

    uid = auth.get_user_id(request)
    context = {
        "include_navigation": include_navigation,
        "vm_id": auth.get_vm_id(request, uid),
        "role": auth.get_role(request, uid),
        "task": model.get_task(task_id),
        "tasks": model.get_datasets_by_task(task_id)
    }
    return render(request, 'tira/task_detail.html', context)


def dataset_list(request):
    check.has_access(request, 'any')

    context = {
        "include_navigation": include_navigation,
        "role": auth.get_role(request),
        "datasets": model.get_datasets()
    }
    return render(request, 'tira/dataset_list.html', context)


def dataset_detail(request, task_id, dataset_id):
    """ The dataset view. Users, it shows only the public leaderboard right now.
    Admins, it shows all evaluations on the dataset, as well as a list of all runs and the review interface.
     @note maybe later, we can show a consolidated view of all runs the user made on this dataset below.
     """
    check.has_access(request, 'any')

    role = auth.get_role(request, auth.get_user_id(request))

    # For all users: compile the results table from the evaluations
    vm_ids = model.get_vms_by_dataset(dataset_id)
    vm_evaluations = {vm_id: model.get_vm_evaluations_by_dataset(dataset_id, vm_id,
                                                                 only_public_results=False if role == 'admin' else True)
                      for vm_id in vm_ids}
    # This enforces an order to the measures, since they differ between datasets and are rendered dynamically
    keys = set()
    for e1 in vm_evaluations.values():
        for e2 in e1.values():
            keys.update(e2.keys())
    ev_keys = list(keys)

    evaluations = [{"vm_id": vm_id,
                    "run_id": run_id,
                    "measures": [measures[k] for k in ev_keys]}
                   for vm_id, measures_by_runs in vm_evaluations.items()
                   for run_id, measures in measures_by_runs.items()]

    # If an admin views the page, we also show all runs
    vms = None
    if role == 'admin':
        vm_runs = {vm_id: model.get_vm_runs_by_dataset(dataset_id, vm_id)
                   for vm_id in vm_ids}

        vm_reviews = {vm_id: model.get_vm_reviews_by_dataset(dataset_id, vm_id)
                      for vm_id in vm_ids}

        vms = []
        for vm_id, run in vm_runs.items():
            runs = [{"run": run, "review": vm_reviews.get(vm_id, None).get(run["run_id"], None)}
                    for run in vm_runs.get(vm_id)]
            unreviewed_count = len([1 for r in vm_reviews[vm_id].values()
                                    if not r.get("reviewer", None)])
            vms.append({"vm_id": vm_id, "runs": runs, "unreviewed_count": unreviewed_count})
        # vms = [{"vm_id": vm_id,
        #         "runs": [{"run": run, "review": vm_reviews.get(vm_id, None).get(run["run_id"], None)}
        #                  for run in vm_runs.get(vm_id)],
        #         "unreviewed_count": len([1 for r in vm_reviews[vm_id].values()
        #                                  if not r.get("reviewer", None)])
        #         } for vm_id, run in vm_runs.items()]

    context = {
        "include_navigation": include_navigation,
        "role": role,
        "dataset_id": dataset_id,
        "task": model.get_task(task_id),
        "ev_keys": ev_keys,
        "evaluations": evaluations,
        "vms": vms,
    }

    return render(request, 'tira/dataset_detail.html', context)


# def software_user(request, user_id):
#     # TODO show all tasks or datasets a user participated in. -> depends on the disraptor groups
#     return redirect('tira:index')


def software_detail(request, task_id, vm_id):
    """ render the detail of the user page: vm-stats, softwares, and runs """
    check.has_access(request, ["tira", "admin", "participant", "user"], on_vm_id=vm_id)

    # 0. Early return a dummy page, if the user has no vm assigned on this task
    # TODO should be in check. If the user has no VM, check should forward to 'request-vm'.
    #   If user has no permission on the task, should forward to task page
    if auth.get_role(request, user_id=auth.get_user_id(request), vm_id=vm_id) == auth.ROLE_USER or \
            vm_id == "no-vm-assigned":
        context = {
            "include_navigation": include_navigation,
            "task": model.get_task(task_id),
            "vm_id": "no-vm-assigned",
            "role": auth.get_role(request)
        }
        return render(request, 'tira/software.html', context)
    # 2. try to load vm, # TODO if it fails return meaningful error page :D
    try:
        softwares = model.get_software(task_id, vm_id)
        runs = model.get_vm_runs_by_task(task_id, vm_id)
    except KeyError as e:
        logger.error(e)
        logger.warning(f"tried to load vm that does not exists: {vm_id} on task {task_id}")
        return redirect('tira:software-detail', task_id=task_id, vm_id="no-vm-assigned")

    # software_keys = {sw["id"] for sw in softwares}
    # run_by_software = {swk: [r for r in runs if r["software"] == swk] for swk in software_keys}
    # get all evaluations
    evals = {r["input_run_id"]: r for r in runs if "evaluator" in r["software"]}

    software = [{
        "software": sw,
        "runs": [r for r in runs if r["software"] == sw["id"]]
    } for sw in softwares]

    # print(evals)

    # TODO evaluations do not have a software_id as 'software', but 'evaluatorXYZ'
    # code that sorts the runs in a way that runs with input_run_id follow directly after their original run
    # all_run_ids = {r["run_id"] for r in runs}
    # # dependent run: these are the run where input_run_id is the run_id of another run in the batch
    # dependent_runs = {r["run_id"] for r in runs if r["input_run_id"] in all_run_ids}
    # independent_runs = all_run_ids - dependent_runs
    # r_dependent = {r["input_run_id"]: r for r in runs if r["run_id"] in dependent_runs}
    #
    # # here we assign to each software it's runs, and to each run it's dependent runs
    # for software in softwares:
    #     runs_of_current_software = run_by_software[software["id"]]
    #     r_independent = [r for r in runs_of_current_software if r["run_id"] in independent_runs]
    #
    #     for r in r_independent:
    #         if r_dependent.get(r["run_id"], None):
    #             r.get("dependent", list()).append(r_dependent[r["run_id"]])
    #     software["results"] = r_independent

    # TODO Nikolay: this sometimes just hangs infinitely. Uncommented until fixed.
    # request tira-host for vmInfo
    # vm = model.get_vm(vm_id)
    # tira_client = GrpcClient(vm.host)
    # response_vm_info = tira_client.vm_info(vm_id)

    response_vm_info = None

    print("pass")

    context = {
        "include_navigation": include_navigation,
        "task": model.get_task(task_id),
        "vm_id": vm_id,
        "software": software,
        "responseVmInfo": response_vm_info,
    }

    return render(request, 'tira/software.html', context)


def review(request, task_id, vm_id, dataset_id, run_id):
    """
     - no_errors = hasNoErrors
     - output_error -> invalid_output and has_error_output
     - software_error <-> other_error
    """
    check.has_access(request, ["tira", "admin", "participant"], on_vm_id=vm_id)
    role = auth.get_role(request, auth.get_user_id(request))

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

    context = {
        "include_navigation": include_navigation,
        'role': role,
        "review_form": ReviewForm(initial={"no_errors": run_review.get("hasNoErrors") or run_review.get("noErrors"),
                                           "output_error": run_review.get("hasErrorOutput", False)
                                                           or run_review.get("invalidOutput", False),
                                           "software_error": run_review.get("otherErrors", False),
                                           "comment": run_review.get("comment", "")}),
        "review_form_error": review_form_error,
        "task_id": task_id, "dataset_id": dataset_id, "vm_id": vm_id, "run_id": run_id,
        "run": run, "review": run_review, "runtime": runtime, "files": files,
        "stdout": stdout, "stderr": stderr,
    }

    return render(request, 'tira/review.html', context)


def users(request):
    """
    List of all users and virtual machines.
    """

    context = {
        "include_navigation": include_navigation,
        "role": auth.get_role(request),
        "users": model.get_users_vms()
    }
    return render(request, 'tira/user_list.html', context)


def user_detail(request, user_id):
    """
    User-virtual machine details and management.
    """

    role = auth.get_role(request, auth.get_user_id(request))

    # response = None
    # if role == 'admin':
    #     vm = model.get_vm_by_id(user_id)
    #     grpc_client = GrpcClient(vm.host)
    #     response = grpc_client.vm_info(vm.vmName)

    context = {
        "include_navigation": include_navigation,
        "role": role,
        "user": model.get_vm(user_id),
    }

    return render(request, 'tira/user_detail.html', context)
