from django.test import TestCase


class TestSetup(TestCase):
    def setUp(self) -> None:
        self.setup = True

    def test_setup_success(self):
        """test if tests work"""
        self.assertTrue(self.setup)
