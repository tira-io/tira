import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tira.check_format import _fmt
from tira.tira_client import TiraClient

RESOURCE_DIR = Path(__file__).parent / "resources"


def submit_task(directory, dataset="train"):
    client = TiraClient()
    return client.submit_dataset(directory, "task", dataset, True, skip_baseline=True)


class TestTaskSubmissions(unittest.TestCase):
    @patch.object(TiraClient, "clone_git_repository")
    def test_resolves_baseline_from_git_repository(self, clone_git_repository):
        clone_git_repository.return_value = Path("/tmp/cloned-repository")
        client = TiraClient()

        baseline_path, docker_file_root, git_url = client._resolve_baseline_source(
            RESOURCE_DIR,
            "https://github.com/example/task/tree/master/baseline",
        )

        self.assertEqual(Path("/tmp/cloned-repository/baseline"), baseline_path)
        self.assertEqual(Path("/tmp/cloned-repository"), docker_file_root)
        self.assertEqual("https://github.com/example/task", git_url)
        clone_git_repository.assert_called_once_with("https://github.com/example/task")

    @patch.object(TiraClient, "clone_git_repository")
    def test_resolves_baseline_relative_to_dataset_directory(self, clone_git_repository):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "datasets" / "example"
            relative_baseline = Path(tmpdir) / "baseline"
            dataset_path.mkdir(parents=True)
            relative_baseline.mkdir()

            client = TiraClient()
            baseline_path, docker_file_root, git_url = client._resolve_baseline_source(dataset_path, "../../baseline")

            self.assertEqual(relative_baseline.resolve(), baseline_path)
            self.assertEqual(relative_baseline.resolve(), docker_file_root)
            self.assertIsNone(git_url)
            clone_git_repository.assert_not_called()

    def test_rejects_missing_relative_baseline(self):
        client = TiraClient()

        with self.assertRaisesRegex(ValueError, "does not exist"):
            client._resolve_baseline_source(RESOURCE_DIR, "missing-baseline")

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
