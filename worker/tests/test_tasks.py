import os
import sys
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

os.environ["TIRA_WORKER_CONFIG"] = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "tira-worker-config.yml")
)

from tira_worker import _tasks


class TestExecuteMonitored(unittest.TestCase):
    @patch.object(_tasks, "MONITORED_EXECUTION_POLL_INTERVAL_SECONDS", 0.01)
    def test_execute_monitored_updates_running_job_output(self):
        client = Mock()
        client.update_running_process_output_admin.return_value = {"status": 0, "killing": False}

        def method(_output_dir):
            for i in range(20):
                print(f"stdout {i}")
            for i in range(20):
                print(f"stderr {i}", file=sys.stderr)
            time.sleep(0.03)

        ret = _tasks.execute_monitored(method, client=client, job_id="job-1")

        self.assertTrue((ret / "stdout.txt").exists())
        self.assertTrue((ret / "stderr.txt").exists())
        self.assertGreaterEqual(client.update_running_process_output_admin.call_count, 1)

        last_call = client.update_running_process_output_admin.call_args_list[-1]
        self.assertEqual("job-1", last_call.args[0])
        self.assertIn("## stdout (Last 15 lines)", last_call.args[1])
        self.assertIn("# stderr (Last 15 lines)", last_call.args[1])
        self.assertIn("stdout 19", last_call.args[1])
        self.assertIn("stderr 19", last_call.args[1])
        self.assertNotIn("stdout 0", last_call.args[1])
        self.assertNotIn("stderr 0", last_call.args[1])

    def test_execute_monitored_without_client_still_returns_result(self):
        ret = _tasks.execute_monitored(lambda output_dir: output_dir.mkdir(exist_ok=True))
        self.assertTrue((ret / "output").exists())

    @patch.object(_tasks, "huggingface_model_mounts")
    @patch.object(_tasks, "download_hf_model")
    def test_resolve_hf_models_downloads_each_model_before_mounting(self, download_hf_model, huggingface_model_mounts):
        huggingface_model_mounts.return_value = {
            "/cache/models--openai-community--gpt2": {
                "bind": "/root/.cache/huggingface/hub/models--openai-community--gpt2",
                "mode": "ro",
            },
            "/cache/models--openai-community--gpt2-large": {
                "bind": "/root/.cache/huggingface/hub/models--openai-community--gpt2-large",
                "mode": "ro",
            },
        }

        actual = _tasks.resolve_hf_models(["openai-community/gpt2", "openai-community/gpt2-large"])

        self.assertEqual(
            [
                "/cache/models--openai-community--gpt2:/root/.cache/huggingface/hub/models--openai-community--gpt2:ro",
                "/cache/models--openai-community--gpt2-large:/root/.cache/huggingface/hub/models--openai-community--gpt2-large:ro",
            ],
            actual,
        )
        download_hf_model.assert_has_calls(
            [call("openai-community/gpt2"), call("openai-community/gpt2-large")]
        )
        huggingface_model_mounts.assert_called_once_with(["openai-community/gpt2", "openai-community/gpt2-large"])

    @patch.object(_tasks, "check_output")
    def test_rsync_from_local_or_fail_runs_fast_rsync_for_existing_dir(self, check_output):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            src_dir = tmpdir / "src"
            target_dir = tmpdir / "nested" / "target"
            src_dir.mkdir()

            _tasks.rsync_from_local_or_fail(src_dir, target_dir)

            self.assertTrue(target_dir.parent.is_dir())
            check_output.assert_called_once_with(
                [
                    "rsync",
                    "-a",
                    "--size-only",
                    "--ignore-existing",
                    f"{src_dir}/",
                    f"{target_dir}/",
                ]
            )

    @patch.object(_tasks, "check_output")
    def test_rsync_from_local_or_fail_raises_for_missing_dir(self, check_output):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            src_dir = tmpdir / "missing"
            target_dir = tmpdir / "target"

            with self.assertRaises(ValueError) as context:
                _tasks.rsync_from_local_or_fail(src_dir, target_dir)

            self.assertIn(str(src_dir), str(context.exception))
            check_output.assert_not_called()

    def test_resolve_dynamic_mounts_downloads_injected_run_and_resolves_named_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "downloaded-run" / "output"
            cache_dir = output_dir / "CACHE_DIR"
            cache_dir.mkdir(parents=True)
            client = Mock()
            client.download_zip_to_cache_directory.return_value = output_dir

            actual = _tasks.resolve_dynamic_mounts(
                {"CACHE_DIR": {"source": "OUTPUT_OF_OTHER_EXECUTION", "mode": "rw", "run_id": "run-1"}},
                client,
                "task",
                "dataset",
                "team",
            )

            self.assertEqual(str(cache_dir.resolve().absolute()), actual["CACHE_DIR"]["source"])
            client.download_zip_to_cache_directory.assert_called_once_with(
                task="task", dataset="dataset", team="team", run_id="run-1"
            )

    def test_resolve_dynamic_mounts_falls_back_to_output_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "downloaded-run" / "output"
            output_dir.mkdir(parents=True)
            client = Mock()
            client.download_zip_to_cache_directory.return_value = output_dir

            actual = _tasks.resolve_dynamic_mounts(
                {"CACHE_DIR": {"source": "OUTPUT_OF_OTHER_EXECUTION", "mode": "rw", "run_id": "run-1"}},
                client,
                "task",
                "dataset",
                "team",
            )

            self.assertEqual(str(output_dir.resolve().absolute()), actual["CACHE_DIR"]["source"])

    def test_resolve_dynamic_mounts_keeps_non_run_mounts_unchanged(self):
        client = Mock()
        dynamic_mounts = {"CACHE_DIR": {"source": "EMPTY_DIR", "mode": "rw"}}

        actual = _tasks.resolve_dynamic_mounts(dynamic_mounts, client, "task", "dataset", "team")

        self.assertEqual(dynamic_mounts, actual)
        client.download_zip_to_cache_directory.assert_not_called()
