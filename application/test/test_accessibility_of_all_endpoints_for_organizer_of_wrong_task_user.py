from api_access_matrix import ORGANIZER_WRONG_TASK, access_matrix_for_user
from django.test import TestCase
from parameterized import parameterized
from utils_for_testing import (
    assert_all_url_patterns_are_tested,
    execute_method_behind_url_and_return_status_code,
    set_up_tira_environment,
)


class TestAccessibilityOfEndpointsForOrganizerWrongUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []
        set_up_tira_environment()

    @parameterized.expand(access_matrix_for_user(ORGANIZER_WRONG_TASK))
    def test_route(self, url_pattern, method_bound_to_url_pattern, request, expected_status_code, hide_stdout):
        status_code = execute_method_behind_url_and_return_status_code(
            method_bound_to_url_pattern, request, hide_stdout
        )

        assert (
            status_code == expected_status_code
        ), f"Expected response for url_pattern {url_pattern} is {expected_status_code}. But I got {status_code}."

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)
