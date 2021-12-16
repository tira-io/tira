import logging

from tira.authentication import auth
from tira.checks import actions_check_permissions, check_resources_exist
from tira.forms import *
from django.http import HttpResponse, JsonResponse
from http import HTTPStatus

import tira.tira_model as model


logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


@actions_check_permissions({"tira", "admin"})
def admin_reload_data(request):
    if request.method == 'GET':
        # post_id = request.GET['post_id']
        try:
            model.build_model()
            if auth.get_auth_source() == 'legacy':
                auth.load_legacy_users()
            return JsonResponse({'status': 0, 'message': "Success"}, status=HTTPStatus.OK)
        except Exception as e:
            logger.exception(f"/admin/reload_data failed with {e}", e)
            return JsonResponse({'status': 1, 'message': f"Failed with {e}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return JsonResponse({'status': 1, 'message': f"{request.method} is not allowed."}, status=HTTPStatus.FORBIDDEN)


@actions_check_permissions({"tira", "admin"})
def admin_create_vm(request):  # TODO implement
    """ Hook for create_vm posts. Responds with json objects indicating the state of the create process. """

    context = {
        "complete": [],
        'failed': []
    }
    return JsonResponse(context)

    # def parse_create_string(create_string: str):
    #     for line in create_string.split("\n"):
    #         line = line.split(",")
    #         yield line[0], line[1], line[2]
    #
    # if request.method == "POST":
    #     form = CreateVmForm(request.POST)
    #     if form.is_valid():
    #         try:
    #             bulk_create = list(parse_create_string(form.cleaned_data["bulk_create"]))
    #         except IndexError:
    #             context["create_vm_form_error"] = "Error Parsing input. Are all lines complete?"
    #             return JsonResponse(context)
    #
    #         # TODO dummy code talk to Nikolay!
    #         # TODO check semantics downstream (vm exists, host/ova does not exist)
    #         # for create_command in parse_create_string(form.cleaned_data["bulk_create"]):
    #         #     if create_vm(*create_command):
    #         #         model.add_ongoing_execution(*create_command)
    #         return bulk_vm_create(request, bulk_create)
    #     else:
    #         context["create_vm_form_error"] = "Form Invalid (check formatting)"
    #         return JsonResponse(context)
    # else:
    #     HttpResponse("Permission Denied")
    #
    # return JsonResponse(context)


@actions_check_permissions({"tira", "admin"})
def admin_archive_vm():
    return JsonResponse({'status': 1, 'message': f"Not implemented"}, status=HTTPStatus.NOT_IMPLEMENTED)


@actions_check_permissions({"tira", "admin"})
def admin_modify_vm():
    return JsonResponse({'status': 1, 'message': f"Not implemented"}, status=HTTPStatus.NOT_IMPLEMENTED)


@actions_check_permissions({"tira", "admin"})
def admin_create_task(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """

    context = {}

    if request.method == "POST":
        form = CreateTaskForm(request.POST)
        if form.is_valid():
            # sanity checks
            context["status"] = "fail"
            master_vm_id = form.cleaned_data["master_vm_id"]
            task_id = form.cleaned_data["task_id"]
            organizer = form.cleaned_data["organizer"]

            try:
                model.get_vm(master_vm_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Master VM with ID {master_vm_id} does not exist"
                return JsonResponse(context)

            try:
                model.get_task(task_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Task with ID {task_id} does not exist"
                return JsonResponse(context)

            try:
                model.get_organizer(organizer)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Task with ID {organizer} does not exist"
                return JsonResponse(context)

            if model.create_task(form.cleaned_data["task_id"], form.cleaned_data["task_name"],
                                 form.cleaned_data["task_description"], form.cleaned_data["master_vm_id"],
                                 form.cleaned_data["organizer"], form.cleaned_data["website"]):
                context["status"] = "success"
                context["created"] = {
                    "task_id": form.cleaned_data["task_id"], "task_name": form.cleaned_data["task_name"],
                    "task_description": form.cleaned_data["task_description"],
                    "master_vm_id": form.cleaned_data["master_vm_id"],
                    "organizer": form.cleaned_data["organizer"], "website": form.cleaned_data["website"]}
            else:
                context["create_task_form_error"] = f"Could not create {form.cleaned_data['task_id']}. Contact Admin."
                return JsonResponse(context)
        else:
            context["status"] = "fail"
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


@actions_check_permissions({"tira", "admin"})
def admin_add_dataset(request):
    """ Create an entry in the model for the task. Use data supplied by a model.
     Return a json status message. """

    context = {}

    if request.method == "POST":
        form = AddDatasetForm(request.POST)
        if form.is_valid():
            # TODO should be calculated from dataset_name
            dataset_id_prefix = form.cleaned_data["dataset_id_prefix"]
            dataset_name = form.cleaned_data["dataset_name"]
            master_vm_id = form.cleaned_data["master_vm_id"]
            task_id = form.cleaned_data["task_id"]
            command = form.cleaned_data["command"]
            working_directory = form.cleaned_data["working_directory"]
            measures = [line.split(',') for line in form.cleaned_data["measures"].split('\n')]

            # sanity checks
            context["status"] = "fail"
            try:
                model.get_vm(master_vm_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Master VM with ID {master_vm_id} does not exist"
                return JsonResponse(context)

            try:
                model.get_task(task_id)
            except KeyError as e:
                logger.error(e)
                context["add_dataset_form_error"] = f"Task with ID {task_id} does not exist"
                return JsonResponse(context)

            try:
                new_paths = []
                if form.cleaned_data["create_training"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "training", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "training", command,
                                        working_directory, measures)

                if form.cleaned_data["create_test"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "test", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "test", command, working_directory,
                                        measures)

                if form.cleaned_data["create_dev"]:
                    new_paths += model.add_dataset(task_id, dataset_id_prefix, "dev", dataset_name)
                    model.add_evaluator(master_vm_id, task_id, dataset_id_prefix, "dev", command, working_directory,
                                        measures)

                context["status"] = "success"
                context["created"] = {"dataset_id": dataset_id_prefix, "new_paths": new_paths}

            except KeyError as e:
                logger.error(e)
                context["create_task_form_error"] = f"Could not create {dataset_id_prefix}: {e}"
                return JsonResponse(context)
        else:
            context["create_task_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)
    else:
        HttpResponse("Permission Denied")

    return JsonResponse(context)


@actions_check_permissions({"tira", "admin"})
@check_resources_exist('json')
def admin_create_group(request, vm_id):
    """ This is the form endpoint to grant a user permissions on a vm"""
    context = {"status": 0, "message": ""}
    if request.method == "POST":
        form = AdminCreateGroupForm(request.POST)
        if form.is_valid():
            vm_id = form.cleaned_data["vm_id"]
        else:
            context["create_vm_form_error"] = "Form Invalid (check formatting)"
            return JsonResponse(context)

    vm = model.get_vm(vm_id)
    context = auth.create_group(vm)

    return JsonResponse(context)

#
# @actions_check_permissions({"tira", "admin"})
# @check_resources_exist('json')
# def admin_create_group(request, vm_id):
#     """ this is a rest endpoint to grant a user permissions on a vm"""
#     vm = model.get_vm(vm_id)
#
#     context = auth.create_group(vm)
#     return JsonResponse(context)
#
