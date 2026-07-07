import json
import os
from time import sleep
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.request import QueryDict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from tira.check_format import _fmt
from utils_for_testing import dataset_1, method_for_url_pattern, set_up_tira_environment

import tira_app.model as modeldb
from tira_app.endpoints.vm_api import upload

task_function = method_for_url_pattern("api/task/<str:task_id>")
PARTICIPANT = "tira_vm_PARTICIPANT-FOR-TEST-1"


class TestUploadFieldConfiguration(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        cls.factory = APIRequestFactory()

    def _upload_request(self, data):
        request = self.factory.post(
            f"/task/shared-task-1/vm/PARTICIPANT-FOR-TEST-1/upload/{dataset_1}/new-submission",
            data=data,
            format="multipart",
            HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
            HTTP_X_DISRAPTOR_USER="ignored-user.",
            HTTP_X_DISRAPTOR_GROUPS=PARTICIPANT,
            CSRF_COOKIE="aasa",
        )
        request.GET = QueryDict("", mutable=True)
        return request

    def test_task_endpoint_returns_configured_upload_fields(self):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            upload_form_fields=json.dumps(
                [
                    {"name": "team_name", "display_name": "Team Name", "type": "text"},
                    {"name": "notes", "display_name": "Notes", "type": "textarea"},
                ]
            )
        )
        request = self.factory.get(
            "/api/task/shared-task-1",
            HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
            HTTP_X_DISRAPTOR_USER="ignored-user.",
            HTTP_X_DISRAPTOR_GROUPS=PARTICIPANT,
            CSRF_COOKIE="aasa",
        )
        request.GET = QueryDict("", mutable=True)

        response = task_function(request, task_id="shared-task-1")

        self.assertEqual(200, response.status_code)
        content = json.loads(response.content)
        self.assertEqual(
            [
                {"name": "team_name", "display_name": "Team Name", "type": "text"},
                {"name": "notes", "display_name": "Notes", "type": "textarea"},
            ],
            content["context"]["task"]["upload_form_fields"],
        )

    @patch("tira_app.endpoints.vm_api._run_evaluation")
    @patch("tira_app.endpoints.v1._anonymous.check_format_for_dataset", return_value=(_fmt.OK, "ok"))
    def test_upload_uses_default_metadata_when_task_has_no_configuration(self, _check_format, _run_evaluation):
        sleep(2)
        request = self._upload_request(
            {
                "display_name": "baseline-run",
                "description": "A baseline description",
                "file": SimpleUploadedFile("run.txt", b"baseline output", content_type="text/plain"),
            }
        )

        response = upload(
            request,
            task_id="shared-task-1",
            vm_id="PARTICIPANT-FOR-TEST-1",
            dataset_id=dataset_1,
            upload_id="new-submission",
        )

        self.assertEqual(200, response.status_code)
        created_upload = modeldb.Upload.objects.latest("id")
        self.assertEqual("baseline-run", created_upload.display_name)
        self.assertEqual("A baseline description", created_upload.description)
        self.assertEqual(
            {"run_id": "baseline-run", "description": "A baseline description"},
            created_upload.get_upload_metadata(),
        )

    @patch("tira_app.endpoints.vm_api._run_evaluation")
    @patch("tira_app.endpoints.v1._anonymous.check_format_for_dataset", return_value=(_fmt.OK, "ok"))
    def test_upload_stores_configured_metadata(self, _check_format, _run_evaluation):
        modeldb.Task.objects.filter(task_id="shared-task-1").update(
            upload_form_fields=json.dumps(
                [
                    {"name": "run_id", "display_name": "Run Identifier", "type": "text"},
                    {"name": "team_name", "display_name": "Team Name", "type": "text"},
                ]
            )
        )
        request = self._upload_request(
            {
                "upload_metadata": json.dumps({"run_id": "team-run", "team_name": "Group 42"}),
                "file": SimpleUploadedFile("run.txt", b"team output", content_type="text/plain"),
            }
        )

        response = upload(
            request,
            task_id="shared-task-1",
            vm_id="PARTICIPANT-FOR-TEST-1",
            dataset_id=dataset_1,
            upload_id="new-submission",
        )

        self.assertEqual(200, response.status_code)
        created_upload = modeldb.Upload.objects.latest("id")
        self.assertEqual("team-run", created_upload.display_name)
        self.assertEqual("", created_upload.description)
        self.assertEqual({"run_id": "team-run", "team_name": "Group 42"}, created_upload.get_upload_metadata())
