from .tira_model import FileDatabase
from .authentication import auth
from .tira_model import model
from django.core.exceptions import PermissionDenied
from functools import wraps


def actions_check_permissions(roles):
    """ A decorator that checks if the requesting user has the needed role for this request.

    :@param roles: an iterable of role strings (Authentication.ROLE_ADMIN, ...)
    :@param on_vm: If the permissions of a user against a vm are requested, this
                   parameter should be the position of the vm_id in args. Otherwise, None.

    :returns: A JsonResponse
    :raises: django.core.exceptions.PermissionDenied
    """
    def state_check_decorator(func):
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
    return state_check_decorator


def check_vm_exists():
    pass


def check_resource_exists():
    pass


class Check(object):
    def has_access(self, request, roles, on_vm_id=None):
        """ Check if user has a given role.
        @param request: a django request object
        @param roles: a list of roles that should be allowed or 'any'
        @param on_vm_id: If not None, check permissions for the given vm
        """
        if on_vm_id is not None:
            role = self._has_access_to_vm(request, vm_id=on_vm_id)
        else:
            role = self._has_role(request)
        if roles == "any":
            return True
        if role in roles:
            return True

        raise PermissionDenied

    def _has_role(self, request):
        return auth.get_role(request, auth.get_user_id(request))

    # TODO include logic from auth here instead
    def _has_access_to_vm(self, request, vm_id):
        """ Return the users permissions on the given vm_id.
         'participant' if he has edit permissions
         'admin' or 'tira' if user is admin/reviewer
         'user' if vm_id is 'no-vm-assigned'
         """
        role = auth.get_role(request,
                             user_id=auth.get_user_id(request),
                             vm_id=vm_id)
        if vm_id == 'no-vm-assigned' and role == 'user':
            return 'user'
        return role

    def task_exists(self, task_id):
        try:
            model.get_task(task_id)
            return True
        except KeyError:
            return False

    def organizer_exists(self, organizer_id):
        try:
            model.get_organizer(organizer_id)
            return True
        except KeyError:
            return False

    def vm_exists(self, vm_id):
        try:
            model.get_vm(vm_id)
            return True
        except KeyError:
            return False

    def dataset_exists(self, dataset_id):
        pass
