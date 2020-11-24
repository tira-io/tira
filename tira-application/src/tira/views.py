from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from .tira_model import FileDatabase

model = FileDatabase()


def index(request):
    context = {}
    return render(request, 'tira/index.html', context)


def task_list(request):
    context = {
        "tasks": model.tasks
    }
    return render(request, 'tira/task_list.html', context)


def dataset_list(request):
    context = {
        "datasets": model.datasets
    }
    return render(request, 'tira/dataset_list.html', context)


def dataset_detail(request, dataset_name):
    # todo - this should differ based on user authentication
    ev_keys, status, runs, evaluations = model.get_runs(dataset_name, only_public_results=False)
    ev = [f for v in evaluations.values() for f in v]
    users = [(status[user_id], runs[user_id]) for user_id in status.keys()]
    context = {
        "name": dataset_name,
        "ev_keys": ev_keys,
        "evaluations": ev,
        "users": users
    }
    return render(request, 'tira/dataset_detail.html', context)


def software_detail(request, user_id):
    # runs
    # public results
    # softwares
    # vm information

    context = {

    }
    return render(request, 'tira/software.html', context)
