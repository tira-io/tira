"""

"""
import logging
from google.protobuf.text_format import Parse
from pathlib import Path
from .proto import TiraClientWebMessages_pb2 as modelpb
import re


class Authentication(object):
    """ Base class for Authentication and Role Management"""
    subclasses = {}
    ROLE_TIRA = "tira"  # super admin if we ever need it
    ROLE_ADMIN = "admin"  # is admin for the requested resource, so all permissions
    ROLE_PARTICIPANT = "participant"  # has edit but not admin permissions - user-header is set, group is set
    ROLE_USER = "user"  # is logged in, but has no edit permissions - user-header is set, group (tira-vm-vm_id) is not set
    ROLE_GUEST = "guest"  # not logged in -> user-header is not set

    def __init_subclass__(cls):
        """ Init base class based on parameter on creation """
        super().__init_subclass__()
        cls.subclasses[cls._AUTH_SOURCE] = cls

    def __new__(cls, authentication_source=None, **kwargs):
        """ Create base class based on parameter of construction
        :param api: the api type
        :param kwargs: other parameters of creation, they may differ between subclasses
        :return: the instance
        """
        return super(Authentication, cls).__new__(cls.subclasses[authentication_source])

    def __init__(self, **kwargs):
        pass

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):
        return self.ROLE_ADMIN

    def _get_user_id(self, request):
        return "None"

    def get_user_id(self, request):
        return "None"

    def _get_user_groups(self, request):
        return ["1"]

    def get_vm_id(self, request, user_id: str = None):
        return "None"


class StandaloneAuthentication(Authentication):
    _AUTH_SOURCE = "standalone"

    def __init__(self, **kwargs):
        super(StandaloneAuthentication, self).__init__(**kwargs)
        self.users_file_path = kwargs["tira_root"] / "model/users/users.prototext"

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):
        return self.ROLE_ADMIN

    def get_user_id(self, request):
        return "None"

    def _get_user_groups(self, request):
        return ["2"]


class DisraptorAuthentication(Authentication):
    _AUTH_SOURCE = "disraptor"

    def _reply_if_allowed(self, request, response, alternative="None"):
        """ Returns the :param response: if disraptor auth token is correct, otherwise returns the :param alternative:
        TODO return the response if the the disraptor secret is correct but WHERE IS THAT???
        """
        # print(request.headers.get('X-Disraptor-App-Secret-Key', None))
        return response

    def _get_user_id(self, request):
        """ Return the content of the X-Disraptor-User header set in the http request """
        user_id = request.headers.get('X-Disraptor-User', "None")
        return user_id

    def _get_user_groups(self, request) -> tuple:
        """ read groups from the disraptor groups header.
        Returns a tuple:
        - first value is a bool if the user is in the group "admins"
        - second value is a list of vm_ids which the user has permissions the see
        """
        all_groups = request.headers.get('X-Disraptor-Groups', "None").split(",")
        vm_groups = [u.split("-")[2:] for u in all_groups if u.startswith("tira-vm-")]
        return "admins" in all_groups, vm_groups

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):
        """ Determine the role of the user on the requested page (determined by the given directives).
        This is a minimalistic implementation that suffices for the current state of TIRA.

        :return ROLE_GUEST: if disraptor token is wrong or user is not logged in
        :return ROLE_ADMIN: if user is in group 'admins'
        :return ROLE_PARTICIPANT: if user is in the vm-group of the given :param vm_id:
        "return ROLE_USER: if user is logged in, but not in the group of :param vm_id:
        """
        is_admin, user_groups = self._get_user_groups(request)
        if is_admin:
            return self._reply_if_allowed(request, self.ROLE_ADMIN, self.ROLE_GUEST)
        elif vm_id in user_groups:
            return self._reply_if_allowed(request, self.ROLE_PARTICIPANT, self.ROLE_GUEST)
        elif user_id:
            return self._reply_if_allowed(request, self.ROLE_USER, self.ROLE_GUEST)
        return self.ROLE_GUEST

    def get_user_id(self, request):
        """ public wrapper of _get_user_id that checks conditions """
        return self._reply_if_allowed(request, self._get_user_id(request))

    def get_vm_id(self, request, user_id=None):
        """ return the vm_id of the first vm_group ("tira-vm-<vm_id>") found.
         If there is no vm-group, return "no-vm-assigned"
         """
        _, vms = self._get_user_groups(request)
        return vms[0] if len(vms) >= 1 else "no-vm-assigned"


