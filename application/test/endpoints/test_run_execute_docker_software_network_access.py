import json
import os
from unittest.mock import patch

from django.http import QueryDict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from utils_for_testing import dataset_1, set_up_tira_environment

import tira_app.model as modeldb
from tira_app.endpoints.vm_api import run_execute_docker_software

PARTICIPANT = "tira_vm_PARTICIPANT-FOR-TEST-1"
TASK_ID = "shared-task-1"


class TestRunExecuteDockerSoftwareNetworkAccess(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        cls.factory = APIRequestFactory()
        cls.vm = modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1")
        cls.task = modeldb.Task.objects.get(task_id=TASK_ID)

    def setUp(self):
        self._set_task_flag(False)

    def _set_task_flag(self, value):
        modeldb.Task.objects.filter(task_id=TASK_ID).update(allow_network_access_on_request=value)

    def _software(self, allow_network_access_on_request):
        return modeldb.DockerSoftware.objects.create(
            display_name="software-network-" + str(allow_network_access_on_request),
            vm=self.vm,
            task=self.task,
            allow_network_access_on_request=allow_network_access_on_request,
            deleted=False,
        )

    def _call_endpoint(self, software, data):
        request = self.factory.post(
            f"/grpc/{TASK_ID}/PARTICIPANT-FOR-TEST-1/run_execute/docker/{dataset_1}/{software.docker_software_id}/small-resources/none",
            data=data,
            format="multipart",
            HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
            HTTP_X_DISRAPTOR_USER="ignored-user.",
            HTTP_X_DISRAPTOR_GROUPS=PARTICIPANT,
            CSRF_COOKIE="aasa",
        )
        request.GET = QueryDict("", mutable=True)
        return run_execute_docker_software(
            request,
            task_id=TASK_ID,
            vm_id="PARTICIPANT-FOR-TEST-1",
            dataset_id=dataset_1,
            docker_software_id=str(software.docker_software_id),
            docker_resources="small-resources",
            rerank_dataset="none",
        )

    def test_network_access_is_rejected_if_software_does_not_allow_it(self):
        self._set_task_flag(True)
        response = self._call_endpoint(self._software(False), {"allow_network_access": json.dumps(True)})

        self.assertEqual(1, json.loads(response.content)["status"])
        self.assertIn("does not allow", json.loads(response.content)["message"])

    def test_network_access_is_rejected_if_task_does_not_allow_it(self):
        response = self._call_endpoint(self._software(True), {"allow_network_access": json.dumps(True)})

        self.assertEqual(1, json.loads(response.content)["status"])
        self.assertIn("does not allow", json.loads(response.content)["message"])

    @patch("tira_app.endpoints.vm_api.run_sandboxed_software")
    @patch("tira_app.endpoints.vm_api.add_job", return_value="job-123")
    @patch("tira_app.endpoints.vm_api._available_workers", return_value={"small-resources": object()})
    def test_network_access_is_forwarded_to_worker_if_requested_and_allowed(self, _workers, _add_job, run_mock):
        self._set_task_flag(True)
        response = self._call_endpoint(self._software(True), {"allow_network_access": json.dumps(True)})

        self.assertEqual(202, response.status_code)
        self.assertIs(True, run_mock.call_args.args[13])

    @patch("tira_app.endpoints.vm_api.run_sandboxed_software")
    @patch("tira_app.endpoints.vm_api.add_job", return_value="job-123")
    @patch("tira_app.endpoints.vm_api._available_workers", return_value={"small-resources": object()})
    def test_network_access_is_granted_automatically_if_software_and_task_allow_it(self, _workers, _add_job, run_mock):
        self._set_task_flag(True)
        response = self._call_endpoint(self._software(True), {})

        self.assertEqual(202, response.status_code)
        self.assertIs(True, run_mock.call_args.args[13])

    @patch("tira_app.endpoints.vm_api.run_sandboxed_software")
    @patch("tira_app.endpoints.vm_api.add_job", return_value="job-123")
    @patch("tira_app.endpoints.vm_api._available_workers", return_value={"small-resources": object()})
    def test_network_access_is_disabled_if_software_does_not_allow_it(self, _workers, _add_job, run_mock):
        self._set_task_flag(True)
        response = self._call_endpoint(self._software(False), {})

        self.assertEqual(202, response.status_code)
        self.assertIs(False, run_mock.call_args.args[13])
