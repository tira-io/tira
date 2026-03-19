import unittest

from ..format_check import _ERROR, _OK, JSONL_OUTPUT_VALID


def mocked_tira_client():
    return None


def run_worklow(workflow_name, workflow_config, software):
    from tira.workflows import run_workflow as rw

    tira_client = mocked_tira_client()
    return rw(JSONL_OUTPUT_VALID, workflow_name, workflow_config, software, None, None, None, None, tira_client)


class TestErrorMessageWorkflows(unittest.TestCase):
    def test_fails_for_non_existing_workflow_01(self):
        expected = [_ERROR, "No workflow with the identifyier 'non-existing-workflow' exists."]
        workflow_name = "non-existing-workflow"
        workflow_config = {}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_non_existing_workflow_02(self):
        expected = [_ERROR, "No workflow with the identifyier '1non-existing-workflow1' exists."]
        workflow_name = "1non-existing-workflow1"
        workflow_config = {}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_obfuscation_image(self):
        expected = [_ERROR, "The workflow 'pan26-text-watermarking' requires a configuration for 'obfuscation_image'."]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_obfuscation_command(self):
        expected = [
            _ERROR,
            "The workflow 'pan26-text-watermarking' requires a configuration for 'obfuscation_command'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01"}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_software_image(self):
        expected = [
            _ERROR,
            "Software executed for 'pan26-text-watermarking' needs a configuration for 'image'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01", "obfuscation_command": "some-command"}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_watermark_command(self):
        expected = [
            _ERROR,
            "Software executed for 'pan26-text-watermarking' needs a configuration for 'watermark_command'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01", "obfuscation_command": "some-command"}
        software = {"image": "some-image"}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_detect_command(self):
        expected = [
            _ERROR,
            "Software executed for 'pan26-text-watermarking' needs a configuration for 'detect_command'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01", "obfuscation_command": "some-command"}
        software = {"image": "some-image", "watermark_command": "some-command"}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])
