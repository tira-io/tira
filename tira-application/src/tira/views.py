from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from itertools import groupby
from django.conf import settings
from .tira_model import FileDatabase
from .authentication import Authentication
from .forms import LoginForm
from django import forms

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
        "datasets": model.datasets
    }
    return render(request, 'tira/dataset_list.html', context)


def dataset_detail(request, task_id, dataset_id):
    # todo - this should differ based on user authentication
    ev_keys, status, runs, evaluations = model.get_dataset_runs(dataset_id, only_public_results=False)
    ev = [f for v in evaluations.values() for f in v]
    users = [(status[user_id], runs[user_id]) for user_id in status.keys()]
    print(model.get_task(task_id))
    context = {
        "include_navigation": include_navigation,
        "role": auth.get_role(request, auth.get_user_id(request)),
        "dataset_id": dataset_id,
        "task": model.get_task(task_id),
        "ev_keys": ev_keys,
        "evaluations": ev,
        "users": users
    }
    return render(request, 'tira/dataset_detail.html', context)


# def software_user(request, user_id):
#     # TODO show all tasks or datasets a user participated in. -> depends on the disraptor groups
#     return redirect('tira:index')


def software_detail(request, task_id, vm_id):
    """ render the detail of the user page: vm-stats, softwares, and runs
    TODO handle ROLE_USER/ROLE_ADMIN
    TODO handle ROLE_GUEST and "no-vm-assigned"
    """
    if not vm_id or vm_id == "no-vm-assigned":
        context = {
            "include_navigation": include_navigation,
            "task": model.get_task(task_id),
            "role": auth.get_role(request)
        }
        return render(request, 'tira/login.html', context)

    softwares = model.softwares_by_user[vm_id]  # [{id, count, command, working_directory, dataset, run, creation_date, last_edit}]

    # softwares have the same id for different tasks
    # clarify softwares by fixing them to datasets: software1-dataset_id
    for software in softwares:
        software["name"] = f"{software['id']}-{software['dataset']}"

    runs = model.get_user_runs(vm_id)  # [{software, run_id, input_run_id, size, lines, files, dirs, dataset, review: {}}]

    run_by_software = {sw["id"]: [r for r in runs if r["software"] == sw["id"]]
                       for sw in softwares}
    all_run_ids = {r["run_id"] for r in runs}
    # dependent run: these are the run where input_run_id is the run_id of another run in the batch
    dependent_runs = {r["run_id"] for r in runs if r["input_run_id"] in all_run_ids}
    independent_runs = all_run_ids - dependent_runs
    r_dependent = {r["input_run_id"]: r for r in runs if r["run_id"] in dependent_runs}

    # here we assign to each software it's runs, and to each run it's dependent runs
    for software in softwares:
        runs_of_current_software = run_by_software[software["id"]]
        r_independent = [r for r in runs_of_current_software if r["run_id"] in independent_runs]

        for r in r_independent:
            if r_dependent.get(r["run_id"], None):
                r.get("dependent", list()).append(r_dependent[r["run_id"]])
        software["results"] = r_independent

    context = {
        "include_navigation": include_navigation,
        "task": model.get_task(task_id),
        "user_id": vm_id,
        "softwares": softwares
    }

    return render(request, 'tira/software.html', context)
