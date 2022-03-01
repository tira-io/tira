from django.shortcuts import render, redirect
from django.urls import resolve
from .authentication import auth
import tira.tira_model as model
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, Http404
from http import HTTPStatus
from functools import wraps
from django.conf import settings
import logging


logger = logging.getLogger("tira")


def actions_check_permissions(roles):
    """ A decorator that checks if the requesting user has the needed role for this request.

    This decorator considers the resources requested in the func_wrapper function.
        - true if user is admin
        - if vm_id is given, this is true for participant permissions, if the user owns the vm
        - if datasets is given, this is true if the datasets is public
        - if dataset and run are given, this is true if either the run is public or the dataset is public and the run
        belongs to the user

    :@param roles: an iterable of role strings (Authentication.ROLE_ADMIN, ...)

    :returns: A JsonResponse
    :raises: django.core.exceptions.PermissionDenied
    """
    def decorator(func):
        @wraps(func)
        def func_wrapper(request, *args, **kwargs):

            if 'vm_id' in kwargs:
                role = auth.get_role(request, user_id=auth.get_user_id(request), vm_id=kwargs["vm_id"])
            else:
                role = auth.get_role(request, user_id=auth.get_user_id(request))

            if role not in roles and "any" not in roles:
                raise PermissionDenied

            return func(request, *args, **kwargs)

        return func_wrapper
    return decorator


def check_resources_exist(reply_as='json'):
    """ A decorator that checks if the resources given as parameters actually exist. """
    def decorator(func):
        @wraps(func)
        def func_wrapper(request, *args, **kwargs):

            def return_fail(message):
                if reply_as == 'json':
                    response = JsonResponse({'status': '1', 'message': message}, status=HTTPStatus.NOT_FOUND)
                    return response
                return Http404

            if "vm_id" in kwargs:
                if not model.vm_exists(kwargs["vm_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: vm_id does not exist")
                    if "task_id" in kwargs:
                        if kwargs["vm_id"] == "no-vm-assigned":
                            return redirect('tira:request_vm')
                        return redirect('tira:request_vm')
                    return return_fail("vm_id does not exist")

            if "dataset_id" in kwargs:
                if not model.dataset_exists(kwargs["dataset_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: dataset_id does not exist")
                    return return_fail("dataset_id does not exist")

            if "task_id" in kwargs:
                if not model.task_exists(kwargs["task_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: task_id does not exist")
                    return return_fail("task_id does not exist")

            if "organizer_id" in kwargs:
                if not model.organizer_exists(kwargs["organizer_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: organizer_id does not exist")
                    return return_fail("organizer_id does not exist")

            if "software_id" in kwargs:
                if "task_id" not in kwargs or "vm_id" not in kwargs:
                    raise AttributeError("Can't validate software_id: need task_id and vm_id in kwargs")
                if not model.software_exists(kwargs["task_id"], kwargs["vm_id"], kwargs["software_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: software_id does not exist")
                    return return_fail("software_id does not exist")

            if "run_id" in kwargs:
                if "dataset_id" not in kwargs or "vm_id" not in kwargs:
                    raise AttributeError("Can't validate run_id: need dataset_id and vm_id in kwargs")
                if not model.run_exists(kwargs["vm_id"], kwargs["dataset_id"], kwargs["run_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: run_id does not exist")
                    return return_fail("run_id does not exist")

            return func(request, *args, **kwargs)

        return func_wrapper
    return decorator
