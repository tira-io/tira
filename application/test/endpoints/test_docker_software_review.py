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
        self.assertEqual(
            ("approved", "rejected", "ok", "rev"),
            (ctx["code_review"], ctx["execution_review"], ctx["comment"], ctx["reviewer_id"]),
        )

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

    def test_automatic_review_without_concerns_releases_unless_rejected(self):
        vm = modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1")
        software = modeldb.DockerSoftware.objects.create(display_name="auto", vm=vm)
        auto = dict(docker_software=software, title="t", uploader_id="u", review_date="d")
        modeldb.DockerSoftwareAutomaticReview.objects.create(verdict="needs_human_review", **auto)
        self.assertFalse(software.is_released_for_users())
        modeldb.DockerSoftwareAutomaticReview.objects.create(verdict="no_concerns", **auto)
        self.assertTrue(software.is_released_for_users())
        modeldb.DockerSoftwareReview.objects.create(docker_software=software, code_review="rejected")
        self.assertFalse(software.is_released_for_users())


class TestSoftwareToReview(TestCase):
    def test_only_software_that_is_not_released_is_listed(self):
        from tira_app import tira_model

        set_up_tira_environment()
        vm = modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1")
        task = modeldb.Task.objects.get(task_id="shared-task-1")
        make = lambda name, **kwargs: modeldb.DockerSoftware.objects.create(
            display_name=name, vm=vm, task=task, **kwargs
        )
        pending, concerns, clean, _ = make("pending"), make("concerns"), make("clean"), make("deleted", deleted=True)
        auto = dict(title="t", uploader_id="u", review_date="d")
        modeldb.DockerSoftwareAutomaticReview.objects.create(
            docker_software=concerns, verdict="needs_human_review", **auto
        )
        modeldb.DockerSoftwareAutomaticReview.objects.create(docker_software=clean, verdict="no_concerns", **auto)

        mine = {"pending", "concerns", "clean", "deleted"}
        listed = {i["display_name"]: i for i in tira_model.get_software_to_review("shared-task-1")}
        listed = {k: v for k, v in listed.items() if k in mine}
        self.assertEqual({"pending", "concerns"}, set(listed))
        self.assertEqual(0, listed["pending"]["automatic_review_count"])
        self.assertEqual("needs_human_review", listed["concerns"]["latest_automatic_verdict"])
        self.assertEqual(
            {"pending", "concerns", "clean"},
            {i["display_name"] for i in tira_model.get_software_to_review("shared-task-1", include_reviewed=True)}
            & mine,
        )


class TestDockerSoftwareAutomaticReviews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        vm = modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1")
        cls.software = modeldb.DockerSoftware.objects.create(display_name="a", vm=vm)

    def setUp(self):
        from django.contrib.auth.models import User

        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_superuser("auto", "a@x.org", "pw"))
        self.url = f"/v1/admin/docker-software-automatic-reviews/{self.software.docker_software_id}"

    def _zip(self):
        import io
        import zipfile

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            z.writestr("review.json", "{}")
        buffer.name = "review.zip"
        buffer.seek(0)
        return buffer

    def _post(self, **kwargs):
        body = {"title": "t", "verdict": "no_concerns", "details": '{"llm": "m"}', "file": self._zip(), **kwargs}
        return self.client.post(self.url, body, format="multipart")

    def test_multiple_reviews_are_stored_with_zip_on_disk(self):
        from pathlib import Path

        from django.conf import settings

        first, second = self._post(title="first"), self._post(title="second", verdict="needs_human_review")
        self.assertEqual((201, 201), (first.status_code, second.status_code))

        reviews = self.client.get(self.url).json()["context"]["reviews"]
        self.assertEqual(["second", "first"], [r["title"] for r in reviews])
        self.assertEqual({"llm": "m"}, reviews[0]["details"])

        stored = modeldb.DockerSoftwareAutomaticReview.objects.get(id=reviews[0]["id"])
        self.assertTrue((Path(settings.TIRA_ROOT) / stored.archive_path).is_file())
        expected = f"software-reviews/{self.software.docker_software_id}/{stored.id}.zip"
        self.assertTrue(stored.archive_path.endswith(expected))

        download = self.client.get(f"{self.url}/{stored.id}/archive")
        self.assertEqual(200, download.status_code)
        self.assertTrue(b"".join(download.streaming_content).startswith(b"PK"))

    def test_invalid_uploads_are_rejected(self):
        self.assertEqual(400, self._post(verdict="x").status_code)
        self.assertEqual(400, self._post(title="").status_code)
        self.assertEqual(400, self._post(details="[]").status_code)
        self.assertEqual(400, self.client.post(self.url, {"title": "t", "verdict": "no_concerns"}).status_code)
