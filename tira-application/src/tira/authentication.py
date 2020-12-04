"""

"""
import logging
from google.protobuf.text_format import Parse
from pathlib import Path
from .proto import TiraClientWebMessages_pb2 as modelpb


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
        :param kwargs: other parameters of creation, they will differ between subclasses
        :return: the instance
        """
        return super(Authentication, cls).__new__(cls.subclasses[authentication_source])

    def __init__(self, **kwargs):
        pass

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):
        return self.ROLE_ADMIN

    def get_user_id(self, request):
        return "None"

    def get_user_groups(self, request):
        return ["1"]


class StandaloneAuthentication(Authentication):
    _AUTH_SOURCE = "standalone"

    def __init__(self, **kwargs):
        super(StandaloneAuthentication, self).__init__(**kwargs)
        self.users_file_path = kwargs["tira_root"] / "model/users/users.prototext"

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):
        return self.ROLE_ADMIN

    def get_user_id(self, request):
        return "None"

    def get_user_groups(self, request):
        return ["2"]


class DisraptorAuthentication(Authentication):
    _AUTH_SOURCE = "disraptor"

    def _reply_if_allowed(self, request, response):
        """ TODO return the response if the the disraptor secret is correct """
        print(request.headers.get('X-Disraptor-App-Secret-Key', None))
        return response

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):

        return self.ROLE_ADMIN

    def get_user_id(self, request):
        user_id = request.headers.get('X-Disraptor-User', "None")
        print(user_id)
        return self._reply_if_allowed(request, user_id)

    def get_user_groups(self, request):
        user_groups = request.headers.get('X-Disraptor-Groups', "None").split(",")
        print(user_groups)
        return self._reply_if_allowed(request, user_groups)
