from django.test import TestCase
from rest_framework.test import APIClient
from utils_for_testing import set_up_tira_environment

import tira_app.model as modeldb


class TestDockerSoftwareReview(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        vm = modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1")
        cls.software = modeldb.DockerSoftware.objects.create(display_name="s", vm=vm)

    def setUp(self):
        from django.contrib.auth.models import User

        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_superuser("rev", "r@x.org", "pw"))
        self.url = f"/v1/admin/docker-software-review/{self.software.docker_software_id}"

    def test_default_is_pending(self):
        ctx = self.client.get(self.url).json()["context"]
        self.assertEqual(("pending", "pending", ""), (ctx["code_review"], ctx["execution_review"], ctx["comment"]))

    def test_put_stores_review(self):
        body = {"code_review": "approved", "execution_review": "rejected", "comment": "ok"}
        self.assertEqual(200, self.client.put(self.url, body, format="json").status_code)
        ctx = self.client.get(self.url).json()["context"]
        self.assertEqual(("approved", "rejected", "ok", "rev"), (
            ctx["code_review"], ctx["execution_review"], ctx["comment"], ctx["reviewer_id"]))

    def test_invalid_status_rejected(self):
        body = {"code_review": "x", "execution_review": "approved", "comment": ""}
        self.assertEqual(400, self.client.put(self.url, body, format="json").status_code)


class TestReleaseForUsers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        vm = modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1")
        cls.software = modeldb.DockerSoftware.objects.create(display_name="r", vm=vm)

    def test_software_without_review_is_not_released(self):
        self.assertFalse(self.software.is_released_for_users())

    def test_release_requires_both_aspects_approved(self):
        review = modeldb.DockerSoftwareReview.objects.create(docker_software=self.software, code_review="approved")
        self.assertFalse(self.software.is_released_for_users())
        review.execution_review = "approved"
        review.save()
        self.assertTrue(self.software.is_released_for_users())
