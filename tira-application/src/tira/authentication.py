"""

"""
import json
import logging
import os
from datetime import datetime

import requests
from django.conf import settings
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
        return {"status": 0, "message": f"create_group is not implemented for {self.__name__}"}


class LegacyAuthentication(Authentication):
    _AUTH_SOURCE = "legacy"

    def __init__(self, **kwargs):
        """ Load data from the file database to support legacy authentication
        @param kwargs:
        - :param users_file: path to the users.prototext that contains the user data
        """
        super(LegacyAuthentication, self).__init__(**kwargs)
        self.users = {}
        self.users_file = kwargs["users_file"]
        self.load_legacy_users()

    def load_legacy_users(self):
        users = Parse(open(self.users_file, "r").read(), modelpb.Users())
        self.users = {user.userName: user for user in users.users}

    def login(self, request, **kwargs):
        """ Set a user_id cookie to the django session
        @param kwargs:
        - :param user_id:
        - :param password:
        """
        try:
            user = self.users.get(kwargs["user_id"])
            if kwargs["password"] == user.userPw:
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

    # TODO permission logic should be in check.
    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None):
        """ Determine the role of the user on the requested page (determined by the given directives).
        This is a minimalistic implementation using the legacy account storage.

        This implementation ignores the request object. User get_user_id and get_vm_id

        Currently only checks: (1) is user admin, (2) otherwise, is user owner of the vm (ROLE_PARTICIPANT)
        """
        user = self.users.get(user_id, None)
        if not user_id or not user:
            return self.ROLE_GUEST

        if 'reviewer' in {role for role in user.roles}:
            return self.ROLE_ADMIN
        # NOTE: in the old user management vm_id == user_id
        if user_id == vm_id:
            return self.ROLE_PARTICIPANT

        if user_id != vm_id and vm_id is not None and vm_id != 'no-vm-assigned':
            return self.ROLE_FORBIDDEN

        return self.ROLE_USER

    def get_user_id(self, request):
        return request.session.get("user_id", None)

    def get_vm_id(self, request, user_id):
        """ Note: in the old schema, user_id == vm_id"""
        user = self.users.get(user_id, None)
        if user and user.vmName:
            return user_id
        return "no-vm-assigned"


class DisraptorAuthentication(Authentication):
    _AUTH_SOURCE = "disraptor"
    _DISRAPTOR_APP_SECRET_KEY = os.getenv("DISRAPTOR_APP_SECRET_KEY")

    # TODO should be in check
    def _reply_if_allowed(self, request, response, alternative="None"):
        """ Returns the :param response: if disraptor auth token is correct, otherwise returns the :param alternative:
        """
        if request.headers.get('X-Disraptor-App-Secret-Key', None) == self._DISRAPTOR_APP_SECRET_KEY:
            return response
        else:
            return alternative

    @staticmethod
    def _get_user_id(request):
        """ Return the content of the X-Disraptor-User header set in the http request """
        user_id = request.headers.get('X-Disraptor-User', None)
        return user_id

    @staticmethod
    def _is_in_group(request, group_name='tira_reviewer') -> bool:
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
        @param group_type: {"vm"}, indicate the class of groups.
        """
        all_groups = request.headers.get('X-Disraptor-Groups', "None").split(",")

        if group_type == 'vm':  # if we check for groups of a virtual machine
            return [group["value"] for group in self._parse_tira_groups(all_groups) if group["key"] == "vm"]
            # return [u.split("-")[2:] for u in all_groups if u.startswith("tira-vm-")]

    # TODO: permission logic should be in Check
    def get_role(self, request, user_id: str = None, vm_id: str = None, task_id: str = None):
        """ Determine the role of the user on the requested page (determined by the given directives).
        This is a minimalistic implementation that suffices for the current features of TIRA.

        This implementation relies only on the request object, since disraptor takes care of the rest.

        Currently only checks: (1) is user admin, (2) otherwise, is user owner of the vm (ROLE_PARTICIPANT)
        """

        if self._is_in_group(request, "admins"):
            return self._reply_if_allowed(request, self.ROLE_ADMIN, self.ROLE_GUEST)

        user_groups = self._get_user_groups(request, group_type='vm')
        # Role for users with permissions for the vm
        if vm_id in user_groups:
            return self._reply_if_allowed(request, self.ROLE_PARTICIPANT, self.ROLE_GUEST)
        # Role for registered
        elif user_id and not vm_id:
            return self._reply_if_allowed(request, self.ROLE_USER, self.ROLE_GUEST)
        # Role without permissions for the vm
        elif user_id and vm_id in user_groups:
            return self._reply_if_allowed(request, self.ROLE_FORBIDDEN, self.ROLE_GUEST)
        return self.ROLE_GUEST

    def get_user_id(self, request):
        """ public wrapper of _get_user_id that checks conditions """
        return self._reply_if_allowed(request, self._get_user_id(request))

    def get_vm_id(self, request, user_id=None):
        """ return the vm_id of the first vm_group ("tira-vm-<vm_id>") found.
         If there is no vm-group, return "no-vm-assigned"
         """
        vms = self._get_user_groups(request)
        return vms[0] if len(vms) >= 1 else "no-vm-assigned"

    def _discourse_api_key(self):
        return open(settings.DISRAPTOR_SECRET_FILE, "r").read().strip()

    def _create_discourse_group(self, vm):
        group_bio = f"""Members of this group have access to the virtual machine ${vm.userName}:<br><br>
    <ul>
      <li>Host: {vm.host}</li>
      <li>User: {vm.userName}</li>
      <li>Passwort: {vm.userPw}</li>
      <li>SSH Port: {vm.portSsh}</li>
      <li>RDP Port: {vm.portRdp}</li>
      <li>SSH Example: <code>sshpass -p {vm.userPw} ssh {vm.userName}@{vm.host} -p {vm.portSsh} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no</code></li>
    </ul><br><br>
    Please contact us when you have questions.
    """

        ret = requests.post("https://www.tira.io/admin/groups",
                            headers={"Api-Key": self._discourse_api_key(), "Accept": "application/json",
                                     "Content-Type": "multipart/form-data"},
                            data={"group[name]": f"tira_vm_{vm.userName}", "group[visibility_level]": 2,
                                  "group[members_visibility_level]": 2, "group[bio_raw]": group_bio}
                            )

        return json.loads(ret.text)['basic_group']['id']

    def _create_discourse_invite_link(self, group_id):
        ret = requests.post("https://www.tira.io/invites",
                            headers={"Api-Key": self._discourse_api_key(), "Accept": "application/json",
                                     "Content-Type": "multipart/form-data"},
                            data={"group_ids[]": group_id, "max_redemptions_allowed": 20,
                                  "expires_at": str(datetime.now().year + 1) + "-12-31"}
                            )

        return json.loads(ret.text)['link']

    def create_group(self, vm_id):
        vm_group = self._create_discourse_group(vm_id)
        invite_link = self._create_discourse_invite_link(vm_group)

        return {"status": 1,
                "message": f"Invite Mail: Please use this link to create your login for TIRA: {invite_link}. "
                           f"After login to TIRA, you can find the credentials and usage examples for your "
                           f"dedicated virtual machine {vm_id} here: https://www.tira.io/g/tira_vm_{vm_id}"}


auth = Authentication(authentication_source=settings.DEPLOYMENT,
                      users_file=settings.LEGACY_USER_FILE)
