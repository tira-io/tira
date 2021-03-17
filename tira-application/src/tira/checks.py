from .tira_model import FileDatabase
from .authentication import Authentication


class Check(object):

    def __init__(self, model, authentication):
        self.model = model
        self.authentication = authentication

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

        return False

    def _has_role(self, request):
        return self.authentication.get_role(request, self.authentication.get_user_id(request))

    # TODO include logic from auth here instead
    def _has_access_to_vm(self, request, vm_id):
        """ Return the users permissions on the given vm_id.
         'participant' if he has edit permissions
         'admin' or 'tira' if user is admin/reviewer
         'user' if vm_id is 'no-vm-assigned'
         """
        role = self.authentication.get_role(request,
                                            user_id=self.authentication.get_user_id(request),
                                            vm_id=vm_id)
        if vm_id == 'no-vm-assigned' and role == 'user':
            return 'user'
        return role

    def task_exists(self, task_id):
        try:
            self.model.get_task(task_id)
            return True
        except KeyError:
            return False

    def organizer_exists(self, organizer_id):
        try:
            self.model.get_organizer(organizer_id)
            return True
        except KeyError:
            return False

    def vm_exists(self, vm_id):
        try:
            self.model.get_vm(vm_id)
            return True
        except KeyError:
            return False

    def dataset_exists(self, dataset_id):
        pass