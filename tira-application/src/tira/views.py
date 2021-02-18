from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from itertools import groupby
from django.conf import settings
from .tira_model import FileDatabase
from .authentication import Authentication
from .forms import LoginForm
from django import forms
from django.core.exceptions import PermissionDenied

model = FileDatabase()
include_navigation = True if settings.DEPLOYMENT == "legacy" else False
auth = Authentication(authentication_source=settings.DEPLOYMENT,
                      users_file=settings.LEGACY_USER_FILE)


def index(request):
    uid = auth.get_user_id(request)
    context = {
        "include_navigation": include_navigation,
        "tasks": model.get_tasks(),
        "user_id": uid,
        "vm_id": auth.get_vm_id(request, uid),
        "role": auth.get_role(request, user_id=uid)
    }
    return render(request, 'tira/index.html', context)


def login(request):
    """ Hand out the login form
    Note that this is only called in legacy deployment. Disraptor is supposed to catch the route to /login
    """
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
    auth.logout(request)
    return redirect('tira:index')


def task_detail(request, task_id):
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
    role = auth.get_role(request, auth.get_user_id(request))

    # For all users: compile the results table from the evaluations
    vm_ids = model.get_vms_by_dataset(dataset_id)
    vm_evaluations = {vm_id: model.get_vm_evaluations_by_dataset(dataset_id, vm_id, only_public_results=False if role == 'admin' else True)
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
                      for vm_id in vm_ids}  # reviews[vm_id][run_id]

        vms = [{"vm_id": vm_id,
                "runs": [{"run": run, "review": vm_reviews.get(vm_id, None).get(run["run_id"], None)}
                         for run in vm_runs[vm_id]],
                "unreviewed_count": len([1 for r in vm_reviews[vm_id].values()
                                         if not r.get("reviewer", None)])
                } for vm_id, run in vm_runs.items()]

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
    # 0. Early return a dummy page, if the user has no vm assigned on this task
    if not vm_id or vm_id == "no-vm-assigned":
        context = {
            "include_navigation": include_navigation,
            "task": model.get_task(task_id),
            "vm_id": "no-vm-assigned",
            "role": auth.get_role(request)
        }
        return render(request, 'tira/software.html', context)

    # 1. check permissions
    role = auth.get_role(request, auth.get_user_id(request), vm_id=vm_id)

    if role == 'forbidden':
        raise PermissionDenied

    # 2. try to load vm, if it fails, the user has no vm
    try:
        softwares = model.get_software(task_id, vm_id)
        runs = model.get_vm_runs_by_task(task_id, vm_id)
    except KeyError:
        # TODO logging
        return redirect('tira:software-detail', task_id=task_id, vm_id="no-vm-assigned")


    # software_keys = {sw["id"] for sw in softwares}
    # run_by_software = {swk: [r for r in runs if r["software"] == swk] for swk in software_keys}
    # get all evaluations
    evals = {r["input_run_id"]: r for r in runs if "evaluator" in r["software"]}

    software = [{
        "software": sw,
        "runs": [r for r in runs if r["software"] == sw["id"]]
    } for sw in softwares]

    print(evals)

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

    context = {
        "include_navigation": include_navigation,
        "task": model.get_task(task_id),
        "vm_id": vm_id,
        "software": software
    }

    return render(request, 'tira/software.html', context)


def review(request, task_id, vm_id, dataset_id, run_id):
    # permissions
    role = auth.get_role(request, auth.get_user_id(request), vm_id=vm_id)
    if role == 'forbidden':
        raise PermissionDenied

    run_review = model.get_run_review(dataset_id, vm_id, run_id)
    context = {
        "include_navigation": include_navigation,
        "task_id": task_id,
        "vm_id": vm_id,
        "run_id": run_id,
        "review": run_review
    }

    return render(request, 'tira/review.html', context)

# {"reviewer": review.reviewerId, "noErrors": review.noErrors, "missingOutput": review.missingOutput,
# "extraneousOutput": review.extraneousOutput, "invalidOutput": review.invalidOutput,
# "hasErrorOutput": review.hasErrorOutput, "otherErrors": review.otherErrors,
# "comment": review.comment, "hasErrors": review.hasErrors, "hasWarnings": review.hasWarnings,
# "hasNoErrors": review.hasNoErrors, "published": review.published, "blinded": review.blinded
# }


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

    vms = None
    if role == 'admin':
        vm_runs = {vm_id: model.get_vm_runs_by_dataset(user_id, vm_id)
                   for vm_id in vm_ids}

        vm_reviews = {vm_id: model.get_vm_reviews_by_dataset(user_id, vm_id)
                      for vm_id in vm_ids}  # reviews[vm_id][run_id]

        vms = [{"vm_id": vm_id,
                "runs": [{"run": run, "review": vm_reviews.get(vm_id, None).get(run["run_id"], None)}
                         for run in vm_runs[vm_id]],
                "unreviewed_count": len([1 for r in vm_reviews[vm_id].values()
                                         if not r.get("reviewer", None)])
                } for vm_id, run in vm_runs.items()]

    context = {
        "include_navigation": include_navigation,
        "role": role,
        "user_id": user_id,
    }

    return render(request, 'tira/user_detail.html', context)
