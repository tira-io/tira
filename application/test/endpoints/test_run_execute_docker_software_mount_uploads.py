import io
import json
import os
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from utils_for_testing import dataset_1, set_up_tira_environment

import tira_app.model as modeldb
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

    def test_valid_zip_upload_returns_not_yet_implemented_message(self):
        response = self._call_endpoint(
            {
                "mount_config": json.dumps({"primary-input": "UPLOAD_DIRECTORY", "secondary input": "EMPTY_DIR"}),
                _mount_config_upload_field_name("primary-input"): self._valid_zip_upload(),
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content,
            {
                "status": 1,
                "message": "Uploading additional mounted directories via the web UI is not yet implemented on the server side. The uploaded zip archive was validated successfully.",
            },
        )

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

    def test_valid_run_id_returns_not_yet_implemented_message(self):
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

        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content,
            {
                "status": 1,
                "message": "Mounting additional directories from another execution via the web UI is not yet implemented on the server side. The provided run ID was validated successfully.",
            },
        )
