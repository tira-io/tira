from django.test import TestCase
from utils_for_testing import mock_request, set_up_tira_environment

from tira_app.authentication import auth

submit_url_task_1 = "submit/task-of-organizer-1"
overview_url_task_1 = "task-overview/task-of-organizer-1"

submit_url_task_2 = "submit/task-does-not-exist"
overview_url_task_2 = "task-overview/task-does-not-exist"

no_org = ""
wrong_org = "wrong_org,tira_org_pan"
org_1 = "tira_org_EXAMPLE-ORGANIZER"


class TestIsAdminForTask(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_wrong_org_on_wrong_url(self):
        # Arrange
        request = mock_request(wrong_org, "wrong-url")

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_wrong_org_on_existing_task_for_submit_url_1(self):
        # Arrange
        request = mock_request(wrong_org, submit_url_task_1)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_wrong_org_on_existing_task_for_overview_url_1(self):
        # Arrange
        request = mock_request(wrong_org, overview_url_task_1)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_wrong_org_on_existing_task_for_submit_url_2(self):
        # Arrange
        request = mock_request(wrong_org, submit_url_task_2)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_wrong_org_on_existing_task_for_overview_url_2(self):
        # Arrange
        request = mock_request(wrong_org, overview_url_task_2)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_no_org_on_wrong_url(self):
        # Arrange
        request = mock_request(no_org, "wrong-url")

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_no_org_on_existing_task_for_submit_url_1(self):
        # Arrange
        request = mock_request(no_org, submit_url_task_1)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_no_org_on_existing_task_for_overview_url_1(self):
        # Arrange
        request = mock_request(no_org, overview_url_task_1)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_no_org_on_existing_task_for_submit_url_2(self):
        # Arrange
        request = mock_request(no_org, submit_url_task_2)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_no_org_on_existing_task_for_overview_url_2(self):
        # Arrange
        request = mock_request(no_org, overview_url_task_2)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_org_1_on_wrong_url(self):
        # Arrange
        request = mock_request(org_1, "wrong-url")

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_org_1_on_existing_task_for_submit_url_1(self):
        # Arrange
        request = mock_request(org_1, submit_url_task_1)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertTrue(actual)

    def test_org_1_on_existing_task_for_overview_url_1(self):
        # Arrange
        request = mock_request(org_1, overview_url_task_1)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertTrue(actual)

    def test_org_1_on_existing_task_for_submit_url_2(self):
        # Arrange
        request = mock_request(org_1, submit_url_task_2)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    def test_org_1_on_existing_task_for_overview_url_2(self):
        # Arrange
        request = mock_request(org_1, overview_url_task_2)

        # Act
        actual = auth.is_admin_for_task(request)

        # Assert
        self.assertFalse(actual)

    @classmethod
    def tearDownClass(cls):
        pass
