import tempfile
import unittest
from pathlib import Path

from ..format_check import _ERROR, _OK, JSONL_OUTPUT_VALID


def mocked_tira_client(on_run=None):
    class MockedLocalExecution:
        def __init__(self):
            self.calls = []

        def run(
            self,
            image,
            command,
            input_dir,
            output_dir,
            allow_network,
            additional_volumes,
            cpu_count,
            gpu_count=0,
            mem_limit=None,
            gpu_device_ids=None,
            forward_environment_variables=None,
            mount_directory=None,
            platform="linux/amd64",
        ):
            call = {
                "image": image,
                "command": command,
                "input_dir": input_dir,
                "output_dir": output_dir,
                "allow_network": allow_network,
                "additional_volumes": additional_volumes,
                "cpu_count": cpu_count,
                "gpu_count": gpu_count,
                "mem_limit": mem_limit,
                "gpu_device_ids": gpu_device_ids,
                "forward_environment_variables": forward_environment_variables,
                "mount_directory": mount_directory,
                "platform": platform,
            }
            self.calls.append(call)
            (output_dir / "results.txt").write_text("done")
            if on_run:
                on_run(call)

    class MockedTiraClient:
        def __init__(self):
            self.local_execution = MockedLocalExecution()

    return MockedTiraClient()


def run_workflow(software, **kwargs):
    from tira.workflows import run_workflow as rw

    tira_client = mocked_tira_client(kwargs.pop("on_run", None))
    result = rw(
        system_inputs=JSONL_OUTPUT_VALID,
        workflow="cached-execution",
        workflow_configuration={},
        software=software,
        tira=tira_client,
        **kwargs,
    )
    return result, tira_client


class TestCachedExecutionWorkflow(unittest.TestCase):
    def test_fails_for_missing_image(self):
        actual, _ = run_workflow({"command": "some-command"})

        self.assertEqual(_ERROR, actual[0])
        self.assertEqual("Software executed for 'cached-execution' needs a configuration for 'image'.", actual[1])

    def test_fails_for_missing_command(self):
        actual, _ = run_workflow({"image": "some-image"})

        self.assertEqual(_ERROR, actual[0])
        self.assertEqual("Software executed for 'cached-execution' needs a configuration for 'command'.", actual[1])

    def test_uses_cache_directory_and_forwards_runtime_arguments(self):
        with tempfile.TemporaryDirectory() as cache_source, tempfile.TemporaryDirectory() as read_only_mount:
            cache_source = Path(cache_source)
            read_only_mount = Path(read_only_mount)
            (cache_source / "seed.txt").write_text("cached-input")
            (read_only_mount / "mounted.txt").write_text("ro")

            def on_run(call):
                cache_mount = call["mount_directory"]["CACHE_DIR"]
                self.assertEqual("rw", cache_mount["mode"])
                self.assertTrue((cache_mount["path"] / "seed.txt").exists())
                (cache_mount["path"] / "used.txt").write_text("cached-output")

            actual, tira_client = run_workflow(
                {"image": "some-image", "command": "some-command"},
                allow_network=True,
                additional_volumes=["/tmp/models:/models:ro"],
                cpu_count=3,
                gpu_count=2,
                mem_limit="7g",
                gpu_device_ids=["0", "1"],
                forward_environment_variables=["OPENAI_API_KEY"],
                mount_directory={"READ_ONLY": {"path": read_only_mount, "mode": "ro"}},
                cache_directory={"CACHE_DIR": cache_source},
                platform="linux/arm64",
                on_run=on_run,
            )

            self.assertEqual(_OK, actual[0])
            self.assertIn("cache directory mounted via CACHE_DIR was used during the execution.", actual[1])
            self.assertEqual(1, len(tira_client.local_execution.calls))

            call = tira_client.local_execution.calls[0]
            self.assertEqual("some-image", call["image"])
            self.assertEqual("some-command", call["command"])
            self.assertTrue(call["allow_network"])
            self.assertEqual(["/tmp/models:/models:ro"], call["additional_volumes"])
            self.assertEqual(3, call["cpu_count"])
            self.assertEqual(2, call["gpu_count"])
            self.assertEqual("7g", call["mem_limit"])
            self.assertEqual(["0", "1"], call["gpu_device_ids"])
            self.assertEqual(["OPENAI_API_KEY"], call["forward_environment_variables"])
            self.assertEqual("linux/arm64", call["platform"])
            self.assertIn("READ_ONLY", call["mount_directory"])
            self.assertIn("CACHE_DIR", call["mount_directory"])
            self.assertEqual("ro", call["mount_directory"]["READ_ONLY"]["mode"])
            self.assertTrue((actual.run / "output" / "results.txt").exists())
            self.assertEqual("cached-input", (actual.run / "CACHE_DIR" / "seed.txt").read_text())
            self.assertEqual("cached-output", (actual.run / "CACHE_DIR" / "used.txt").read_text())

    def test_succeeds_without_mounts(self):
        actual, tira_client = run_workflow({"image": "some-image", "command": "some-command"})

        self.assertEqual(_OK, actual[0])
        self.assertEqual("The execution finished {}.", actual[1])
        self.assertEqual(1, len(tira_client.local_execution.calls))
        self.assertEqual({}, tira_client.local_execution.calls[0]["mount_directory"])
        self.assertTrue((actual.run / "output" / "results.txt").exists())

    def test_uses_rw_mount_directory_and_copies_back_results(self):
        with tempfile.TemporaryDirectory() as rw_mount:
            rw_mount = Path(rw_mount)

            def on_run(call):
                work_mount = call["mount_directory"]["WORK_DIR"]
                self.assertEqual("rw", work_mount["mode"])
                (work_mount["path"] / "written-by-command.txt").write_text("from-run")

            actual, tira_client = run_workflow(
                {"image": "some-image", "command": "some-command"},
                mount_directory={"WORK_DIR": {"path": rw_mount, "mode": "rw"}},
                on_run=on_run,
            )

            self.assertEqual(_OK, actual[0])
            self.assertIn("cache directory mounted via WORK_DIR was used during the execution.", actual[1])
            self.assertEqual(1, len(tira_client.local_execution.calls))
            self.assertEqual("rw", tira_client.local_execution.calls[0]["mount_directory"]["WORK_DIR"]["mode"])
            self.assertEqual("from-run", (actual.run / "WORK_DIR" / "written-by-command.txt").read_text())

    def test_fails_when_command_execution_raises_exception(self):
        def on_run(_call):
            raise RuntimeError("boom")

        actual, tira_client = run_workflow(
            {"image": "some-image", "command": "some-command"},
            on_run=on_run,
        )

        self.assertEqual(_ERROR, actual[0])
        self.assertEqual("The command \"some-command\" failed: RuntimeError('boom')", actual[1])
        self.assertEqual(1, len(tira_client.local_execution.calls))
        self.assertEqual("RuntimeError('boom')", (actual.run / "exception.txt").read_text())
        self.assertIn("RuntimeError('boom')", (actual.run / "stdout.txt").read_text())
        self.assertIn("RuntimeError('boom')", (actual.run / "stderr.txt").read_text())

    def test_fails_when_rw_cache_mount_is_unused(self):
        with tempfile.TemporaryDirectory() as cache_mount:
            actual, tira_client = run_workflow(
                {"image": "some-image", "command": "some-command"},
                mount_directory={"CACHE_DIR": {"path": Path(cache_mount), "mode": "rw"}},
            )

            self.assertEqual(_ERROR, actual[0])
            self.assertEqual(
                "The cache directory mounted via CACHE_DIR was not used during the execution.",
                actual[1],
            )
            self.assertEqual(1, len(tira_client.local_execution.calls))
