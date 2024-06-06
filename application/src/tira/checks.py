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

    # TODO at some point, this should not return http responses anymore but send a 'forbidden' json response
    :raises: django.core.exceptions.PermissionDenied
    """
    @wraps(func)
    def func_wrapper(request, *args, **kwargs):
        vm_id = kwargs.get('vm_id', None)
        user_id = kwargs.get('user_id', None)
        if vm_id is None and user_id is not None:  # some endpoints say user_id instead of vm_id
            vm_id = user_id
        dataset_id = kwargs.get('dataset_id', None)
        run_id = kwargs.get('run_id', None)
        task_id = kwargs.get('task_id', None)
        organizer_id = kwargs.get('organizer_id', None)
        role = auth.get_role(request, user_id=auth.get_user_id(request))

        if role == auth.ROLE_ADMIN or role == auth.ROLE_TIRA:
            return func(request, *args, **kwargs)
            
        # Listing runs for ir-lab at CLEF 2024 is public for the moment
        if request.path_info.startswith('api/list-runs/ir-lab-padua-2024/') or request.path_info.startswith('/api/list-runs/ir-lab-padua-2024/'):
             return func(request, *args, **kwargs)
        
        # Listing runs for ir-lab at CLEF 2024 is public for the moment
        if (request.path_info.startswith('task/ir-lab-padua-2024/user/') or request.path_info.startswith('/task/ir-lab-padua-2024/user/')) and request.path_info.endswith('.zip') and '/user/' in request.path_info and '/dataset/' in request.path_info and 'download' in request.path_info and request.path_info.split('/user/')[1].split('/')[1] == 'dataset' and request.path_info.split('/user/')[1].split('/')[3] == 'download':
            return func(request, *args, **kwargs)

        # SERP endpoint is allowed for runs that are published and unblinded
        if (request.path_info.startswith('serp/') or request.path_info.startswith('/serp/')) and run_id \
                and run_id in request.path_info and model.run_is_public_and_unblinded(run_id):
            return func(request, *args, **kwargs)

        if (request.path_info.startswith('data-download/') or request.path_info.startswith('/data-download/')) and dataset_is_public(dataset_id):
            return func(request, *args, **kwargs)

        if 'run_id_1' in kwargs or 'run_id_2' in kwargs:
            return HttpResponseNotAllowed(f"Access forbidden.")

        if request.path_info.startswith(f'/task/{task_id}/vm/{vm_id}/software_details/'):
            software_name = request.path_info.split(f'/task/{task_id}/vm/{vm_id}/software_details/')[1].split('/')[0]
            software = model.get_docker_software_by_name(software_name, vm_id, task_id)
            if software and 'public_image_name' in software and software['public_image_name']:
                return func(request, *args, **kwargs)

        if request.path_info.startswith(f'/task/{task_id}/vm/{vm_id}/run_details/'):

            review = model.model.get_run_review(run_id=run_id, dataset_id=dataset_id, vm_id=vm_id)
            logger.warning(f'Show run details for {run_id}: {review}.')
            print(f'Show run details for {run_id}: {review}.')
            if review and 'published' in review and 'blinded' in review and review['published'] and not review['blinded']:
                return func(request, *args, **kwargs)

        if auth.user_is_organizer_for_endpoint(request=request, path=request.path_info, task_id=task_id,
                                               organizer_id_from_params=organizer_id, dataset_id_from_params=dataset_id,
                                               run_id_from_params=run_id, vm_id_from_params=vm_id, role=role):
            return func(request, *args, **kwargs)

        if vm_id:
            if not model.vm_exists(vm_id):  # If the resource does not exist
                return redirect('tira:login')
            role = auth.get_role(request, user_id=auth.get_user_id(request), vm_id=vm_id)
            if run_id and dataset_id:  # this prevents participants from viewing hidden runs
                if not model.run_exists(vm_id, dataset_id, run_id):
                    return Http404(f'The VM {vm_id} has no run with the id {run_id} on {dataset_id}.')
                review = model.get_run_review(dataset_id, vm_id, run_id)
                dataset = model.get_dataset(dataset_id)
                is_review_visible = (not review['blinded']) or review['published'] or not dataset.get('is_confidential', True)
                if not is_review_visible:
                    role = auth.ROLE_USER
            if task_id:  # This checks if the registration requirement is fulfilled.
                if model.get_task(task_id)["require_registration"]:
                    if not model.user_is_registered(task_id, request):
                        return HttpResponseNotAllowed(f"Access forbidden. You must register first.")

        if role == auth.ROLE_PARTICIPANT:
            return func(request, *args, **kwargs)
        elif role == auth.ROLE_GUEST:  # If guests access a restricted resource, we send them to login
            return redirect('tira:login')

        if 'docker_software_id' in kwargs and vm_id:
            docker_software = model.get_docker_software(int(kwargs['docker_software_id']))
            if docker_software and 'vm_id' in docker_software and auth.ROLE_PARTICIPANT == auth.get_role(request, user_id=auth.get_user_id(request), vm_id=docker_software['vm_id']):
                return func(request, *args, **kwargs)

        return HttpResponseNotAllowed(f"Access forbidden.")

    return func_wrapper


def check_conditional_permissions(restricted=False, public_data_ok=False, private_run_ok=False,
                                  not_registered_ok=False):
    """ A decorator that checks if the requesting user has the needed permissions to call the decorated function.
    This decorator redirects or blocks requests if the requesting user does not have permission.
    This decorator considers the resources requested in the decorated function:
        - vm_id: returns the permissions the requesting user has on the vm
        - run_id: in addition to vm_id, checks if the requesting user can see the run. By default, permission is denied
        if the run is not visible.

    @param restricted: if True, only admins can ever access the decorated function
    @param public_data_ok: if True and if a run is requested, return with permissions if the user owns the VM and the
        dataset is public, even if the run is blinded and not published
    @param private_run_ok: if True, and if a run is requested, return with permissions even if the run is blinded
    @param not_registered_ok: if True, and if a task is requests, return with permissions even if the user is not
        registered yet.

    :raises: django.core.exceptions.PermissionDenied
    """
    def decorator(func):
        @wraps(func)
        def func_wrapper(request, vm_id, *args, dataset_id=None, run_id=None, **kwargs):
            # Admins can access and do everything
            kwargs['vm_id'] = vm_id
            user_id = kwargs.get('user_id', None)
            task_id = kwargs.get('task_id', None)
            if vm_id is None and user_id is not None:  # some endpoints say user_id instead of vm_id
                vm_id = user_id
            if dataset_id:
                kwargs['dataset_id'] = dataset_id
            if run_id:
                kwargs['run_id'] = run_id

            role = auth.get_role(request, user_id=auth.get_user_id(request))
            if role == auth.ROLE_ADMIN or role == auth.ROLE_TIRA:
                return func(request, *args, **kwargs)
            elif auth.user_is_organizer_for_endpoint(request=request, path=request.path_info, task_id=task_id,
                                                   organizer_id_from_params=None,
                                                   dataset_id_from_params=dataset_id,
                                                   run_id_from_params=run_id, vm_id_from_params=vm_id, role=role):
                return func(request, *args, **kwargs)
            elif restricted:
                return HttpResponseNotAllowed(f"Access restricted.")

            if vm_id:  # First we determine the role of the user on the resource he requests
                if not model.vm_exists(vm_id):
                    return redirect('tira:login')
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

                if public_data_ok and run_is_public(run_id, vm_id, dataset_id):
                    return func(request, *args, **kwargs)

                if task_id and not not_registered_ok:  # This checks if the registration requirement is fulfilled.
                    if model.get_task(task_id)["require_registration"]:
                        if not model.user_is_registered(task_id, request):
                            return HttpResponseNotAllowed(f"Access forbidden. You must register first.")

            if not restricted and role == auth.ROLE_PARTICIPANT:  # Participants can access when it is their resource, the resource is visible to them, and the call is not restricted
                return func(request, *args, **kwargs)
            if public_data_ok and run_is_public(run_id, vm_id, dataset_id):
                return func(request, *args, **kwargs)
            elif role == auth.ROLE_GUEST:  # If guests access a restricted resource, we send them to login
                return redirect('tira:login')

            return HttpResponseNotAllowed(f"Access forbidden.")

        return func_wrapper
    return decorator


def run_is_public(run_id, vm_id, dataset_id):
    if not run_id or not vm_id or not dataset_id or (dataset_id not in settings.PUBLIC_TRAINING_DATA and not dataset_id.endswith('-training')):
        return False

    i = model.get_run_review(dataset_id, vm_id, run_id)
    if not (i and 'blinded' in i and 'published' in i and not i['blinded'] and i['published']):
        return False

    return dataset_is_public(dataset_id)


def dataset_is_public(dataset_id):
    if not dataset_id or (dataset_id not in settings.PUBLIC_TRAINING_DATA and not dataset_id.endswith('-training')):
        return False

    i = model.get_dataset(dataset_id)
    return i and 'is_confidential' in i and not i['is_confidential'] and 'is_deprecated' in i and not i['is_deprecated']


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
                    return redirect('tira:login')
                return Http404(message)

            if "vm_id" in kwargs:
                if not model.vm_exists(kwargs["vm_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: vm_id does not exist")
                    if "task_id" in kwargs:
                        return return_fail(f'There is no vm with id {kwargs["vm_id"]} matching your request.',
                                           request_vm_instead=True)

                    return return_fail(f"vm_id {kwargs['vm_id']} does not exist", request_vm_instead=True)

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
                if not model.run_exists(kwargs.get("vm_id", None), kwargs.get("dataset_id", None), kwargs["run_id"]):
                    logger.error(f"{resolve(request.path_info).url_name}: run_id does not exist")
                    return return_fail("run_id does not exist")

            return func(request, *args, **kwargs)

        return func_wrapper
    return decorator
