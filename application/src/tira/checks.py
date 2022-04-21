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
        vm_id = kwargs.get('vm_id', None)
        dataset_id = kwargs.get('dataset_id', None)
        run_id = kwargs.get('run_id', None)
        role = auth.get_role(request, user_id=auth.get_user_id(request))

        if role == auth.ROLE_ADMIN or role == auth.ROLE_TIRA:
            return func(request, *args, **kwargs)

        if vm_id:
            if not model.vm_exists(vm_id):
                return redirect('tira:request_vm')
            role = auth.get_role(request, user_id=auth.get_user_id(request), vm_id=vm_id)
            if run_id and dataset_id:
                if not model.run_exists(vm_id, dataset_id, run_id):
                    return Http404(f'The VM {vm_id} has no run with the id {run_id} on {dataset_id}.')
                review = model.get_run_review(dataset_id, vm_id, run_id)
                is_review_visible = (not review['blinded']) or review['published']
                if not is_review_visible:
                    role = auth.ROLE_USER

        if role == auth.ROLE_PARTICIPANT:
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
        def func_wrapper(request, vm_id, *args, dataset_id=None, run_id=None, **kwargs):
            # Admins can access and do everything
            kwargs['vm_id'] = vm_id
            if dataset_id:
                kwargs['dataset_id'] = dataset_id
            if run_id:
                kwargs['run_id'] = run_id

            role = auth.get_role(request, user_id=auth.get_user_id(request))
            if role == auth.ROLE_ADMIN or role == auth.ROLE_TIRA:
                return func(request, *args, **kwargs)
            elif restricted:
                return HttpResponseNotAllowed(f"Access restricted.")

            if vm_id:
                if not model.vm_exists(vm_id):
                    return redirect('tira:request_vm')
                role_on_vm = auth.get_role(request, user_id=auth.get_user_id(request), vm_id=vm_id)
                if run_id and dataset_id:
                    role = auth.ROLE_USER
                    if not model.run_exists(vm_id, dataset_id, run_id):
                        return Http404(f'The VM {vm_id} has no run with the id {run_id} on {dataset_id}.')

                    review = model.get_run_review(dataset_id, vm_id, run_id)
                    is_review_visible = (not review['blinded']) or review['published']
                    is_dataset_confidential = model.get_dataset(dataset_id).get('is_confidential', True)
                    # if the run is visible OR if we make an exception for public datasets
                    if is_review_visible:
                        role = role_on_vm
                    elif not is_dataset_confidential and public_data_ok:
                        role = role_on_vm
                    elif private_run_ok:
                        role = role_on_vm
                else:
                    role = role_on_vm

            if not restricted and role == auth.ROLE_PARTICIPANT:  # Participants can access when it is their resource, the resource is visible to them, and the call is not restricted
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
            def return_fail(message, request_vm_instead=False):
                logger.warning(message)
                if reply_as == 'json':
                    response = JsonResponse({'status': 1, 'message': message})
                    return response
                if request_vm_instead:
                    return redirect('tira:request_vm')
                return Http404

            if "vm_id" in kwargs:
                if not model.vm_exists(kwargs["vm_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: vm_id does not exist")
                    if "task_id" in kwargs:
                        # if kwargs["vm_id"] == "no-vm-assigned":
                        #     return return_fail('No vm was assigned, please request a vm.', request_vm_instead=True)
                        return return_fail(f'There is no vm with id {kwargs["vm_id"]} matching your request.',
                                           request_vm_instead=True)

                    return return_fail(f"vm_id {kwargs['vm_id']} does not exist", request_vm_instead=True)
                # TODO uncommented so uploads work without a live vm
                # elif not model.get_vm(kwargs["vm_id"]).get('host', None):
                #     return return_fail(f'The requested account has no live vm with id: {kwargs["vm_id"]}',
                #                        request_vm_instead=True)

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
