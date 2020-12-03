"""

"""
import logging
from google.protobuf.text_format import Parse
from pathlib import Path
from .proto import TiraClientWebMessages_pb2 as modelpb


class Authentication(object):
    """ Base class for Authentication and Role Management"""
    subclasses = {}
    ROLE_TIRA = 0  # super admin if we ever need it
    ROLE_ADMIN = 1  # is admin for the requested resource, so all permissions
    ROLE_PARTICIPANT = 2  # has edit but not admin permissions
    ROLE_USER = 3  # is logged in, but has no edit permissions
    ROLE_GUEST = 4  # not logged in

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


class StandaloneAuthentication(Authentication):
    _AUTH_SOURCE = "standalone"

    def __init__(self, **kwargs):
        super(StandaloneAuthentication, self).__init__(**kwargs)
        self.users_file_path = kwargs["tira_root"] / "model/users/users.prototext"

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):
        return self.ROLE_ADMIN


class DisraptorAuthentication(Authentication):
    _AUTH_SOURCE = "disraptor"

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None, dataset_id: str = None):
        return self.ROLE_ADMIN
