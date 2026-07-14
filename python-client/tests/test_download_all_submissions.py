import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from tira.rest_api_client import Client


class TestDownloadAllSubmissions(unittest.TestCase):
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

