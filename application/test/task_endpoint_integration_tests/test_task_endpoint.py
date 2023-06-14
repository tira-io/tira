from django.test import TestCase
from api_access_matrix import GUEST
from utils_for_testing import method_for_url_pattern, mock_request, set_up_tira_environment

task_function = method_for_url_pattern('api/task/<str:task_id>')


class TestTaskEndpoint(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_response_for_non_existing_task(self):
        # Arrange
        request = mock_request(GUEST, 'api/task/<str:task_id>')

        # Act
        actual = task_function(request, task_id='task-does-not-exist')

        # Assert
        self.verify_as_json(actual, 'response_for_non_existing_task')

    def test_result_for_existing_task(self):
        # Arrange
        request = mock_request(GUEST, 'api/task/<str:task_id>')

        # Act
        actual = task_function(request, task_id='task-of-organizer-1')

        # Assert
        self.verify_as_json(actual, 'result_for_existing_task')

    def verify_as_json(self, actual, test_name):
        from approvaltests import verify_as_json
        from approvaltests.core.options import Options
        from approvaltests.namer.cli_namer import CliNamer
        import json

        self.assertEquals(200, actual.status_code)
        verify_as_json(json.loads(actual.content), options=Options().with_namer(CliNamer(test_name)))


    @classmethod
    def tearDownClass(cls):
        pass

