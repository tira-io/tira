from django.test import TestCase
from utils_for_testing import route_to_test, assert_all_url_patterns_are_tested, execute_method_behind_url_and_return_status_code
from parameterized import parameterized
import json
from tira.tira_model import model as tira_model
from datetime import datetime

#Used for some tests
now = datetime.now().strftime("%Y%m%d")

ADMIN = 'tira_reviewer'
ROUTES_TO_TEST = [
    route_to_test(url_pattern='', params=None, groups=ADMIN, expected_status_code=200),
    route_to_test(url_pattern='task', params=None, groups=ADMIN, expected_status_code=200),
    route_to_test(url_pattern='tasks', params=None, groups=ADMIN, expected_status_code=200),
    route_to_test(url_pattern='task/<str:task_id>', params={'task_id': 'this-task-does-not-exist'}, groups=ADMIN, expected_status_code=404),
    route_to_test(url_pattern='task/<str:task_id>', params={'task_id': 'shared-task-1'}, groups=ADMIN, expected_status_code=200),
    
    route_to_test(url_pattern='task/<str:task_id>/dataset/<str:dataset_id>', params={'task_id': 'shared-task-1', 'dataset_id': 'this-dataset-does-not-exist'}, groups=ADMIN, expected_status_code=404),
    
    route_to_test(url_pattern='task/<str:task_id>/dataset/<str:dataset_id>', params={'task_id': 'shared-task-1', 'dataset_id': f'dataset-1-{now}-training'}, groups=ADMIN, expected_status_code=200),
    
]

class TestAccessibilityOfEndpointsForAdminUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []
        tira_model.edit_organizer('organizer', 'organizer', 'years', 'web', [])
        tira_model.add_vm('master-vm-for-task-1', 'user_name', 'initial_user_password', 'ip', 'host', '123', '123')
        tira_model.create_task('shared-task-1', 'task_name', 'task_description', False, 'master-vm-for-task-1', 'organizer',
                'website', False, False, False, 'help_command', '', '')
        tira_model.add_dataset('shared-task-1', 'dataset-1', 'training', 'dataset-1', 'upload-name')

    @parameterized.expand(ROUTES_TO_TEST)
    def test_route(self, url_pattern, method_bound_to_url_pattern, request, expected_status_code):
        status_code = execute_method_behind_url_and_return_status_code(
            method_bound_to_url_pattern,
            request
        )
        
        assert status_code == expected_status_code, \
            f'Expected response for url_pattern {url_pattern} is {expected_status_code}. But I got {status_code}'

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)    

