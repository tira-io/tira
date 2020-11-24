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
    context = {
        "name": dataset_name
    }
    return render(request, 'tira/dataset_detail.html', context)


def software_detail(request):
    context = {}
    return render(request, 'tira/software.html', context)
