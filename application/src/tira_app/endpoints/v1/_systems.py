from django.http import HttpRequest, JsonResponse
from django.urls import path


def public_submissions(request: HttpRequest) -> JsonResponse:
    ret = [
        {"team": "team-1", "name": "foo1", "type": "Docker", "tasks": ["ir-benchmarks", "reneuir"]},
        {"team": "team-1", "name": "foo2", "type": "Docker", "tasks": ["ir-benchmarks", "reneuir"]},
        {"team": "team-1", "name": "foo3", "type": "Docker", "tasks": ["ir-benchmarks", "reneuir"]},
        {"team": "team-2", "name": "foo2", "type": "Run", "tasks": ["ir-benchmarks", "reneuir"]},
        {"team": "team-3", "name": "foo2", "type": "VM", "tasks": ["ir-benchmarks", "reneuir"]},
    ]
    return JsonResponse(ret, safe=False)


endpoints = [path("", public_submissions)]
