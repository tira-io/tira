import unittest

from tira.io_utils import hostnames_required_for_network_access


class TestHostnamesRequiredForNetworkAccess(unittest.TestCase):
    def test_empty_environment_requires_no_hostnames(self):
        self.assertEqual(hostnames_required_for_network_access({}), [])

    def test_unrelated_environment_variables_require_no_hostnames(self):
        environment = {"FOO": "1", "BAR": "2"}

        self.assertEqual(hostnames_required_for_network_access(environment), [])

    def test_partial_openai_environment_variables_require_no_hostnames(self):
        environment = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "https://api.openai.com/v1"}

        self.assertEqual(hostnames_required_for_network_access(environment), [])

    def test_complete_openai_environment_variables_require_the_base_url_hostname(self):
        environment = {
            "OPENAI_API_KEY": "123",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4",
        }

        self.assertEqual(hostnames_required_for_network_access(environment), ["api.openai.com"])

    def test_openai_base_url_without_scheme_is_used_as_hostname(self):
        environment = {
            "OPENAI_API_KEY": "123",
            "OPENAI_BASE_URL": "api.openai.com",
            "OPENAI_MODEL": "gpt-4",
        }

        self.assertEqual(hostnames_required_for_network_access(environment), ["api.openai.com"])

    def test_orbit_api_base_requires_its_hostname(self):
        environment = {"ORBIT_API_BASE": "https://orbit.example.com/api"}

        self.assertEqual(hostnames_required_for_network_access(environment), ["orbit.example.com"])

    def test_multiple_groups_return_multiple_hostnames(self):
        environment = {
            "OPENAI_API_KEY": "123",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4",
            "ORBIT_API_BASE": "https://orbit.example.com/api",
        }

        self.assertEqual(
            sorted(hostnames_required_for_network_access(environment)),
            ["api.openai.com", "orbit.example.com"],
        )
