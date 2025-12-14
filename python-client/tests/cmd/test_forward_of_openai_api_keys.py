import os
import unittest

from tira.io_utils import openai_api_environment_variables


class TestForwardOfOpenAiAPIKeys(unittest.TestCase):
    def test_empty_dict_stays_empty_if_no_environment_variable_is_set(self):
        expected = {}

        actual = openai_api_environment_variables()
        self.assertEqual(actual, expected)

    def test_minimal_environment_variables_are_set(self):
        expected = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456", "OPENAI_MODEL": "789"}

        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"

        actual = openai_api_environment_variables()
        self.assertEqual(actual, expected)

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]

    def test_more_environment_variables_are_set(self):
        expected = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456", "OPENAI_MODEL": "789", "OPENAI_XYZ": "10"}

        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"
        os.environ["OPENAI_XYZ"] = "10"

        actual = openai_api_environment_variables()
        self.assertEqual(actual, expected)

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]
        del os.environ["OPENAI_XYZ"]

    def test_more_environment_variables_are_set(self):
        expected = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456", "OPENAI_MODEL": "789", "OPENAI_XYZ": "10"}

        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"
        os.environ["OPENAI_XYZ"] = "10"

        actual = openai_api_environment_variables()
        self.assertEqual(actual, expected)

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]
        del os.environ["OPENAI_XYZ"]

    def test_failure_thrown_if_model_is_missing(self):
        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"

        with self.assertRaises(ValueError):
            openai_api_environment_variables()

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]

    def test_failure_thrown_if_base_url_is_missing(self):
        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_MODEL"] = "789"

        with self.assertRaises(ValueError):
            openai_api_environment_variables()

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_MODEL"]

    def test_failure_thrown_if_api_key_is_missing(self):
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"

        with self.assertRaises(ValueError):
            openai_api_environment_variables()

        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]
