import json
import tempfile
import unittest
from pathlib import Path

from tira.check_format import lines_if_valid

from ..format_check import _OK, JSONL_OUTPUT_VALID


def passthrough_command(input_dir, output_dir, mount_directory=None):
    ret = []
    print("hello world from passthrough")
    for line in lines_if_valid(input_dir, "*.jsonl"):
        ret.append(json.dumps(line))
    (output_dir / "predictions.jsonl").write_text("\n".join(ret))


def command_with_writable_mount_copy(input_dir, output_dir, mount_directory=None):
    copied_mount = mount_directory["CACHE_DIR"]
    copied_mount_path = Path(copied_mount["path"])
    print(f"writing to {copied_mount_path}")
    (copied_mount_path / "written-by-workflow.txt").write_text("workflow can write here")
    passthrough_command(input_dir, output_dir, mount_directory)


COMMAND_TO_MOCK = {
    "some-passthrough-command": passthrough_command,
    "some-cache-command": command_with_writable_mount_copy,
}


def mocked_tira_client():
    class MockedLocalExecution:
        def __init__(self):
            self.calls = []

        def extract_entrypoint(self, image):
            return "some-passthrough-command"

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
            forward_environment_variables=None,
            mount_directory=None,
        ):
            self.calls.append(
                {
                    "image": image,
                    "command": command,
                    "mount_directory": mount_directory,
                }
            )
            COMMAND_TO_MOCK[command](input_dir, output_dir, mount_directory)

    class MockedTiraClient:
        def __init__(self):
            self.local_execution = MockedLocalExecution()

    return MockedTiraClient()


def run_worklow(workflow_name, workflow_config, software, mount_directory=None):
    from tira.workflows import run_workflow as rw

    tira_client = mocked_tira_client()
    result = rw(
        JSONL_OUTPUT_VALID,
        workflow_name,
        workflow_config,
        software,
        None,
        None,
        None,
        None,
        None,
        tira_client,
        None,
        mount_directory,
    )
    return result, tira_client


class TestTrecAutoJudgeWorkflow(unittest.TestCase):
    def test_for_correct_configuration(self):
        expected = [_OK, "workflow executed on 'trec-auto-judge'."]
        actual, _ = run_worklow("trec-autojudge", {}, {"image": "some-image", "command": "some-passthrough-command"})
        stderr = actual.run / "stderr.txt"
        stdout = actual.run / "stdout.txt"

        self.assertTrue(stderr.exists())
        self.assertTrue(stdout.exists())
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])
        self.assertTrue((actual.run / "output" / "predictions.jsonl").exists())

        stdout_text = stdout.read_text()
        self.assertIn("hello world from passthrough", stdout_text)
        self.assertIn("Step 1: Execute with some-passthrough-command", stdout_text)

        stderr_text = stderr.read_text()
        self.assertIn("Step 1: Execute with some-passthrough-command", stderr_text)
        self.assertNotIn("hello world from passthrough", stderr_text)

    def test_mount_directory_is_copied_and_mounted_read_write(self):
        with tempfile.TemporaryDirectory() as mount_source_dir:
            mount_source_dir = Path(mount_source_dir)
            (mount_source_dir / "existing.txt").write_text("original content")

            actual, tira_client = run_worklow(
                "trec-auto-judge",
                {},
                {"image": "some-image", "command": "some-cache-command"},
                {"CACHE_DIR": str(mount_source_dir)},
            )

        self.assertEqual(_OK, actual[0])
        forwarded_mount = tira_client.local_execution.calls[0]["mount_directory"]["CACHE_DIR"]
        self.assertEqual("rw", forwarded_mount["mode"])
        self.assertNotEqual(str(mount_source_dir), forwarded_mount["path"])
        self.assertTrue((Path(forwarded_mount["path"]) / "existing.txt").exists())
        self.assertTrue((Path(forwarded_mount["path"]) / "written-by-workflow.txt").exists())
        self.assertFalse((mount_source_dir / "written-by-workflow.txt").exists())
