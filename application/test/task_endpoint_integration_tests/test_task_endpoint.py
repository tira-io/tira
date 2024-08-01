from api_access_matrix import ADMIN, GUEST
from django.test import TestCase
from utils_for_testing import method_for_url_pattern, mock_request, set_up_tira_environment

task_function = method_for_url_pattern("api/task/<str:task_id>")
submission_function = method_for_url_pattern(
    "api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>"
)


class TestTaskEndpoint(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_response_for_non_existing_task(self):
        # Arrange
        request = mock_request(GUEST, "api/task/<str:task_id>")

        # Act
        actual = task_function(request, task_id="task-does-not-exist")

        # Assert
        self.verify_as_json(actual, "response_for_non_existing_task")

    def test_result_for_existing_task(self):
        # Arrange
        request = mock_request(GUEST, "api/task/<str:task_id>")

        # Act
        actual = task_function(request, task_id="task-of-organizer-1")

        # Assert
        self.verify_as_json(actual, "result_for_existing_task")

    def test_upload_submissions_for_non_existing_task(self):
        # Arrange
        request = mock_request(ADMIN, "api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>")

        # Act
        actual = submission_function(
            request, task_id="does-not-exist", user_id="does-not-exist", submission_type="upload"
        )

        # Assert
        self.verify_as_json(actual, "result_upload_submissions_for_non_existing_task")

    def test_software_submissions_for_existing_task(self):
        # Arrange
        request = mock_request(ADMIN, "api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>")

        # Act
        actual = submission_function(
            request, task_id="shared-task-1", user_id="PARTICIPANT-FOR-TEST-1", submission_type="docker"
        )

        # Assert
        self.verify_as_json(actual, "result_software_submissions_for_existing_task")

    def test_upload_submissions_for_existing_task(self):
        # Arrange
        request = mock_request(ADMIN, "api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>")

        # Act
        actual = submission_function(
            request, task_id="shared-task-1", user_id="PARTICIPANT-FOR-TEST-1", submission_type="upload"
        )

        # Assert
        self.verify_as_json(actual, "result_upload_submissions_for_existing_task")

    def test_software_submissions_for_existing_task_and_user_without_software(self):
        # Arrange
        request = mock_request(ADMIN, "api/submissions-for-task/<str:task_id>/<str:user_id>/<str:submission_type>")

        # Act
        actual = submission_function(
            request, task_id="shared-task-1", user_id="PARTICIPANT-WITHOUT_SOFTWARE", submission_type="docker"
        )

        # Assert
        self.verify_as_json(actual, "result_software_submissions_for_existing_task_and_user_without_software")

    def verify_as_json(self, actual, test_name):
        import json

        from approvaltests import verify_as_json
        from approvaltests.core.options import Options
        from approvaltests.namer.cli_namer import CliNamer

        self.assertEqual(200, actual.status_code)
        content = json.loads(actual.content)

        if "context" in content:
            for d in content["context"]["datasets"]:
                d["dataset_id"] = d["dataset_id"].split("-20")[0]
                d["display_name"] = d["display_name"].split("-20")[0]

        verify_as_json(content, options=Options().with_namer(CliNamer(test_name)))

    @classmethod
    def tearDownClass(cls):
        pass
