import os
import sys
import time
import unittest
from unittest.mock import Mock, patch

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
