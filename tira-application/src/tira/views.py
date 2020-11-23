from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from .data import FileDatabase

data = FileDatabase()


def index(request):
    context = {}
    return render(request, 'tira/index.html', context)


def task_list(request):
    t = data.get_task_list()
    context = {}
    return render(request, 'tira/task_list.html', context)


def dataset_list(request):
    context = {}
    return render(request, 'tira/dataset_list.html', context)


def dataset_detail(request, dataset_name):
    context = {
        'dataset': {
            'name': dataset_name,
            'year': "2020",
        }
    }
    return render(request, 'tira/dataset_detail.html', context)


def software_detail(request):
    context = {}
    return render(request, 'tira/software.html', context)
