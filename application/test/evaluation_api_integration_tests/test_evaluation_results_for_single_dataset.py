from django.test import TestCase
from api_access_matrix import GUEST, ADMIN
from utils_for_testing import dataset_1, dataset_2, method_for_url_pattern, mock_request, set_up_tira_environment

url = 'api/evaluations/<str:task_id>/<str:dataset_id>'
evaluations_function = method_for_url_pattern(url)


class TestEvaluationResults(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_for_non_existing_task_and_dataset(self):
        # Arrange
        request = mock_request(GUEST, url)

        # Act
        actual = evaluations_function(request, task_id='does-not-exist', dataset_id='does-not-exist')

        # Assert
        self.verify_as_json(actual, 'non_existing_task_and_dataset.json')

    def test_for_existing_task_and_dataset_with_few_evaluations(self):
        # Arrange
        request = mock_request(GUEST, url)

        # Act
        actual = evaluations_function(request, task_id='shared-task-1', dataset_id=dataset_1)

        # Assert
        self.verify_as_json(actual, 'existing_task_and_dataset_with_few_evaluations.json')

    def test_for_existing_task_and_dataset_with_few_evaluations_including_blinded(self):
        # Arrange
        request = mock_request(ADMIN, url)

        # Act
        actual = evaluations_function(request, task_id='shared-task-1', dataset_id=dataset_1)

        # Assert
        self.verify_as_json(actual, 'test_for_existing_task_and_dataset_with_few_evaluations_including_blinded.json')

    def test_for_existing_task_and_dataset_with_little_evaluations(self):
        # Arrange
        request = mock_request(GUEST, url)

        # Act
        actual = evaluations_function(request, task_id='shared-task-1', dataset_id=dataset_2)

        # Assert
        self.verify_as_json(actual, 'existing_task_and_dataset_with_little_evaluations.json')

    def test_for_existing_task_and_dataset_with_little_evaluations_including_blinded(self):
        # Arrange
        request = mock_request(ADMIN, url)

        # Act
        actual = evaluations_function(request, task_id='shared-task-1', dataset_id=dataset_2)

        # Assert
        self.verify_as_json(actual, 'test_for_existing_task_and_dataset_with_little_evaluations_including_blinded.json')

    def verify_as_json(self, actual, test_name):
        from approvaltests import verify_as_json
        from approvaltests.core.options import Options
        from approvaltests.namer.cli_namer import CliNamer
        import json
        content = json.loads(actual.content)

        if 'context' in content and 'dataset_id' in content['context']:
            content['context']['dataset_id'] = content['context']['dataset_id'].split('-20')[0]

        self.assertEquals(200, actual.status_code)
        verify_as_json(content, options=Options().with_namer(CliNamer(test_name)))

    @classmethod
    def tearDownClass(cls):
        pass

