import unittest
# PYTHONPATH=src/python/tira/git_integration/ pytest tests
from gitlab_integration import clean_job_output, clean_job_command

from pathlib import Path

class TestParsingOfOutputs(unittest.TestCase):
    def test_foo_01(self):
        text = Path('tests/resources/job_output_old').read_text()
        actual = clean_job_output(text)
        self.assertIn("15438/96147 [00:10<00:56, 1429.56 examples/s]", actual)

    def test_foo_02(self):
        text = Path('tests/resources/job_output_new').read_text()
        actual = clean_job_output(text)
        self.assertIn("Run command with tirex-tracker", actual)

    def test_foo_03(self):
        text = Path('tests/resources/job_output_old').read_text()
        actual = clean_job_command(text)
        self.assertEqual("/predict.py", actual)

    def test_foo_04(self):
        text = Path('tests/resources/job_output_new').read_text()
        actual = clean_job_command(text)
        self.assertEqual("/predict.py --threshold 0.25", actual)

