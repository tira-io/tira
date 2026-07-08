import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tira.tira_client import TiraClient
from tira.check_format import _fmt

RESOURCE_DIR = Path(__file__).parent / "resources"


def submit_task(directory, dataset="train"):
    client = TiraClient()
    return client.submit_dataset(directory, "task", dataset, True, skip_baseline=True)


class TestTaskSubmissions(unittest.TestCase):
    def test_fails_for_non_existing_directory(self):
        actual = submit_task(RESOURCE_DIR / "does-not-exist")
        self.assertIsNone(actual)

    def test_works_for_valid_directory(self):
        actual = submit_task(RESOURCE_DIR / "example-datasets" / "multi-author-analysis")
        self.assertIsNotNone(actual)

    def test_fails_without_default_upload_name_in_readme(self):
        actual = submit_task(RESOURCE_DIR / "example-datasets" / "missing-default-upload-name")
        self.assertIsNone(actual)

    def test_fails_for_non_existing_dataset(self):
        actual = submit_task(RESOURCE_DIR / "example-datasets" / "multi-author-analysis", "does-not-exist")
        self.assertIsNone(actual)

    def test_works_for_lsr_benchmark(self):
        actual = submit_task(RESOURCE_DIR / "example-datasets" / "learned-sparse-retrieval")
        self.assertIsNotNone(actual)

    @patch("tira.io_utils.verify_tira_installation", return_value=_fmt.OK)
    @patch("requests.post")
    def test_uploads_default_upload_name_from_readme(self, post_mock, _verify_installation):
        response_config = MagicMock()
        response_config.status_code = 200
        response_config.content = b'{"context":{"dataset_id":"dataset-1"}}'
        response_input = MagicMock()
        response_input.status_code = 200
        response_input.content = b'{"status":0,"message":"ok"}'
        response_truth = MagicMock()
        response_truth.status_code = 200
        response_truth.content = b'{"status":0,"message":"ok"}'
        post_mock.side_effect = [response_config, response_input, response_truth]

        client = TiraClient()
        client.authentication_headers = MagicMock(return_value={})
        client.fail_if_api_key_is_invalid = MagicMock()
        client.get_csrf_token = MagicMock(return_value="csrf-token")
        client.base_url = "https://www.tira.io"
        client.verify = True

        actual = client.submit_dataset(
            RESOURCE_DIR / "example-datasets" / "multi-author-analysis",
            "task",
            "train",
            False,
            skip_baseline=True,
        )

        self.assertIsNotNone(actual)
        self.assertEqual("predictions.jsonl", post_mock.call_args_list[0].kwargs["json"]["upload_name"])
