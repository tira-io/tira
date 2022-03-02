from django.shortcuts import render, redirect
from django.urls import resolve
from .authentication import auth
import tira.tira_model as model
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, Http404, HttpResponseNotAllowed
from http import HTTPStatus
from functools import wraps
from django.conf import settings
import logging


logger = logging.getLogger("tira")


def check_permissions(func):
    """ A decorator that checks if the requesting user has the needed permissions to call the decorated function.
    This decorator redirects or blocks requests if the requesting user does not have permission.
    This decorator considers the resources requested in the decorated function:
        - vm_id: returns the permissions the requesting user has on the vm
        - run_id: in addition to vm_id, checks if the requesting user can see the run. By default, permission is denied
        if the run is not visible.

    :raises: django.core.exceptions.PermissionDenied
    """
    @wraps(func)
    def func_wrapper(request, *args, **kwargs):
        if kwargs.get('vm_id', None):
            role = auth.get_role(request, user_id=auth.get_user_id(request), vm_id=kwargs["vm_id"])

            if kwargs.get('run_id', None) and kwargs.get('dataset_id', None):
                if not model.run_exists(kwargs["vm_id"], kwargs["dataset_id"], kwargs["run_id"]):
                    return Http404(f'The VM {kwargs["vm_id"]} has no run with the id {kwargs["run_id"]} on {kwargs["dataset_id"]}.')
                review = model.get_run_review(kwargs["dataset_id"], kwargs["vm_id"], kwargs["run_id"])
                is_review_visible = (not review['blinded']) or review['published']
                if not is_review_visible:
                    role = auth.ROLE_USER
        else:
            role = auth.get_role(request, user_id=auth.get_user_id(request))

        if role == auth.ROLE_ADMIN or role == auth.ROLE_TIRA or role == auth.ROLE_PARTICIPANT:
            return func(request, *args, **kwargs)
        elif role == auth.ROLE_GUEST:  # If guests access a restricted resource, we send them to login
            return redirect('tira:login')

        return HttpResponseNotAllowed(f"Access forbidden.")

    return func_wrapper


def check_conditional_permissions(restricted=False, public_data_ok=False, private_run_ok=False):
    """ A decorator that checks if the requesting user has the needed permissions to call the decorated function.
    This decorator redirects or blocks requests if the requesting user does not have permission.
    This decorator considers the resources requested in the decorated function:
        - vm_id: returns the permissions the requesting user has on the vm
        - run_id: in addition to vm_id, checks if the requesting user can see the run. By default, permission is denied
        if the run is not visible.

    :param restricted: if True, only admins can ever access the decorated function
    :param public_data_ok: if True and if a run is requested, return with permissions if the user owns the VM and the
        dataset is public, even if the run is blinded and not published
    :param private_run_ok: if True, and if a run is requested, return with permissions even if the run is blinded

    :raises: django.core.exceptions.PermissionDenied
    """
    def decorator(func):
        @wraps(func)
        def func_wrapper(request, *args, **kwargs):
            if kwargs.get('vm_id', None):
                role = auth.get_role(request, user_id=auth.get_user_id(request), vm_id=kwargs["vm_id"])

                if kwargs.get('run_id', None) and kwargs.get('dataset_id', None):
                    if not model.run_exists(kwargs["vm_id"], kwargs["dataset_id"], kwargs["run_id"]):
                        return Http404(f'The VM {kwargs["vm_id"]} has no run with the id {kwargs["run_id"]} on {kwargs["dataset_id"]}.')
                    review = model.get_run_review(kwargs["dataset_id"], kwargs["vm_id"], kwargs["run_id"])
                    is_review_visible = (not review['blinded']) or review['published']
                    is_dataset_confidential = model.get_dataset(kwargs["dataset_id"])['is_confidential']

                    # demote role to USER if the run is not visible and we make no exception for public datasets
                    if role not in {auth.ROLE_ADMIN, auth.ROLE_TIRA} and \
                            not is_review_visible and \
                            not (public_data_ok and not is_dataset_confidential):
                        role = auth.ROLE_USER
                    # demote role to USER if the run is not visible and we make no exception
                    elif role not in {auth.ROLE_ADMIN, auth.ROLE_TIRA} and not is_review_visible and not private_run_ok:
                        role = auth.ROLE_USER
            else:
                role = auth.get_role(request, user_id=auth.get_user_id(request))
            if role == auth.ROLE_ADMIN or role == auth.ROLE_TIRA:  # Admins can access and do everything
                return func(request, *args, **kwargs)
            if restricted:
                return HttpResponseNotAllowed(f"Access restricted.")
            elif not restricted and role == auth.ROLE_PARTICIPANT:  # Participants can access when it is their resource, the resource is visible to them, and the call is not restricted
                return func(request, *args, **kwargs)
            elif role == auth.ROLE_GUEST:  # If guests access a restricted resource, we send them to login
                return redirect('tira:login')

            return HttpResponseNotAllowed(f"Access forbidden.")

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
