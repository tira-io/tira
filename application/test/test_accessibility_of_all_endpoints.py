from api_access_matrix import ADMIN, GUEST, ORGANIZER, ORGANIZER_WRONG_TASK, PARTICIPANT, access_matrix_for_user
from django.test import TestCase
from parameterized import parameterized  # , parameterized_class
from utils_for_testing import (
    assert_all_url_patterns_are_tested,
    execute_method_behind_url_and_return_status_code,
    set_up_tira_environment,
)

# TODO: I leave this here since it should work (but does not); at some point (something like) this should replace all
# the other classes below (TestAccessibilityOfEndpointsForAdminUser, ...)
"""
@parameterized_class(("user",), [(ADMIN,), (GUEST,), (ORGANIZER,), (ORGANIZER_WRONG_TASK,), (PARTICIPANT,)])
class TestAccessibilityOfEndpoints(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_route(self):
        tested_urls = []
        for (
            url_pattern,
            method_bound_to_url_pattern,
            request,
            expected_status_code,
            hide_stdout,
        ) in access_matrix_for_user(self.user):
            status_code = execute_method_behind_url_and_return_status_code(
                method_bound_to_url_pattern, request, hide_stdout
            )

            self.assertEqual(
                status_code,
                expected_status_code,
                f"{request['request'].method} {url_pattern} yielded {status_code} for user '{self.user}'; Expected: {expected_status_code}",
            )

            tested_urls.append(url_pattern)

        assert_all_url_patterns_are_tested(tested_urls)

    @classmethod
    def tearDownClass(cls):
        pass
"""


class TestAccessibilityOfEndpointsForAdminUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []
        set_up_tira_environment()

    @parameterized.expand(access_matrix_for_user(ADMIN))
    def test_route(self, url_pattern, method_bound_to_url_pattern, request, expected_status_code, hide_stdout):
        status_code = execute_method_behind_url_and_return_status_code(
            method_bound_to_url_pattern, request, hide_stdout
        )

        self.assertEqual(
            status_code,
            expected_status_code,
            f"{request['request'].method} {url_pattern} yielded {status_code}; Expected: {expected_status_code}",
        )

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)


class TestAccessibilityOfEndpointsForGuestUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []
        set_up_tira_environment()

    @parameterized.expand(access_matrix_for_user(GUEST))
    def test_route(self, url_pattern, method_bound_to_url_pattern, request, expected_status_code, hide_stdout):
        status_code = execute_method_behind_url_and_return_status_code(
            method_bound_to_url_pattern, request, hide_stdout
        )

        self.assertEqual(
            status_code,
            expected_status_code,
            f"{request['request'].method} {url_pattern} yielded {status_code}; Expected: {expected_status_code}",
        )

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)


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

        self.assertEqual(
            status_code,
            expected_status_code,
            f"{request['request'].method} {url_pattern} yielded {status_code}; Expected: {expected_status_code}",
        )

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)


class TestAccessibilityOfEndpointsForOrganizerUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []
        set_up_tira_environment()

    @parameterized.expand(access_matrix_for_user(ORGANIZER))
    def test_route(self, url_pattern, method_bound_to_url_pattern, request, expected_status_code, hide_stdout):
        status_code = execute_method_behind_url_and_return_status_code(
            method_bound_to_url_pattern, request, hide_stdout
        )

        self.assertEqual(
            status_code,
            expected_status_code,
            f"{request['request'].method} {url_pattern} yielded {status_code}; Expected: {expected_status_code}",
        )

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)


class TestAccessibilityOfEndpointsForParticipantUser(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tested_urls = []
        set_up_tira_environment()

    @parameterized.expand(access_matrix_for_user(PARTICIPANT))
    def test_route(self, url_pattern, method_bound_to_url_pattern, request, expected_status_code, hide_stdout):
        status_code = execute_method_behind_url_and_return_status_code(
            method_bound_to_url_pattern, request, hide_stdout
        )

        self.assertEqual(
            status_code,
            expected_status_code,
            f"{request['request'].method} {url_pattern} yielded {status_code}; Expected: {expected_status_code}",
        )

        self.tested_urls += [url_pattern]

    @classmethod
    def tearDownClass(cls):
        assert_all_url_patterns_are_tested(cls.tested_urls)
