import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

os.environ["TIRA_WORKER_CONFIG"] = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "tira-worker-config.yml")
)

from tira.tira_client import TiraClient
from tira_worker import _tasks


class FakeAdminClient(TiraClient):
    """A minimal admin-client stub for the worker's `evaluate` celery task. It fakes only
    the parts that would otherwise require network access (get_dataset, download_dataset,
    download_zip_to_cache_directory, upload_run_admin). TiraClient.evaluate itself is
    NOT overridden, so the real, unsandboxed evaluator runs end-to-end against the
    predictions/truths written to disk by the test."""

    def __init__(self, config, truths_dir: Path, run_dir: Path):
        self.config = config
        self.truths_dir = truths_dir
        self.run_dir = run_dir
        self.download_dataset_calls = []
        self.download_zip_to_cache_directory_calls = []
        self.upload_run_admin_calls = []

    def get_dataset(self, dataset):
        return self.config

    def download_dataset(self, task, dataset, truth_dataset=False):
        self.download_dataset_calls.append((task, dataset, truth_dataset))
        return self.truths_dir

    def download_zip_to_cache_directory(self, run_id, dataset, task, team):
        self.download_zip_to_cache_directory_calls.append((run_id, dataset, task, team))
        return self.run_dir

    def upload_run_admin(self, file_path, job_id):
        self.upload_run_admin_calls.append((file_path, job_id))


class TestEvaluateTask(unittest.TestCase):
    @patch.object(_tasks, "persist_tira_metadata_for_job")
    @patch.object(_tasks, "get_admin_client")
    def test_evaluate_task_runs_the_real_unsandboxed_accuracy_evaluator_and_fills_output_dir(
        self, get_admin_client, persist_tira_metadata_for_job
    ):
        config = {
            "run_format": "*.jsonl",
            "run_format_configuration": {"id_field": "id", "value_field": "label"},
            "truth_format": "*.jsonl",
            "truth_format_configuration": {"id_field": "id", "value_field": "label"},
            "measures": ["accuracy"],
        }

        predictions = [
            {"id": "1", "label": 1},
            {"id": "2", "label": 0},
            {"id": "3", "label": 1},  # wrong, ground truth is 0
        ]
        truths = [
            {"id": "1", "label": 1},
            {"id": "2", "label": 0},
            {"id": "3", "label": 0},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            truths_dir = Path(tmp) / "truths"
            run_dir.mkdir()
            truths_dir.mkdir()

            (run_dir / "predictions.jsonl").write_text("\n".join(json.dumps(i) for i in predictions))
            (truths_dir / "truths.jsonl").write_text("\n".join(json.dumps(i) for i in truths))

            client = FakeAdminClient(config, truths_dir, run_dir)
            get_admin_client.return_value = client

            _tasks.evaluate.run(
                run_id="run-1",
                dataset="dataset-1",
                evaluator_id="evaluator-1",
                task="task-1",
                team="team-1",
                job_id="job-1",
            )

            self.assertEqual([("task-1", "dataset-1", True)], client.download_dataset_calls)
            self.assertEqual(
                [("run-1", "dataset-1", "task-1", "team-1")], client.download_zip_to_cache_directory_calls
            )

            self.assertEqual(1, len(client.upload_run_admin_calls))
            eval_results_dir, uploaded_job_id = client.upload_run_admin_calls[0]
            self.assertEqual("job-1", uploaded_job_id)

            # the output_dir that TiraClient.evaluate received (from execute_monitored) must be
            # correctly filled with the real evaluation results
            evaluation_file = eval_results_dir / "output" / "evaluation.prototext"
            self.assertTrue(evaluation_file.exists())
            content = evaluation_file.read_text()
            self.assertIn('key: "Accuracy"', content)
            self.assertIn('value: "0.6666666666666666"', content)

            persist_tira_metadata_for_job.assert_called_once_with(
                eval_results_dir, ANY, "run-1", "evaluator-1", "dataset-1", "task-1"
            )


if __name__ == "__main__":
    unittest.main()
