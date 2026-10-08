import json
import os
import zipfile
from io import BytesIO

from django.http.request import QueryDict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from utils_for_testing import method_for_url_pattern, set_up_tira_environment

import tira_app.model as modeldb
import tira_app.tira_model as tira_model
from tira_app.endpoints.task_exports import task_export

task_function = method_for_url_pattern("api/task/<str:task_id>")
ADMIN = "admins"
PARTICIPANT = "tira_vm_PARTICIPANT-FOR-TEST-1"


def _request(groups, method="get"):
    factory = APIRequestFactory()
    request = getattr(factory, method)(
        "/ignored",
        HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
        HTTP_X_DISRAPTOR_USER="ignored-user.",
        HTTP_X_DISRAPTOR_GROUPS=groups,
        CSRF_COOKIE="aasa",
    )
    request.GET = QueryDict("", mutable=True)
    return request


class TestNormalizeExportButtons(TestCase):
    def test_normalize_export_buttons_accepts_valid_configuration(self):
        buttons = [{"display_name": "Example Export", "value": "example-zip-export"}]

        self.assertEqual(buttons, modeldb.normalize_export_buttons(buttons))

    def test_normalize_export_buttons_accepts_json_string(self):
        buttons = [{"display_name": "Example Export", "value": "example-zip-export"}]

        self.assertEqual(buttons, modeldb.normalize_export_buttons(json.dumps(buttons)))

    def test_normalize_export_buttons_rejects_unknown_value(self):
        buttons = [{"display_name": "Not Implemented", "value": "does-not-exist"}]

        self.assertIsNone(modeldb.normalize_export_buttons(buttons))

    def test_normalize_export_buttons_rejects_missing_display_name(self):
        buttons = [{"value": "example-zip-export"}]

        self.assertIsNone(modeldb.normalize_export_buttons(buttons))

    def test_normalize_export_buttons_rejects_malformed_entries(self):
        self.assertIsNone(modeldb.normalize_export_buttons(["not-a-dict"]))

    def test_normalize_export_buttons_rejects_non_list(self):
        self.assertIsNone(modeldb.normalize_export_buttons({"display_name": "x", "value": "example-zip-export"}))

    def test_normalize_export_buttons_handles_none_and_empty(self):
        self.assertIsNone(modeldb.normalize_export_buttons(None))
        self.assertIsNone(modeldb.normalize_export_buttons(""))
        self.assertIsNone(modeldb.normalize_export_buttons([]))


class TestTaskExportButtonsPersistence(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def test_edit_task_persists_export_buttons(self):
        tira_model.edit_task(
            "shared-task-1",
            "Shared Task 1",
            "Updated description",
            False,
            "master-vm-for-task-1",
            "organizer",
            "website",
            False,
            False,
            False,
            allowed_task_teams="",
            export_buttons=[{"display_name": "Example Export", "value": "example-zip-export"}],
        )

        task = modeldb.Task.objects.get(task_id="shared-task-1")
        self.assertEqual(
            [{"display_name": "Example Export", "value": "example-zip-export"}],
            task.get_export_buttons(),
        )

    def test_edit_task_drops_invalid_export_buttons(self):
        tira_model.edit_task(
            "shared-task-1",
            "Shared Task 1",
            "Updated description",
            False,
            "master-vm-for-task-1",
            "organizer",
            "website",
            False,
            False,
            False,
            allowed_task_teams="",
            export_buttons=[{"display_name": "Bad", "value": "not-registered"}],
        )

        task = modeldb.Task.objects.get(task_id="shared-task-1")
        self.assertIsNone(task.get_export_buttons())

    def test_task_endpoint_returns_configured_export_buttons(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            export_buttons=json.dumps([{"display_name": "Example Export", "value": "example-zip-export"}])
        )

        response = task_function(_request(PARTICIPANT), task_id="shared-task-1")

        self.assertEqual(200, response.status_code)
        content = json.loads(response.content)
        self.assertEqual(
            [{"display_name": "Example Export", "value": "example-zip-export"}],
            content["context"]["task"]["export_buttons"],
        )


class TestTaskExportEndpoint(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()

    def setUp(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            export_buttons=json.dumps([{"display_name": "Example Export", "value": "example-zip-export"}])
        )

    def test_admin_can_download_configured_export(self):
        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="example-zip-export"
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/zip", response["Content-Type"])
        zipf = zipfile.ZipFile(BytesIO(response.content))
        self.assertEqual(["export.txt"], zipf.namelist())
        self.assertIn("shared-task-1", zipf.read("export.txt").decode())

    def test_admin_gets_404_for_unconfigured_value(self):
        response = task_export(
            _request(ADMIN), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="not-configured-value"
        )

        self.assertEqual(404, response.status_code)

    def test_non_admin_participant_of_other_vm_is_denied(self):
        response = task_export(
            _request(PARTICIPANT),
            task_id="shared-task-1",
            vm_id="master-vm-for-task-1",
            value="example-zip-export",
        )

        self.assertNotEqual(200, response.status_code)

    def test_guest_is_redirected_to_login(self):
        response = task_export(
            _request(""), task_id="shared-task-1", vm_id="master-vm-for-task-1", value="example-zip-export"
        )

        self.assertEqual(302, response.status_code)
