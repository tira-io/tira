from django.test import TestCase
from utils_for_testing import route_to_test, assert_all_url_patterns_are_tested, execute_method_behind_url_and_return_status_code
from parameterized import parameterized
import json

ADMIN = 'tira_reviewer'
ROUTES_TO_TEST = [
    route_to_test(url_pattern='', params=None, groups=ADMIN, expected_status_code=200),
    route_to_test(url_pattern='task', params=None, groups=ADMIN, expected_status_code=200),
    route_to_test(url_pattern='tasks', params=None, groups=ADMIN, expected_status_code=200),
    route_to_test(url_pattern='task/<str:task_id>', params={'task_id': 'this-task-does-not-exist'}, groups=ADMIN, expected_status_code=404),
]

class TestAccessibilityOfEndpointsForAdminUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []

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

