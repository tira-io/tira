from django.http import HttpRequest, JsonResponse
from django.urls import path

from ...model import DockerSoftware
from ...tira_model import model


def public_submissions(request: HttpRequest) -> JsonResponse:
    all_runs = model.all_runs()
    ret = []

    for vm in all_runs:
        for title in all_runs[vm]:
            blinded = True
            public = False
            run_type = []
            tasks = set()
            for run in all_runs[vm][title].values():
                run_type += [run["type"]]
                blinded = run["blinded"] and blinded
                public = run["published"] or public
                tasks.add(str(run["task"]))

            if public:
                ret += [{"team": vm, "name": title, "type": run_type[0], "tasks": sorted([i for i in tasks])}]

    return JsonResponse(ret, safe=False)


def software_details(request: HttpRequest, user_id: str, software: str) -> JsonResponse:
    ret = []
    for i in DockerSoftware.objects.filter(vm_id=user_id, display_name=software):
        if not i.public_image_name:
            continue
        ret += [{"PublicDockerImage": i.public_image_name, "Command": i.command}]

    return JsonResponse({"DockerImage": "dasda", "tbd": ret}, safe=False)


endpoints = [path("", public_submissions), path("<str:user_id>/<str:software>", software_details)]
