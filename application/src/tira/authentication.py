import json
import logging
import os
from functools import wraps
from typing import Optional

import tira.tira_model as model
from django.conf import settings
from django.http import HttpRequest, HttpResponseNotAllowed
from slugify import slugify

logger = logging.getLogger(__name__)

# TODO: this file can be reduced significantly when the differen deployment configurations are removed


class Authentication(object):
    """Base class for Authentication and Role Management"""

    subclasses: dict[str, type] = {}
    _AUTH_SOURCE = "superclass"
    ROLE_TIRA = "tira"  # super admin if we ever need it
    ROLE_ADMIN = "admin"  # is admin for the requested resource, so all permissions
    ROLE_PARTICIPANT = "participant"  # has edit but not admin permissions - user-header is set, group is set
    ROLE_USER = (  # is logged in, but has no edit permissions - user-header is set, group (tira-vm-vm_id) is not set
        "user"
    )
    ROLE_FORBIDDEN = "forbidden"
    ROLE_GUEST = "guest"  # not logged in -> user-header is not set

    def __init_subclass__(cls):
        """Init base class based on parameter on creation"""
        super().__init_subclass__()
        cls.subclasses[cls._AUTH_SOURCE] = cls

    def __new__(cls, authentication_source=None):
        """Create base class based on parameter of construction
        :param api: the api type
        :return: the instance
        """
        return super(Authentication, cls).__new__(cls.subclasses[authentication_source])

    def __init__(self, **kwargs):
        pass

    @staticmethod
    def get_default_vm_id(user_id: str) -> str:
        return f"{user_id}-default"

    def get_role(
        self,
        request: HttpRequest,
        user_id: Optional[str] = None,
        vm_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        """Determine the role of the user on the requested page (determined by the given directives).

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

    def get_user_id(self, request: HttpRequest):
        return None

    def get_vm_id(self, request: HttpRequest, user_id):
        return "None"

    def login(self, request: HttpRequest, **kwargs):
        pass

    def logout(self, request: HttpRequest, **kwargs):
        pass

    def create_group(self, vm_id):
        return {"status": 0, "message": f"create_group is not implemented for {self._AUTH_SOURCE}"}

    def get_organizer_ids(self, request: HttpRequest, user_id=None):
        pass

    def get_vm_ids(self, request: HttpRequest, user_id=None):
        pass

    def user_is_organizer_for_endpoint(
        self,
        request,
        path,
        task_id,
        organizer_id_from_params,
        dataset_id_from_params,
        run_id_from_params,
        vm_id_from_params,
        role,
    ):
        return False

    def is_admin_for_task(self, request):
        """
        Returns true if the user is an admin for the task specified in the request (false if the request url does not
        point to a task or if the user is only admin for some other task).
        """
        organizer_ids = auth.get_organizer_ids(request)

        if not organizer_ids or not isinstance(organizer_ids, list) or len(organizer_ids) < 1:
            return False

        task_id = None
        if request.path_info.startswith("submit/") or request.path_info.startswith("/submit/"):
            task_id = (request.path_info + "/").split("submit/")[1].split("/")[0]
        elif request.path_info.startswith("task-overview/") or request.path_info.startswith("/task-overview/"):
            task_id = (request.path_info + "/").split("task-overview/")[1].split("/")[0]

        if not task_id:
            return False

        try:
            task = model.get_task(task_id)
        except Exception:
            return False

        if not task:
            return False

        return task is not None and "organizer_id" in task and task["organizer_id"] in organizer_ids


def check_disraptor_token(func):
    @wraps(func)
    def func_wrapper(auth, request, *args, **kwargs):
        _DISRAPTOR_APP_SECRET_KEY = os.getenv("DISRAPTOR_APP_SECRET_KEY")

        if not request.headers.get("X-Disraptor-App-Secret-Key", None) == _DISRAPTOR_APP_SECRET_KEY:
            return HttpResponseNotAllowed("Access forbidden.")

        return func(auth, request, *args, **kwargs)

    return func_wrapper


class DisraptorAuthentication(Authentication):
    _AUTH_SOURCE = "disraptor"

    def __init__(self, **kwargs):
        """Disraptor authentication that delegates all authentication to discourse/disraptor.
        @param kwargs:
            unused, only for consistency to the LegacyAuthentication
        """
        super(DisraptorAuthentication, self).__init__(**kwargs)
        self.discourse_client = model.discourse_api_client()

    def _get_user_id(self, request: HttpRequest) -> Optional[str]:
        """Return the content of the X-Disraptor-User header set in the http request"""
        user_id = request.headers.get("X-Disraptor-User", None)
        if user_id is not None:
            vm_id = Authentication.get_default_vm_id(user_id)
            _ = model.get_vm(vm_id, create_if_none=True)
        return user_id

    def _is_in_group(self, request: HttpRequest, group_name="tira_reviewer") -> bool:
        """return True if the user is in the given disraptor group"""
        return group_name in request.headers.get("X-Disraptor-Groups", "").split(",")

    def _parse_tira_groups(self, groups: list[str]) -> dict[str, str]:
        """find all groups with 'tira_' prefix and return key and value of the group.
        Note: Groupnames should be in the format '[tira_]key[_value]'
        """
        for group in groups:
            g = group.split("_")
            if g[0] == "tira":
                try:
                    key = g[1]
                except IndexError:
                    continue
                try:
                    value = g[2]
                except IndexError:
                    value = None
                yield {"key": key, "value": value}

    def _get_user_groups(self, request: HttpRequest, group_type: str = "vm") -> list:
        """read groups from the disraptor groups header.
        @param group_type: {"vm", "org"}, indicate the class of groups.
        """
        all_groups = request.headers.get("X-Disraptor-Groups", "None").split(",")
        user_id = f"{request.headers.get('X-Disraptor-User', None)}-default"

        if group_type == "vm":  # if we check for groups of a virtual machine
            ret = [group["value"] for group in self._parse_tira_groups(all_groups) if group["key"] == "vm"]

            # Some discourse vm groups are created manually, so we have to ensure that they also have a vm
            for vm_id in ret:
                _ = model.get_vm(vm_id, create_if_none=True)

            return ret + [user_id]
        if group_type == "org":  # if we check for organizer groups of a user
            return [group["value"] for group in self._parse_tira_groups(all_groups) if group["key"] == "org"]

        raise ValueError(f"Can't handle group type {group_type}")

    @check_disraptor_token
    def get_role(
        self,
        request: HttpRequest,
        user_id: Optional[str] = None,
        vm_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        """Determine the role of the user on the requested page (determined by the given directives).
        This is a minimalistic implementation that suffices for the current features of TIRA.

        This implementation relies only on the request object, since disraptor takes care of the rest.

        Currently only checks: (1) is user admin, (2) otherwise, is user owner of the vm (ROLE_PARTICIPANT)
        """

        if (
            self._is_in_group(request, "admins")
            or self._is_in_group(request, "tira_reviewer")
            or self.is_admin_for_task(request)
        ):
            return self.ROLE_ADMIN

        user_groups = self._get_user_groups(request, group_type="vm")
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
    def get_user_id(self, request: HttpRequest):
        """public wrapper of _get_user_id that checks conditions"""
        return self._get_user_id(request)

    @check_disraptor_token
    def get_vm_id(self, request: HttpRequest, user_id=None):
        """return the vm_id of the first vm_group ("tira-vm-<vm_id>") found.
        If there is no vm-group, return "no-vm-assigned"
        """

        return self.get_vm_ids(request, user_id)[0]

    @check_disraptor_token
    def get_organizer_ids(self, request: HttpRequest, user_id=None):
        """return the organizer ids of all organizer teams that the user is found in ("tira-org-<vm_id>").
        If there is no vm-group, return the empty list
        """

        return self._get_user_groups(request, group_type="org")

    @check_disraptor_token
    def get_vm_ids(self, request: HttpRequest, user_id=None):
        """returns a list of all vm_ids of the all vm_groups ("tira-vm-<vm_id>") found.
        If there is no vm-group, a list with "no-vm-assigned" is returned
        """
        vms = self._get_user_groups(request)
        user_id = self._get_user_id(request)

        if user_id is None:
            return vms

        return vms if len(vms) >= 1 else [Authentication.get_default_vm_id(user_id)]

    def _create_discourse_vm_group(self, vm):
        """Create the vm group in the distaptor. Members of this group will be owners of the vm and
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
        return self.discourse_client.create_group(f"tira_vm_{vm['vm_id']}", group_bio, 2)

    def notify_organizers_of_new_participants(self, data, task_id):
        task = model.get_task(task_id)
        message = (
            """Dear Organizers """
            + task["organizer"]
            + """ of """
            + task_id
            + """

This message intends to inform you that there is a new registration for your task on """
            + task_id
            + """ has a new registration:

"""
            + json.dumps(data)
            + """

Best regards"""
        )

        self.discourse_client.write_message(
            f'New Registration to {task_id} by {data["group"]}',
            message,
            "tira_org_" + slugify(task["organizer"].lower()),
        )

    def create_group(self, vm):
        """Create the vm group in the distaptor. Members of this group will be owners of the vm and
            have all permissions.
        :param vm: a vm dict as returned by tira_model.get_vm
        """
        vm_group = self._create_discourse_vm_group(vm)
        invite_link = self.discourse_client.create_invite_link(vm_group)
        message = f"""Invite Mail: Please use this link to create your login for TIRA: {invite_link}.
                      After login to TIRA, you can find the credentials and usage examples for your
                      dedicated virtual machine {vm['vm_id']} here: https://www.tira.io/g/tira_vm_{vm['vm_id']}"""

        return message

    def create_organizer_group(self, organizer_name, user_name):
        group_bio = f"""Members of this team organize shared tasks in TIRA as  in shared tasks as {organizer_name}.
        <br><br>

        Please do not hesitate to design your page accorging to your needs."""

        group_id = self.discourse_client.create_group(f"tira_org_{organizer_name}", group_bio, 0)
        self.discourse_client.add_user_as_owner_to_group(group_id, user_name)

    def create_docker_group(self, team_name, user_name):
        group_bio = f"""Members of this team participate in shared tasks as {team_name}. <br><br>

        Please do not hesitate to design your team's page accorging to your needs."""

        group_id = self.discourse_client.create_group(f"tira_vm_{slugify(team_name)}", group_bio, 0)
        model.get_vm(team_name, create_if_none=True)
        self.discourse_client.add_user_as_owner_to_group(group_id, user_name)

    def user_is_organizer_for_endpoint(
        self,
        request,
        path,
        task_id,
        organizer_id_from_params,
        dataset_id_from_params,
        run_id_from_params,
        vm_id_from_params,
        role,
    ):
        if request is None or path is None:
            return False
        if not path.startswith("/"):
            path = "/" + path

        organizer_ids = self.get_organizer_ids(request)

        if path.startswith("/tira-admin/add-organizer/"):
            existing_organizer_ids = set([i["organizer_id"] for i in model.get_organizer_list()])
            orga_name = path.split("/tira-admin/add-organizer/")[1]

            return (
                len(orga_name.split("/")) == 1
                and orga_name not in existing_organizer_ids
                and organizer_id_from_params == orga_name
                and (
                    role == auth.ROLE_PARTICIPANT
                    or role == auth.ROLE_ADMIN
                    or role == auth.ROLE_USER
                    or role == auth.ROLE_TIRA
                )
            )

        if not organizer_ids or len(organizer_ids) < 1:
            return False

        organizer_id_from_dataset_id, organizer_id_from_run_id = None, None

        if run_id_from_params:
            try:
                dataset_id_from_run = model.get_run(run_id=run_id_from_params, vm_id=None, dataset_id=None)["dataset"]
                organizer_id_from_run_id = model.get_dataset(dataset_id_from_run)["organizer_id"]
            except Exception:
                return False

        if dataset_id_from_params:
            try:
                organizer_id_from_dataset_id = model.get_dataset(dataset_id_from_params).get("organizer_id", None)
            except Exception:
                return False

        potentially_inconsistent_ids = [
            organizer_id_from_params,
            organizer_id_from_dataset_id,
            organizer_id_from_run_id,
        ]
        if len(set([i for i in potentially_inconsistent_ids if i is not None])) > 1:
            return False

        task = None
        if task_id:
            try:
                task = model.get_task(task_id)
            except Exception:
                pass

        return (
            (task and "organizer_id" in task and task["organizer_id"] in organizer_ids)
            or (
                organizer_id_from_params
                and organizer_id_from_params in organizer_ids
                and path in set(f"/tira-admin/{i}/create-task" for i in organizer_ids)
            )
            or (
                organizer_id_from_run_id
                and organizer_id_from_run_id in organizer_ids
                and path.startswith(f"/task/{organizer_id_from_run_id}/vm/")
            )
            or (
                organizer_id_from_run_id
                and organizer_id_from_run_id in organizer_ids
                and organizer_id_from_dataset_id
                and path == f"/api/review/{dataset_id_from_params}/{vm_id_from_params}/{run_id_from_params}"
            )
            or (
                organizer_id_from_run_id
                and organizer_id_from_run_id in organizer_ids
                and organizer_id_from_dataset_id
                and path == f"/tira-admin/edit-review/{dataset_id_from_params}/{vm_id_from_params}/{run_id_from_params}"
            )
            or (
                organizer_id_from_dataset_id
                and organizer_id_from_dataset_id in organizer_ids
                and path == f"/tira-admin/edit-dataset/{dataset_id_from_params}"
            )
            or (
                organizer_id_from_dataset_id
                and organizer_id_from_dataset_id in organizer_ids
                and path == f"/tira-admin/delete-dataset/{dataset_id_from_params}"
            )
            or (
                organizer_id_from_dataset_id
                and organizer_id_from_dataset_id in organizer_ids
                and path.startswith("/data-download/")
                and path.endswith(f"/{dataset_id_from_params}.zip")
            )
        )


auth = Authentication(authentication_source=settings.DEPLOYMENT)
