from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from itertools import groupby
from django.conf import settings
from .tira_model import FileDatabase
from .authentication import Authentication

model = FileDatabase()
include_navigation = True if settings.DEPLOYMENT == "standalone" else False
auth = Authentication(authentication_source=settings.DEPLOYMENT,
                      tira_root=settings.TIRA_ROOT)


def index(request):

    context = {
        "include_navigation": include_navigation,
        "tasks": model.get_tasks(),
        "user_id": auth.get_user_id(request),
        "group_id": auth.get_user_groups(request),
        "auth": auth.get_role(request)
    }
    return render(request, 'tira/index.html', context)


def authentication(request):
    return redirect('https://disraptor.tira.io/authentication')


def task_list(request):
    return redirect('tira:index')


def task_detail(request, task_id):
    context = {
        "include_navigation": include_navigation,
        "task_id": task_id,
        "tasks": model.get_datasets_by_task(task_id)
    }
    return render(request, 'tira/task_detail.html', context)


def dataset_list(request):
    context = {
        "include_navigation": include_navigation,
        "datasets": model.datasets
    }
    return render(request, 'tira/dataset_list.html', context)


def dataset_detail(request, dataset_id):
    # todo - this should differ based on user authentication
    ev_keys, status, runs, evaluations = model.get_dataset_runs(dataset_id, only_public_results=False)
    ev = [f for v in evaluations.values() for f in v]
    users = [(status[user_id], runs[user_id]) for user_id in status.keys()]
    context = {
        "include_navigation": settings.DEPLOYMENT,
        "name": dataset_id,
        "ev_keys": ev_keys,
        "evaluations": ev,
        "users": users
    }
    return render(request, 'tira/dataset_detail.html', context)


def software_user(request, user_id):
    # TODO show all tasks or datasets a user participated in. -> depends on the disraptor groups
    return redirect('tira:index')


def software_detail(request, task_id, user_id):
    """ render the detail of the user page: vm-stats, softwares, and runs """
    if not user_id:
        context = {
            "include_navigation": include_navigation,
        }
        return render(request, 'tira/login.html', context)

    softwares = model.softwares_by_user[user_id]  # [{id, count, command, working_directory, dataset, run, creation_date, last_edit}]

    # softwares have the same id for different tasks
    # clarify softwares by fixing them to datasets: software1-dataset_id
    for software in softwares:
        software["name"] = f"{software['id']}-{software['dataset']}"

    runs = model.get_user_runs(user_id)  # [{software, run_id, input_run_id, size, lines, files, dirs, dataset, review: {}}]

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
        "include_navigation": True if settings.DEPLOYMENT == "standalone" else False,
        "user_id": user_id,
        "softwares": softwares
    }

    return render(request, 'tira/software.html', context)
