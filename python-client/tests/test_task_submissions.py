import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

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

    def test_evaluator_image_is_returned_unchanged_for_plain_docker_reference(self):
        client = TiraClient()
        client.build_docker_image_from_code = MagicMock()

        actual = client._resolve_evaluator_image(RESOURCE_DIR, {}, "ghcr.io/example/evaluator:latest", MagicMock())

        self.assertEqual("ghcr.io/example/evaluator:latest", actual)
        client.build_docker_image_from_code.assert_not_called()

    def test_evaluator_image_is_built_from_local_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "datasets" / "example"
            evaluator_dir = dataset_path / "evaluator"
            dataset_path.mkdir(parents=True)
            evaluator_dir.mkdir()

            client = TiraClient()
            client.build_docker_image_from_code = MagicMock(
                return_value=("evaluator-docker-tag", None, None, None, None, None)
            )

            actual = client._resolve_evaluator_image(dataset_path, {}, "evaluator", MagicMock())

            self.assertEqual("evaluator-docker-tag", actual)
            client.build_docker_image_from_code.assert_called_once_with(
                evaluator_dir.resolve(), unittest.mock.ANY, False, docker_file=None
            )

    def test_evaluator_image_is_built_with_configured_dockerfile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "datasets" / "example"
            evaluator_dir = dataset_path / "evaluator"
            dataset_path.mkdir(parents=True)
            evaluator_dir.mkdir()

            client = TiraClient()
            client.build_docker_image_from_code = MagicMock(
                return_value=("evaluator-docker-tag", None, None, None, None, None)
            )

            client._resolve_evaluator_image(dataset_path, {"file": "Dockerfile.eval"}, "evaluator", MagicMock())

            client.build_docker_image_from_code.assert_called_once_with(
                evaluator_dir.resolve(),
                unittest.mock.ANY,
                False,
                docker_file=evaluator_dir.resolve() / "Dockerfile.eval",
            )

    @patch.object(TiraClient, "clone_git_repository")
    def test_evaluator_image_is_built_from_git_repository(self, clone_git_repository):
        clone_git_repository.return_value = Path("/tmp/cloned-repository")
        client = TiraClient()
        client.build_docker_image_from_code = MagicMock(
            return_value=("evaluator-docker-tag", None, None, None, None, None)
        )

        actual = client._resolve_evaluator_image(
            RESOURCE_DIR,
            {},
            "https://github.com/example/task/tree/main/evaluator",
            MagicMock(),
        )

        self.assertEqual("evaluator-docker-tag", actual)
        client.build_docker_image_from_code.assert_called_once_with(
            Path("/tmp/cloned-repository/evaluator"), unittest.mock.ANY, False, docker_file=None
        )

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


def _submit_code_with_mocks(tmp_upload_dir, skip_code_upload=False, directory_in_path="some-directory", **submit_code_kwargs):
    """Runs TiraClient.submit_code with all of its network/docker/git dependencies mocked out, so that only
    the pure bookkeeping logic (e.g., what gets written/uploaded) is exercised."""
    client = TiraClient()

    zipped_code = Path(tmp_upload_dir) / "zipped-source-code.zip"
    with zipfile.ZipFile(zipped_code, "w") as zf:
        zf.writestr("Dockerfile", "FROM bash\n")

    client.build_docker_image_from_code = MagicMock(
        return_value=("some-docker-tag", zipped_code, {"origin": "foo"}, "commit-1", "main", directory_in_path)
    )
    client.datasets = MagicMock()
    client.get_dataset = MagicMock(
        return_value={
            "mirrors": {"inputs": "some-mirror"},
            "format": ["jsonl"],
            "format_configuration": None,
        }
    )
    client.download_dataset = MagicMock(return_value=Path(tmp_upload_dir) / "dataset-input")
    client.local_execution = MagicMock()
    client.local_execution.extract_entrypoint.return_value = "some-command"
    client.upload_run_anonymous = MagicMock(return_value={"uuid": "some-uuid"})
    client.add_docker_software = MagicMock(return_value={"display_name": "some-software"})

    with patch("tira.tira_run.guess_vm_id_of_user", return_value="team-1"), patch(
        "tira.io_utils.verify_images_can_be_build_and_pushed", return_value=(_fmt.OK, "ok")
    ), patch("tira.io_utils.verify_images_are_in_correct_format", return_value=(_fmt.OK, "ok")), patch(
        "tira.io_utils.resolve_mount_directory", return_value=None
    ), patch(
        "tira.third_party_integrations.temporary_directory", return_value=Path(tmp_upload_dir) / "output"
    ), patch(
        "tira.tira_client.check_format", return_value=(_fmt.OK, "ok")
    ), patch(
        "tira.tira_run.push_image", return_value="pushed-image-tag"
    ), patch(
        "tira.io_utils.huggingface_model_mounts", return_value={}
    ):
        (Path(tmp_upload_dir) / "output").mkdir()
        client.submit_code(
            Path(tmp_upload_dir),
            "task",
            dataset_id="dataset",
            dry_run=False,
            skip_code_upload=skip_code_upload,
            **submit_code_kwargs,
        )

    return client


class TestSkipCodeUpload(unittest.TestCase):
    def test_source_code_zip_is_uploaded_by_default(self):
        with tempfile.TemporaryDirectory() as tmp_upload_dir:
            client = _submit_code_with_mocks(tmp_upload_dir, skip_code_upload=False)

            client.upload_run_anonymous.assert_called_once()
            uploaded_dir = client.upload_run_anonymous.call_args[0][0]
            self.assertTrue((Path(uploaded_dir) / "source-code.zip").exists())

    def test_source_code_zip_is_omitted_when_skip_code_upload_is_set(self):
        with tempfile.TemporaryDirectory() as tmp_upload_dir:
            client = _submit_code_with_mocks(tmp_upload_dir, skip_code_upload=True)

            client.upload_run_anonymous.assert_called_once()
            uploaded_dir = client.upload_run_anonymous.call_args[0][0]
            self.assertFalse((Path(uploaded_dir) / "source-code.zip").exists())
            self.assertTrue((Path(uploaded_dir) / "submission-metadata.yml").exists())


class TestSubmissionMetadataYmlContent(unittest.TestCase):
    """Tests that the submission-metadata.yml written by submit_code (see tira_client.py) contains all the
    metadata that is also uploaded to the server, so that a submission's exact source code, command, and
    context can be reconstructed later (e.g., via 'tira-cli run local --compile-from-code')."""

    def test_submission_metadata_yml_contains_all_expected_fields(self):
        with tempfile.TemporaryDirectory() as tmp_upload_dir:
            client = _submit_code_with_mocks(
                tmp_upload_dir,
                skip_code_upload=False,
                command="some-command",
                user_id="team-1",
                mount_hf_model=["some-model"],
                forward_environment_variable=["OPENAI_API_KEY"],
                tira_cli_command="tira-cli code-submission --path some/path --task task",
            )

            uploaded_dir = client.upload_run_anonymous.call_args[0][0]
            with open(Path(uploaded_dir) / "submission-metadata.yml") as f:
                submission_metadata = yaml.safe_load(f)

        self.assertEqual(
            {
                "tira_cli_command": "tira-cli code-submission --path some/path --task task",
                "task_id": "task",
                "user_id": "team-1",
                "dataset_id": "dataset",
                "command": "some-command",
                "source_code_remotes": {"origin": "foo"},
                "source_code_commit": "commit-1",
                "source_code_active_branch": "main",
                "source_code_directory": "some-directory",
                "mount_hf_model": ["some-model"],
                "workflow_configuration": None,
                "forward_environment_variable": ["OPENAI_API_KEY"],
                "cache_behaviour": None,
                "mount_config": None,
            },
            submission_metadata,
        )

    def test_submission_metadata_yml_reflects_repository_root_submission(self):
        with tempfile.TemporaryDirectory() as tmp_upload_dir:
            client = _submit_code_with_mocks(tmp_upload_dir, directory_in_path="")

            uploaded_dir = client.upload_run_anonymous.call_args[0][0]
            with open(Path(uploaded_dir) / "submission-metadata.yml") as f:
                submission_metadata = yaml.safe_load(f)

        self.assertEqual("", submission_metadata["source_code_directory"])

