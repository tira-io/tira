import json
import unittest

from tira.check_format import lines_if_valid

from ..format_check import _ERROR, _OK, JSONL_OUTPUT_VALID


def pseudo_watermarking(input_dir, output_dir):
    ret = []
    print("hello world from watermarking")
    for l in lines_if_valid(input_dir, "*.jsonl"):
        l["text"] = "foo"
        ret.append(json.dumps(l))
    (output_dir / "watermarked.jsonl").write_text("\n".join(ret))


def wrong_watermarking(input_dir, output_dir):
    print("A wrong watermarking that does not produce an output")


def pseudo_obfuscation(input_dir, output_dir):
    ret = []
    print("hello world from obfuscation")
    for l in lines_if_valid(input_dir / "01-watermarking", "*.jsonl"):
        l["text"] = "obfuscated"
        l["truth_label"] = "sadasd"
        ret.append(json.dumps(l))
    (output_dir / "obfuscation.jsonl").write_text("\n".join(ret))


def detection_command(input_dir, output_dir):
    ret = []
    print("hello world from detection")
    for l in lines_if_valid(input_dir, "*.jsonl"):
        if "truth_label" in l:
            raise ValueError("dasda")
        if "text" not in l:
            raise ValueError("dsada")

        ret.append(json.dumps(l))
    (output_dir / "predictions.jsonl").write_text("\n".join(ret))


def wrong_detection_command(input_dir, output_dir):
    print("detection that does not write a file...")


COMMAND_TO_MOCK = {
    "wrong-watermarking-command": wrong_watermarking,
    "some-watermarking-command": pseudo_watermarking,
    "some-obfuscation-command": pseudo_obfuscation,
    "some-detection-command": detection_command,
    "wrong-detection-command": wrong_detection_command,
}


def mocked_tira_client():
    class MockedLocalExecution:
        def run(
            self,
            image,
            command,
            input_dir,
            output_dir,
            allow_network,
            additional_volumes,
            cpu_count,
            mem_limit,
            gpu_device_ids,
        ):
            COMMAND_TO_MOCK[command](input_dir, output_dir)

    class MockedTiraClient:
        def __init__(self):
            self.local_execution = MockedLocalExecution()

    return MockedTiraClient()


def run_worklow(workflow_name, workflow_config, software):
    from tira.workflows import run_workflow as rw

    tira_client = mocked_tira_client()
    return rw(JSONL_OUTPUT_VALID, workflow_name, workflow_config, software, None, None, None, None, None, tira_client)


class TestErrorMessageWorkflows(unittest.TestCase):
    def test_for_configuration_with_invalid_watermarking(self):
        expected = [
            _ERROR,
            'Watermarking the text failed. The command "wrong-watermarking-command" did not produce a valid jsonl file.',
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {
            "obfuscation_image": "some-obfuscation-image-01",
            "obfuscation_command": "some-obfuscation-command",
        }
        software = {
            "image": "some-image",
            "watermark_command": "wrong-watermarking-command",
            "detect_command": "some-detection-command",
        }
        actual = run_worklow(workflow_name, workflow_config, software)
        stderr = actual.run / "stderr.txt"
        stdout = actual.run / "stdout.txt"
        self.assertTrue(stderr.exists())
        self.assertTrue(stdout.exists())

        print(stderr.read_text())
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

        stdout_text = stdout.read_text()

        self.assertIn("A wrong watermarking that does not produce an output", stdout_text)
        self.assertIn("Step 1: Watermarking with wrong-watermarking-command", stdout_text)
        self.assertNotIn("hello world from obfuscation", stdout_text)
        self.assertNotIn("hello world from detection", stdout_text)
        self.assertNotIn("Step 5: Detection with some-detection-command", stdout_text)
        self.assertNotIn("Step 3: Obfuscation with some-obfuscation-command", stdout_text)
        self.assertNotIn("The jsonl file has the correct format", stdout_text)

        stderr_text = stderr.read_text()

        self.assertIn("Step 1: Watermarking with wrong-watermarking-command", stderr_text)
        self.assertNotIn("A wrong watermarking that does not produce an output", stderr_text)
        self.assertNotIn("Step 5: Detection with some-detection-command", stderr_text)
        self.assertNotIn("Step 3: Obfuscation with some-obfuscation-command", stderr_text)
        self.assertNotIn("The jsonl file has the correct format", stderr_text)

    def test_for_configuration_with_invalid_detection(self):
        expected = [
            _ERROR,
            'The detection step failed. The command "wrong-detection-command" did not produce a valid jsonl file.',
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {
            "obfuscation_image": "some-obfuscation-image-01",
            "obfuscation_command": "some-obfuscation-command",
        }
        software = {
            "image": "some-image",
            "watermark_command": "some-watermarking-command",
            "detect_command": "wrong-detection-command",
        }
        actual = run_worklow(workflow_name, workflow_config, software)
        stderr = actual.run / "stderr.txt"
        stdout = actual.run / "stdout.txt"
        self.assertTrue(stderr.exists())
        self.assertTrue(stdout.exists())

        print(stderr.read_text())
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

        stdout_text = stdout.read_text()

        self.assertIn("hello world from watermarking", stdout_text)
        self.assertIn("hello world from obfuscation", stdout_text)
        self.assertIn("detection that does not write a file...", stdout_text)
        self.assertIn("Step 5: Detection with wrong-detection-command", stdout_text)
        self.assertIn("Step 3: Obfuscation with some-obfuscation-command", stdout_text)
        self.assertIn("Step 1: Watermarking with some-watermarking-command", stdout_text)
        self.assertIn("The jsonl file has the correct format", stdout_text)

        stderr_text = stderr.read_text()

        self.assertIn("Step 5: Detection with wrong-detection-command", stderr_text)
        self.assertIn("Step 3: Obfuscation with some-obfuscation-command", stderr_text)
        self.assertIn("Step 1: Watermarking with some-watermarking-command", stderr_text)
        self.assertIn("The jsonl file has the correct format", stderr_text)

    def test_for_correct_configuration(self):
        expected = [
            _OK,
            "workflow executed on 'pan26-text-watermarking'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {
            "obfuscation_image": "some-obfuscation-image-01",
            "obfuscation_command": "some-obfuscation-command",
        }
        software = {
            "image": "some-image",
            "watermark_command": "some-watermarking-command",
            "detect_command": "some-detection-command",
        }
        actual = run_worklow(workflow_name, workflow_config, software)
        stderr = actual.run / "stderr.txt"
        stdout = actual.run / "stdout.txt"
        self.assertTrue(stderr.exists())
        self.assertTrue(stdout.exists())

        print(stderr.read_text())
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

        stdout_text = stdout.read_text()

        self.assertIn("hello world from watermarking", stdout_text)
        self.assertIn("hello world from obfuscation", stdout_text)
        self.assertIn("hello world from detection", stdout_text)
        self.assertIn("Step 5: Detection with some-detection-command", stdout_text)
        self.assertIn("Step 3: Obfuscation with some-obfuscation-command", stdout_text)
        self.assertIn("Step 1: Watermarking with some-watermarking-command", stdout_text)
        self.assertIn("The jsonl file has the correct format", stdout_text)

        stderr_text = stderr.read_text()

        self.assertNotIn("hello world from watermarking", stderr_text)
        self.assertNotIn("hello world from obfuscation", stderr_text)
        self.assertNotIn("hello world from detection", stderr_text)
        self.assertIn("Step 5: Detection with some-detection-command", stderr_text)
        self.assertIn("Step 3: Obfuscation with some-obfuscation-command", stderr_text)
        self.assertIn("Step 1: Watermarking with some-watermarking-command", stderr_text)
        self.assertIn("The jsonl file has the correct format", stderr_text)
