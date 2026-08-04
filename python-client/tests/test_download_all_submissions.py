import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from tira.rest_api_client import Client
from tira.tira_cli import parse_args


class TestDownloadAllSubmissions(unittest.TestCase):
    def test_all_evaluations_flag_is_registered(self):
        original_argv = list(sys.argv)
        try:
            sys.argv = [
                "tira-cli",
                "download",
                "--all-submissions",
                "--all-evaluations",
                "--dataset",
                "dataset",
                "--output",
                "tmp",
            ]
            args = parse_args()
        finally:
            sys.argv = original_argv

        self.assertTrue(args.all_submissions)
        self.assertTrue(args.all_evaluations)

    @patch("tira.rest_api_client.time.sleep", return_value=None)
    def test_repackaged_download_includes_upload_metadata(self, _sleep):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_output_dir = tmp_path / "cached-run" / "output"
            run_output_dir.mkdir(parents=True, exist_ok=True)
            (run_output_dir / "predictions.jsonl").write_text("hello\n")

            client = Client()
            client.get_dataset = MagicMock(return_value={"default_task": "task"})
            client.evaluations = MagicMock(return_value=pd.DataFrame([{"run_id": "run-1", "team": "team-1"}]))
            client.download_zip_to_cache_directory = MagicMock(return_value=run_output_dir)
            client.json_response = MagicMock(
                side_effect=[
                    {"context": {"all_uploadgroups": [{"id": "upload-1"}]}},
                    {
                        "context": {
                            "upload_group_details": {
                                "id": "upload-1",
                                "description": "submission description",
                                "display_name": "submission name",
                                "upload_metadata": {"track": "main", "run_id": "submission-name"},
                                "runs": [{"input_run_id": "", "run_id": "run-1"}],
                            }
                        }
                    },
                ]
            )

            client.download_all_submissions("english-20260708_0-test", tmp_path, repackage=True)

            metadata = [
                json.loads(line)
                for line in (tmp_path / "metadata.jsonl").read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(1, len(metadata))
            self.assertEqual({"track": "main", "run_id": "submission-name"}, metadata[0]["upload_metadata"])

    def test_downloads_all_evaluations_and_adds_their_paths_to_metadata(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            cached_runs = tmp_path / "cached-runs"
            for run_id in ["run-1", "evaluation-1", "evaluation-2"]:
                output_dir = cached_runs / run_id / "output"
                output_dir.mkdir(parents=True)
                (output_dir / "result.json").write_text("{}")

            client = Client()
            client.get_dataset = MagicMock(return_value={"default_task": "task"})
            client.evaluations = MagicMock(
                return_value=pd.DataFrame(
                    [
                        {
                            "run_id": "run-1",
                            "evaluation_run_id": "evaluation-1",
                            "team": "team-1",
                        },
                        {
                            "run_id": "run-1",
                            "evaluation_run_id": "evaluation-2",
                            "team": "team-1",
                        },
                    ]
                )
            )
            client.download_zip_to_cache_directory = MagicMock(
                side_effect=lambda _task, _dataset, _team, run_id: cached_runs / run_id / "output"
            )

            client.download_all_submissions(
                "dataset",
                tmp_path / "download",
                repackage=False,
                all_evaluations=True,
            )

            metadata = [
                json.loads(line)
                for line in (tmp_path / "download" / "metadata.jsonl").read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(1, len(metadata))
            self.assertEqual(
                [
                    "raw-evaluations/dataset/evaluation-1",
                    "raw-evaluations/dataset/evaluation-2",
                ],
                metadata[0]["evaluations"],
            )
            self.assertTrue(
                (tmp_path / "download" / "raw-evaluations" / "dataset" / "evaluation-1" / "output").is_dir()
            )
            self.assertTrue(
                (tmp_path / "download" / "raw-evaluations" / "dataset" / "evaluation-2" / "output").is_dir()
            )
