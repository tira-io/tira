import unittest

from tira.io_utils import environment_variables_require_network_access


class TestEnvironmentVariablesRequireNetworkAccess(unittest.TestCase):
    def test_empty_environment_does_not_require_network_access(self):
        self.assertFalse(environment_variables_require_network_access({}))

    def test_unrelated_environment_variables_do_not_require_network_access(self):
        environment = {"FOO": "1", "BAR": "2"}

        self.assertFalse(environment_variables_require_network_access(environment))

    def test_partial_openai_environment_variables_do_not_require_network_access(self):
        environment = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456"}

        self.assertFalse(environment_variables_require_network_access(environment))

    def test_complete_openai_environment_variables_require_network_access(self):
        environment = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456", "OPENAI_MODEL": "789"}

        self.assertTrue(environment_variables_require_network_access(environment))

    def test_orbit_api_base_requires_network_access(self):
        environment = {"ORBIT_API_BASE": "https://orbit.example.com"}

        self.assertTrue(environment_variables_require_network_access(environment))

    def test_orbit_api_base_together_with_unrelated_variables_requires_network_access(self):
        environment = {"ORBIT_API_BASE": "https://orbit.example.com", "FOO": "1"}

        self.assertTrue(environment_variables_require_network_access(environment))
