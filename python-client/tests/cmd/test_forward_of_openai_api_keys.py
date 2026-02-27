import os
import unittest

from tira.io_utils import environment_variables_to_forward


class TestForwardOfOpenAiAPIKeys(unittest.TestCase):
    def test_empty_dict_stays_empty_if_no_environment_variable_is_set(self):
        expected = {}

        actual = environment_variables_to_forward()
        self.assertEqual(actual, expected)

    def test_minimal_environment_variables_are_set(self):
        expected = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456", "OPENAI_MODEL": "789"}

        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"

        actual = environment_variables_to_forward(("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"))
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

        actual = environment_variables_to_forward(("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "OPENAI_XYZ"))
        self.assertEqual(actual, expected)

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]
        del os.environ["OPENAI_XYZ"]

    def test_some_environment_variables_are_ignored(self):
        expected = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456", "OPENAI_MODEL": "789"}

        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"
        os.environ["OPENAI_XYZ"] = "10"

        actual = environment_variables_to_forward(("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"))
        self.assertEqual(actual, expected)

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]
        del os.environ["OPENAI_XYZ"]

    def test_more_environment_variables_are_set_02(self):
        expected = {"OPENAI_API_KEY": "123", "OPENAI_BASE_URL": "456", "OPENAI_MODEL": "789", "OPENAI_XYZ": "11"}

        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"
        os.environ["OPENAI_XYZ"] = "11"

        actual = environment_variables_to_forward(("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "OPENAI_XYZ"))
        self.assertEqual(actual, expected)

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]
        del os.environ["OPENAI_XYZ"]

    def test_failure_thrown_if_model_is_missing(self):
        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_BASE_URL"] = "456"

        with self.assertRaises(ValueError):
            environment_variables_to_forward(("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"))

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_BASE_URL"]

    def test_failure_thrown_if_base_url_is_missing(self):
        os.environ["OPENAI_API_KEY"] = "123"
        os.environ["OPENAI_MODEL"] = "789"

        with self.assertRaises(ValueError):
            environment_variables_to_forward(("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"))

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_MODEL"]

    def test_failure_thrown_if_api_key_is_missing(self):
        os.environ["OPENAI_BASE_URL"] = "456"
        os.environ["OPENAI_MODEL"] = "789"

        with self.assertRaises(ValueError):
            environment_variables_to_forward(("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"))

        del os.environ["OPENAI_BASE_URL"]
        del os.environ["OPENAI_MODEL"]
