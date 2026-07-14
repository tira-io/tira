import io
import json
import os
import zipfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from utils_for_testing import dataset_1, dataset_2, set_up_tira_environment

import tira_app.model as modeldb
from tira_app.endpoints.v1._admin import upload_response
from tira_app.endpoints.vm_api import _mount_config_upload_field_name, run_execute_docker_software

PARTICIPANT = "tira_vm_PARTICIPANT-FOR-TEST-1"


class TestRunExecuteDockerSoftwareMountUploads(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        cls.factory = APIRequestFactory()
        cls.software = modeldb.DockerSoftware.objects.create(
            display_name="software-with-mounted-directory-upload",
            vm=modeldb.VirtualMachine.objects.get(vm_id="PARTICIPANT-FOR-TEST-1"),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
            mount_config=json.dumps({"primary-input": "ro", "secondary input": "rw"}),
            deleted=False,
        )
        cls.existing_run = modeldb.Run.objects.create(
            run_id="existing-run-for-mounted-directory",
            docker_software=cls.software,
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_1),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
        )
        cls.non_public_foreign_software = modeldb.DockerSoftware.objects.create(
            display_name="software-with-foreign-mounted-directory-run",
            vm=modeldb.VirtualMachine.objects.get(vm_id="participant-2"),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
            deleted=False,
        )
        cls.non_public_foreign_run = modeldb.Run.objects.create(
            run_id="non-public-foreign-mounted-directory-run",
            docker_software=cls.non_public_foreign_software,
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_2),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
        )
        modeldb.Review.objects.update_or_create(
            run=cls.non_public_foreign_run, defaults={"published": False, "blinded": True}
        )
        cls.public_foreign_software = modeldb.DockerSoftware.objects.create(
            display_name="software-with-public-mounted-directory-run",
            vm=modeldb.VirtualMachine.objects.get(vm_id="participant-2"),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
            deleted=False,
        )
        cls.public_foreign_run = modeldb.Run.objects.create(
            run_id="public-foreign-mounted-directory-run",
            docker_software=cls.public_foreign_software,
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_2),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
        )
        cls.public_foreign_evaluation = modeldb.Run.objects.create(
            run_id="public-foreign-mounted-directory-run-eval",
            input_run=cls.public_foreign_run,
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_2),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
        )
        modeldb.Review.objects.update_or_create(
            run=cls.public_foreign_evaluation, defaults={"published": True, "blinded": False}
        )

    def _request(self, data):
        request = self.factory.post(
            f"/grpc/shared-task-1/PARTICIPANT-FOR-TEST-1/run_execute/docker/{dataset_1}/{self.software.docker_software_id}/small-resources/none",
            data=data,
            format="multipart",
            HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
            HTTP_X_DISRAPTOR_USER="ignored-user.",
            HTTP_X_DISRAPTOR_GROUPS=PARTICIPANT,
            CSRF_COOKIE="aasa",
        )
        request.GET = QueryDict("", mutable=True)
        return request

    def _call_endpoint(self, data):
        request = self._request(data)
        return run_execute_docker_software(
            request,
            task_id="shared-task-1",
            vm_id="PARTICIPANT-FOR-TEST-1",
            dataset_id=dataset_1,
            docker_software_id=str(self.software.docker_software_id),
            docker_resources="small-resources",
            rerank_dataset="none",
        )

    def _valid_zip_upload(self, archive_name="mounted-directory.zip"):
        archive_bytes = io.BytesIO()

        with zipfile.ZipFile(archive_bytes, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("some-directory/file.txt", "content")

        return SimpleUploadedFile(archive_name, archive_bytes.getvalue(), content_type="application/zip")

    def test_requires_all_additional_mounted_directories(self):
        response = self._call_endpoint({"mount_config": json.dumps({"primary-input": "EMPTY_DIR"})})

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content, {"status": 1, "message": "Mounted directory is required: secondary input."}
        )

    def test_rejects_invalid_zip_uploads(self):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps({"primary-input": "UPLOAD_DIRECTORY", "secondary input": "EMPTY_DIR"}),
                _mount_config_upload_field_name("primary-input"): SimpleUploadedFile(
                    "mounted-directory.zip", b"not a valid zip archive", content_type="application/zip"
                ),
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content,
            {
                "status": 1,
                "message": "Uploaded file for mounted directory primary-input is not a valid zip archive.",
            },
        )

    @patch("tira_app.endpoints.vm_api.run_sandboxed_software")
    @patch("tira_app.endpoints.vm_api.add_job", return_value="job-123")
    @patch("tira_app.endpoints.vm_api._available_workers", return_value={"small-resources": object()})
    def test_valid_zip_upload_creates_uploaded_run_and_starts_execution(
        self, _available_workers, _add_job, run_sandboxed_software_mock
    ):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps({"primary-input": "UPLOAD_DIRECTORY", "secondary input": "EMPTY_DIR"}),
                _mount_config_upload_field_name("primary-input"): self._valid_zip_upload(),
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertJSONEqual(response.content, {"status": 0})
        self.assertEqual(
            1,
            modeldb.Upload.objects.filter(display_name="Mounted directory for primary-input").count(),
        )

        uploaded_run = modeldb.Run.objects.filter(upload__display_name="Mounted directory for primary-input").get()
        self.assertEqual(dataset_1, uploaded_run.input_dataset.dataset_id)
        dynamic_mounts = run_sandboxed_software_mock.call_args.args[12]
        self.assertEqual("OUTPUT_OF_OTHER_EXECUTION", dynamic_mounts["primary-input"]["source"])
        self.assertEqual(uploaded_run.run_id, dynamic_mounts["primary-input"]["run_id"])

    def test_requires_run_id_for_previous_execution_mount(self):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps(
                    {
                        "primary-input": {"source": "OUTPUT_OF_OTHER_EXECUTION"},
                        "secondary input": "EMPTY_DIR",
                    }
                )
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content,
            {
                "status": 1,
                "message": "Run ID is required for mounted directory: primary-input.",
            },
        )

    def test_rejects_unknown_run_id_for_previous_execution_mount(self):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps(
                    {
                        "primary-input": {
                            "source": "OUTPUT_OF_OTHER_EXECUTION",
                            "run_id": "does-not-exist",
                        },
                        "secondary input": "EMPTY_DIR",
                    }
                )
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content,
            {
                "status": 1,
                "message": "There is no run with id does-not-exist.",
            },
        )

    @patch("tira_app.endpoints.vm_api.run_sandboxed_software")
    @patch("tira_app.endpoints.vm_api.add_job", return_value="job-123")
    @patch("tira_app.endpoints.vm_api._available_workers", return_value={"small-resources": object()})
    def test_valid_run_id_starts_execution(self, _available_workers, _add_job, run_sandboxed_software_mock):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps(
                    {
                        "primary-input": {
                            "source": "OUTPUT_OF_OTHER_EXECUTION",
                            "run_id": self.existing_run.run_id,
                        },
                        "secondary input": "EMPTY_DIR",
                    }
                )
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertJSONEqual(response.content, {"status": 0})
        dynamic_mounts = run_sandboxed_software_mock.call_args.args[12]
        self.assertEqual(self.existing_run.run_id, dynamic_mounts["primary-input"]["run_id"])

    def test_rejects_non_public_run_from_other_vm_and_dataset(self):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps(
                    {
                        "primary-input": {
                            "source": "OUTPUT_OF_OTHER_EXECUTION",
                            "run_id": self.non_public_foreign_run.run_id,
                        },
                        "secondary input": "EMPTY_DIR",
                    }
                )
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content,
            {
                "status": 1,
                "message": (
                    f"Run {self.non_public_foreign_run.run_id} must be from your own submission on this dataset"
                    " or published by administrators."
                ),
            },
        )

    @patch("tira_app.endpoints.vm_api.run_sandboxed_software")
    @patch("tira_app.endpoints.vm_api.add_job", return_value="job-123")
    @patch("tira_app.endpoints.vm_api._available_workers", return_value={"small-resources": object()})
    def test_accepts_public_run_from_other_vm_and_dataset(
        self, _available_workers, _add_job, run_sandboxed_software_mock
    ):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps(
                    {
                        "primary-input": {
                            "source": "OUTPUT_OF_OTHER_EXECUTION",
                            "run_id": self.public_foreign_run.run_id,
                        },
                        "secondary input": "EMPTY_DIR",
                    }
                )
            }
        )

        self.assertEqual(202, response.status_code)
        self.assertJSONEqual(response.content, {"status": 0})
        dynamic_mounts = run_sandboxed_software_mock.call_args.args[12]
        self.assertEqual(self.public_foreign_run.run_id, dynamic_mounts["primary-input"]["run_id"])

    def test_rejects_non_public_run_from_other_dataset(self):
        self_owned_run = modeldb.Run.objects.create(
            run_id="other-dataset-mounted-directory-run",
            docker_software=self.software,
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_2),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
        )
        modeldb.Review.objects.update_or_create(run=self_owned_run, defaults={"published": False, "blinded": True})

        response = self._call_endpoint(
            {
                "mount_config": json.dumps(
                    {
                        "primary-input": {
                            "source": "OUTPUT_OF_OTHER_EXECUTION",
                            "run_id": self_owned_run.run_id,
                        },
                        "secondary input": "EMPTY_DIR",
                    }
                )
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content,
            {
                "status": 1,
                "message": (
                    f"Run {self_owned_run.run_id} must be from your own submission on this dataset"
                    " or published by administrators."
                ),
            },
        )


class TestUploadResponseDynamicMounts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        set_up_tira_environment()
        cls.factory = APIRequestFactory()
        cls.task = modeldb.Task.objects.get(task_id="shared-task-1")
        cls.task.featured = True
        cls.task.save(update_fields=["featured"])

    def test_upload_response_persists_dynamic_mounts_on_run(self):
        dataset = modeldb.Dataset.objects.get(dataset_id=dataset_1)
        dataset.format = json.dumps(["arbitrary"])
        dataset.save(update_fields=["format"])

        run = modeldb.Run.objects.create(
            run_id="run-with-dynamic-mounts",
            docker_software=modeldb.DockerSoftware.objects.filter(vm__vm_id="PARTICIPANT-FOR-TEST-1").first(),
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_1),
            task=self.task,
        )
        modeldb.RunningProcesses.objects.create(
            uuid="job-with-dynamic-mounts",
            task="shared-task-1",
            vm_id="PARTICIPANT-FOR-TEST-1",
            dataset_id=dataset_1,
            details=json.dumps(
                {
                    "job_config": {
                        "dynamic_mounts": {"primary-input": {"source": "OUTPUT_OF_OTHER_EXECUTION", "run_id": "abc"}}
                    }
                }
            ),
        )
        request = self.factory.post(
            "/v1/admin/upload-response/PARTICIPANT-FOR-TEST-1/job-with-dynamic-mounts",
            data={"file": SimpleUploadedFile("run.zip", b"ignored", content_type="application/zip")},
            format="multipart",
            HTTP_X_DISRAPTOR_APP_SECRET_KEY=os.getenv("DISRAPTOR_APP_SECRET_KEY"),
            HTTP_X_DISRAPTOR_USER="ignored-user.",
            HTTP_X_DISRAPTOR_GROUPS="admins",
        )

        with patch("tira_app.endpoints.v1._admin._extract_run_from_archive", return_value=run.run_id), patch(
            "tira_app.endpoints.v1._admin._run_evaluation"
        ):
            response = upload_response(request, vm_id="PARTICIPANT-FOR-TEST-1", job_id="job-with-dynamic-mounts")

        self.assertEqual(200, response.status_code)
        run.refresh_from_db()
        self.assertEqual(
            {"primary-input": {"source": "OUTPUT_OF_OTHER_EXECUTION", "run_id": "abc"}},
            json.loads(run.dynamic_mounts),
        )
