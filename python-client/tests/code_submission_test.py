import unittest
from pathlib import Path

from tira.rest_api_client import Client


class CodeSubmissionTest(unittest.TestCase):
    def test_code_submission_fails_if_code_not_in_version_control(self):
        tira = Client()
        with self.assertRaises(ValueError):
            tira.submit_code(Path("."), "wows-eval")
