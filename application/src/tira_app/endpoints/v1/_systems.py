import json
from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponseNotFound, JsonResponse
from django.urls import path

from ...model import DockerSoftware, Run, Upload
from ...tira_model import model

if TYPE_CHECKING:
    from typing import Any


def public_submissions(request: "HttpRequest") -> JsonResponse:
    all_runs = model.all_runs()
    all_run_formats = model.all_run_formats()
    ret = []

    for vm in all_runs:
        for title in all_runs[vm]:
            blinded = True
            public = False
            run_type = []
            tasks = set()
            valid_executions = None
            for run in all_runs[vm][title].values():
                run_type += [run["type"]]
                blinded = run["blinded"] and blinded
                public = run["published"] or public
                tasks.add(str(run["task"]))
                if run["software-id"] in all_run_formats[run["type"]]:
                    valid_executions = all_run_formats[run["type"]][run["software-id"]]

            if public:
                tmp = {"team": vm, "name": title, "type": run_type[0], "tasks": sorted([i for i in tasks])}
                if valid_executions:
                    tmp["verified_outputs"] = valid_executions
                ret += [tmp]

    return JsonResponse(ret, safe=False)


def serialize_docker_software(ds: "DockerSoftware") -> "dict[str, Any]":
    input_docker_software = []

    if ds and ds.input_docker_software:
        input_docker_software.append(serialize_docker_software(ds.input_docker_software))
        for i in model.get_ordered_additional_input_runs_of_software({"docker_software_id": ds.docker_software_id}):
            matches = DockerSoftware.objects.filter(docker_software_id=i)
            assert len(matches) == 1
            for ds_inp in matches:
                input_docker_software.append(serialize_docker_software(ds_inp))
    vm = ds.vm
    task = ds.task

    return {
        "public_image_name": ds.public_image_name,
        "command": ds.command,
        "display_name": ds.display_name,
        "deleted": ds.deleted,
        "description": ds.description,
        "paper_link": ds.paper_link,
        "ir_re_ranker": ds.ir_re_ranker,
        "ir_re_ranking_input": ds.ir_re_ranking_input,
        "team": vm.vm_id if vm else None,
        "task": task.task_id if task else None,
        "docker_software_id": ds.docker_software_id,
        "input_docker_software": input_docker_software,
    }


def software_details(request: "HttpRequest", user_id: str, software: str) -> JsonResponse:
    ret: list[dict[str, Any]] = []
    for i in DockerSoftware.objects.filter(vm_id=user_id, display_name=software):
        if not i.public_image_name or i.deleted:
            continue
        ret.append(serialize_docker_software(i))

    if len(ret) == 0:
        for i in Upload.objects.filter(vm_id=user_id, display_name=software):
            for run in Run.objects.select_related("review").filter(upload=i):
                if run.review.published and not run.review.blinded:
                    ret = [{"foo": "1212"}]

    if len(ret) == 1:
        return JsonResponse(ret[0], safe=False)
    else:
        return HttpResponseNotFound(
            json.dumps({"status": 1, "message": f"Could not find a software '{software}' by user '{user_id}'."})
        )


endpoints = [
    path("", public_submissions),
    path("all", public_submissions),
    path("<str:user_id>/<str:software>", software_details),
]
