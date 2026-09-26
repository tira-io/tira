import json
import os

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from utils_for_testing import dataset_1, set_up_tira_environment

import tira_app.model as modeldb
from tira_app import tira_model as model
from tira_app.endpoints.vm_api import docker_software_details

PARTICIPANT = "PARTICIPANT-FOR-TEST-1"


class TestTryRunMetadataOnDockerSoftware(TestCase):
    """Tests for the try_run_metadata that is exposed on docker-software details for admins (see
    HybridDatabase.get_docker_software/_docker_software_to_dict and vm_api.docker_software_details)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        cls.factory = APIRequestFactory()

        cls.anonymous_upload = modeldb.AnonymousUploads.objects.create(
            uuid="some-try-run-uuid",
            dataset=modeldb.Dataset.objects.get(dataset_id=dataset_1),
            has_metadata=True,
            metadata_git_repo="https://github.com/example/repo",
            metadata_has_notebook=False,
        )
        cls.software_with_try_run_metadata = modeldb.DockerSoftware.objects.create(
            display_name="software-with-try-run-metadata",
            vm=modeldb.VirtualMachine.objects.get(vm_id=PARTICIPANT),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
            try_run_metadata=cls.anonymous_upload,
            deleted=False,
        )
        cls.software_without_try_run_metadata = modeldb.DockerSoftware.objects.create(
            display_name="software-without-try-run-metadata",
            vm=modeldb.VirtualMachine.objects.get(vm_id=PARTICIPANT),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
            deleted=False,
        )

    # ------------------------------------------------------------------
    # HybridDatabase.get_docker_software (model layer)
    # ------------------------------------------------------------------

    def test_try_run_metadata_is_omitted_by_default(self):
        ret = model.get_docker_software(self.software_with_try_run_metadata.docker_software_id)

        self.assertIsNone(ret["try_run_metadata"])

    def test_try_run_metadata_is_omitted_when_explicitly_disabled(self):
        ret = model.get_docker_software(
            self.software_with_try_run_metadata.docker_software_id, include_try_run_metadata=False
        )

        self.assertIsNone(ret["try_run_metadata"])

    def test_try_run_metadata_is_included_when_requested_and_available(self):
        ret = model.get_docker_software(
            self.software_with_try_run_metadata.docker_software_id, include_try_run_metadata=True
        )

        self.assertIsNotNone(ret["try_run_metadata"])
        self.assertEqual("some-try-run-uuid", ret["try_run_metadata"]["uuid"])
        self.assertEqual(dataset_1, ret["try_run_metadata"]["dataset_id"])
        self.assertTrue(ret["try_run_metadata"]["has_metadata"])
        self.assertEqual("https://github.com/example/repo", ret["try_run_metadata"]["metadata_git_repo"])
        self.assertFalse(ret["try_run_metadata"]["metadata_has_notebook"])

    def test_try_run_metadata_is_none_when_requested_but_not_available(self):
        ret = model.get_docker_software(
            self.software_without_try_run_metadata.docker_software_id, include_try_run_metadata=True
        )

        self.assertIsNone(ret["try_run_metadata"])

    # ------------------------------------------------------------------
    # docker_software_details endpoint (admin-only gating)
    # ------------------------------------------------------------------

    def _request(self, docker_software_id, groups=""):
        request = self.factory.get(
            f"/api/docker-softwares-details/{PARTICIPANT}/{docker_software_id}",
            HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
            HTTP_X_DISRAPTOR_USER="some-participant-user",
            HTTP_X_DISRAPTOR_GROUPS=groups,
        )
        return docker_software_details(
            request, vm_id=PARTICIPANT, docker_software_id=str(docker_software_id)
        )

    def test_admin_sees_try_run_metadata_in_endpoint_response(self):
        response = self._request(self.software_with_try_run_metadata.docker_software_id, groups="admins")

        context = json.loads(response.content)["context"]
        self.assertIsNotNone(context["docker_software_details"]["try_run_metadata"])
        self.assertEqual("some-try-run-uuid", context["docker_software_details"]["try_run_metadata"]["uuid"])

    def test_non_admin_does_not_see_try_run_metadata_in_endpoint_response(self):
        response = self._request(
            self.software_with_try_run_metadata.docker_software_id, groups=f"tira_vm_{PARTICIPANT}"
        )

        context = json.loads(response.content)["context"]
        self.assertIsNone(context["docker_software_details"]["try_run_metadata"])
