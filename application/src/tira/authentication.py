"""

"""
import json
import logging
import os
from datetime import datetime
from functools import wraps

import requests
from django.conf import settings
from django.http import JsonResponse, Http404, HttpResponseNotAllowed
import tira.tira_model as model

from google.protobuf.text_format import Parse

from .proto import TiraClientWebMessages_pb2 as modelpb

logger = logging.getLogger(__name__)


class Authentication(object):
    """ Base class for Authentication and Role Management"""
    subclasses = {}
    _AUTH_SOURCE = 'superclass'
    ROLE_TIRA = "tira"  # super admin if we ever need it
    ROLE_ADMIN = "admin"  # is admin for the requested resource, so all permissions
    ROLE_PARTICIPANT = "participant"  # has edit but not admin permissions - user-header is set, group is set
    ROLE_USER = "user"  # is logged in, but has no edit permissions - user-header is set, group (tira-vm-vm_id) is not set
    ROLE_FORBIDDEN = 'forbidden'
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

    @staticmethod
    def get_default_vm_id(user_id):
        return f"{user_id}-default"

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None):
        """ Determine the role of the user on the requested page (determined by the given directives).

        @param request: djangos request object associated to the http request
        @param user_id: id of the user requesting the resource
        @param resource_id: to check which role user_id has on the requested resource
        @param resource_type: the type of the resource: {vm_id, task_id, dataset_id}
        :return ROLE_GUEST: if disraptor token is wrong or user is not logged in
        :return ROLE_ADMIN: if user is in group 'admins'
        :return ROLE_PARTICIPANT: if user is in the vm-group of the given :param vm_id:
        :return ROLE_USER: if user is logged in, but not in the group of :param vm_id:
        """
        return self.ROLE_GUEST

    def get_auth_source(self):
        return self._AUTH_SOURCE

    def get_user_id(self, request):
        return None

    def get_vm_id(self, request, user_id):
        return "None"

    def login(self, request, **kwargs):
        pass

    def logout(self, request, **kwargs):
        pass

    def create_group(self, vm_id):
        return {"status": 0, "message": f"create_group is not implemented for {self._AUTH_SOURCE}"}

    def get_organizer_ids(self, request, user_id=None):
        pass

    def get_vm_ids(self, request, user_id=None):
        pass

class LegacyAuthentication(Authentication):
    _AUTH_SOURCE = "legacy"

    def __init__(self, **kwargs):
        """ Load data from the file database to support legacy authentication
        @param kwargs:
        - :param users_file: path to the users.prototext that contains the user data
        """
        super(LegacyAuthentication, self).__init__(**kwargs)

    def login(self, request, **kwargs):
        """ Set a user_id cookie to the django session
        @param kwargs:
        - :param user_id:
        - :param password:
        """
        try:
            user = model.get_vm(kwargs["user_id"])
            if kwargs["password"] == user['user_password']:
                request.session["user_id"] = kwargs["user_id"]
            else:
                return False
        except:
            return False
        return True

    def logout(self, request, **kwargs):
        """ Remove a user_id cookie from the django session """
        try:
            del request.session["user_id"]
        except KeyError:
            pass

    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None):
        """ Determine the role of the user on the requested page (determined by the given directives).
        This is a minimalistic implementation using the legacy account storage.

        This implementation ignores the request object. User get_user_id and get_vm_id

        Currently only checks: (1) is user admin, (2) otherwise, is user owner of the vm (ROLE_PARTICIPANT)
        """
        if not user_id:
            return self.ROLE_GUEST
        user = model.get_vm(user_id)
        if not user:
            return self.ROLE_GUEST

        if 'reviewer' in user['roles']:
            return self.ROLE_ADMIN

        # NOTE: in the old user management vm_id == user_id
        if user_id == vm_id or Authentication.get_default_vm_id(user_id) == vm_id:
            return self.ROLE_PARTICIPANT

        if user_id != vm_id and vm_id is not None and vm_id != Authentication.get_default_vm_id(user_id):
            return self.ROLE_FORBIDDEN

        return self.ROLE_USER

    # TODO creating the default user should be done at some other point that's less frequently called.
    def get_user_id(self, request):
        user_id = request.session.get("user_id", None)
        if user_id:
            vm_id = Authentication.get_default_vm_id(user_id)
            _ = model.get_vm(vm_id, create_if_none=True)

        return request.session.get("user_id", None)

    def get_vm_id(self, request, user_id):
        """ Note: in the old schema, user_id == vm_id"""
        user = model.get_vm(user_id)
        if user and user['host']:  # i.e. if there is a host somewhere
            return user_id
        return Authentication.get_default_vm_id(user_id)

    def get_organizer_ids(self, request, user_id=None):
        return []

    def get_vm_ids(self, request, user_id=None):
        return []

def check_disraptor_token(func):
    @wraps(func)
    def func_wrapper(auth, request, *args, **kwargs):
        _DISRAPTOR_APP_SECRET_KEY = os.getenv("DISRAPTOR_APP_SECRET_KEY")

        if not request.headers.get('X-Disraptor-App-Secret-Key', None) == _DISRAPTOR_APP_SECRET_KEY:
            return HttpResponseNotAllowed(f"Access forbidden.")

        return func(auth, request, *args, **kwargs)

    return func_wrapper


class DisraptorAuthentication(Authentication):
    _AUTH_SOURCE = "disraptor"

    def _get_user_id(self, request):
        """ Return the content of the X-Disraptor-User header set in the http request """
        user_id = request.headers.get('X-Disraptor-User', None)
        if user_id:
            vm_id = Authentication.get_default_vm_id(user_id)
            _ = model.get_vm(vm_id, create_if_none=True)
        return user_id

    def _is_in_group(self, request, group_name='tira_reviewer') -> bool:
        """ return True if the user is in the given disraptor group"""
        return group_name in request.headers.get('X-Disraptor-Groups', "").split(",")

    def _parse_tira_groups(self, groups: list) -> list:
        """ find all groups with 'tira_' prefix and return key and value of the group.
         Note: Groupnames should be in the format '[tira_]key[_value]'
         """
        for group in groups:
            g = group.split("_")
            if g[0] == 'tira':
                try:
                    key = g[1]
                except IndexError:
                    continue
                try:
                    value = g[2]
                except IndexError:
                    value = None
                yield {"key": key, "value": value}

    def _get_user_groups(self, request, group_type: str = "vm") -> list:
        """ read groups from the disraptor groups header.
        @param group_type: {"vm", "org"}, indicate the class of groups.
        """
        all_groups = request.headers.get('X-Disraptor-Groups', "None").split(",")
        user_id = f"{request.headers.get('X-Disraptor-User', None)}-default"

        if group_type == 'vm':  # if we check for groups of a virtual machine
            return [group["value"] for group in self._parse_tira_groups(all_groups) if group["key"] == "vm"] + [user_id]
        if group_type == 'org':  # if we check for organizer groups of a user
            return [group["value"] for group in self._parse_tira_groups(all_groups) if group["key"] == "org"]

    @check_disraptor_token
    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None):
        """ Determine the role of the user on the requested page (determined by the given directives).
        This is a minimalistic implementation that suffices for the current features of TIRA.

        This implementation relies only on the request object, since disraptor takes care of the rest.

        Currently only checks: (1) is user admin, (2) otherwise, is user owner of the vm (ROLE_PARTICIPANT)
        """

        if self._is_in_group(request, "admins") or self._is_in_group(request, "tira_reviewer"):
            return self.ROLE_ADMIN

        user_groups = self._get_user_groups(request, group_type='vm')
        # Role for users with permissions for the vm
        if vm_id in user_groups:
            return self.ROLE_PARTICIPANT
        elif user_id and not vm_id:
            return self.ROLE_USER
        # Role without permissions for the vm
        elif user_id and vm_id in user_groups:
            return self.ROLE_FORBIDDEN
        return self.ROLE_GUEST

    @check_disraptor_token
    def get_user_id(self, request):
        """ public wrapper of _get_user_id that checks conditions """
        return self._get_user_id(request)

    @check_disraptor_token
    def get_vm_id(self, request, user_id=None):
        """ return the vm_id of the first vm_group ("tira-vm-<vm_id>") found.
         If there is no vm-group, return "no-vm-assigned"
         """
         
        return self.get_vm_ids(request, user_id)[0]

    @check_disraptor_token
    def get_organizer_ids(self, request, user_id=None):
        """ return the organizer ids of all organizer teams that the user is found in ("tira-org-<vm_id>").
        If there is no vm-group, return the empty list
        """

        return self._get_user_groups(request, group_type='org')

    @check_disraptor_token
    def get_vm_ids(self, request, user_id=None):
        """ returns a list of all vm_ids of the all vm_groups ("tira-vm-<vm_id>") found.
         If there is no vm-group, a list with "no-vm-assigned" is returned
         """
        vms = self._get_user_groups(request)
        user_id = self._get_user_id(request)
        
        if user_id == None:
            return vms
        
        return vms if len(vms) >= 1 else [Authentication.get_default_vm_id(user_id)]

    def _discourse_api_key(self):
        return open(settings.DISRAPTOR_SECRET_FILE, "r").read().strip()

    def _create_discourse_group(self, group_name, group_bio, visibility_level=2, members_visibility_level=2):
        """ Create a discourse group in the distaptor. 
        :param vm: a vm dict as returned by tira_model.get_vm
            {"vm_id", "user_password", "roles", "host", "admin_name", "admin_pw", "ip", "ssh", "rdp", "archived"}

        """
        ret = requests.post("https://www.tira.io/admin/groups",
                            headers={"Api-Key": self._discourse_api_key(), "Accept": "application/json",
                                     "Content-Type": "multipart/form-data"},
                            data={"group[name]": group_name, "group[visibility_level]": visibility_level,
                                  "group[members_visibility_level]": members_visibility_level, "group[bio_raw]": group_bio}
                            )

        return json.loads(ret.text).get('basic_group', {'id': group_name})["id"]
        
    def _create_discourse_vm_group(self, vm):
        """ Create the vm group in the distaptor. Members of this group will be owners of the vm and
            have all permissions.
        :param vm: a vm dict as returned by tira_model.get_vm
            {"vm_id", "user_password", "roles", "host", "admin_name", "admin_pw", "ip", "ssh", "rdp", "archived"}

        """
        group_bio = f"""Members of this group have access to the virtual machine {vm['vm_id']}:<br><br>
    <ul>
      <li>Host: {vm['host']}</li>
      <li>User: {vm['vm_id']}</li>
      <li>Passwort: {vm['user_password']}</li>
      <li>SSH Port: {vm['ssh']}</li>
      <li>RDP Port: {vm['rdp']}</li>
      <li>SSH Example: <code>sshpass -p {vm['user_password']} ssh {vm['vm_id']}@{vm['host']} -p {vm['ssh']} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no</code></li>
    </ul><br><br>
    Please contact us when you have questions.
    """
    
        return _create_discourse_group(f"tira_vm_{vm['vm_id']}", group_bio, 2)

    def _create_discourse_invite_link(self, group_id):
        """ Create the invite link to get permission to a discourse group """
        ret = requests.post("https://www.tira.io/invites",
                            headers={"Api-Key": self._discourse_api_key(), "Accept": "application/json",
                                     "Content-Type": "multipart/form-data"},
                            data={"group_ids[]": group_id, "max_redemptions_allowed": 20,
                                  "expires_at": str(datetime.now().year + 1) + "-12-31"}
                            )

        return json.loads(ret.text)['link']

    def _add_user_as_owner_to_group(self, group_id, user_name):
        """ Create the invite link to get permission to a discourse group """
        
        ret = requests.put(f"https://www.tira.io/admin/groups/{group_id}/owners.json",
                            headers={"Api-Key": self._discourse_api_key(), "Accept": "application/json",
                                     "Content-Type": "multipart/form-data"
                                     },
                            data={"group[usernames]": user_name, "group[notify_users]": "true"}
                            )
        
        ret = json.loads(ret.text)
        
        if ret['success'] != 'OK' or ret['usernames'] != [user_name]:
            raise ValueError(f'Could not make the user "{user_name}" an owner of the group with id "{group_id}".')

        return ret

    def create_group(self, vm):
        """ Create the vm group in the distaptor. Members of this group will be owners of the vm and
            have all permissions.
        :param vm: a vm dict as returned by tira_model.get_vm
        """
        vm_group = self._create_discourse_vm_group(vm)
        invite_link = self._create_discourse_invite_link(vm_group)
        message = f"""Invite Mail: Please use this link to create your login for TIRA: {invite_link}. 
                      After login to TIRA, you can find the credentials and usage examples for your
                      dedicated virtual machine {vm['vm_id']} here: https://www.tira.io/g/tira_vm_{vm['vm_id']}"""

        return message

    def create_organizer_group(self, organizer_name, user_name):
        group_bio = f"""Members of this team organize shared tasks in TIRA as  in shared tasks as {organizer_name}. <br><br>
        
        Please do not hesitate to design your page accorging to your needs."""
        
        group_id = self._create_discourse_group(f"tira_org_{organizer_name}", group_bio, 0)
        self._add_user_as_owner_to_group(group_id, user_name)

    def create_docker_group(self, team_name, user_name):
        group_bio = f"""Members of this team participate in shared tasks as {team_name}. <br><br>
        
        Please do not hesitate to design your team's page accorging to your needs."""
        
        group_id = self._create_discourse_group(f"tira_vm_{team_name}", group_bio, 0)
        self._add_user_as_owner_to_group(group_id, user_name)

auth = Authentication(authentication_source=settings.DEPLOYMENT)

