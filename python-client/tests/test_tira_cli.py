import unittest
from unittest.mock import patch

from tira.tira_cli import dataset_submission_command, requires_mount_workflow, setup_dataset_submission_command


class TestRequiresMountWorkflow(unittest.TestCase):
    def test_non_cache_dir_mount_requires_mount_workflow(self):
        self.assertTrue(requires_mount_workflow({"mount_config": {"NUGGETS": "ro"}}))

    def test_cache_dir_mount_requires_mount_workflow(self):
        self.assertTrue(requires_mount_workflow({"mount_config": {"CACHE_DIR": "rw"}}))

    def test_cache_behaviour_requires_mount_workflow(self):
        self.assertTrue(requires_mount_workflow({"cache_behaviour": "deterministic"}))

    def test_system_without_mounts_uses_direct_execution(self):
        self.assertFalse(requires_mount_workflow({}))
        self.assertFalse(requires_mount_workflow({"mount_config": {}}))


class TestDatasetSubmissionForwardEnvironmentVariable(unittest.TestCase):
    def _parse(self, argv):
        import argparse

        parser = argparse.ArgumentParser()
        setup_dataset_submission_command(parser)
        return parser.parse_args(argv)

    def test_forward_environment_variable_defaults_to_empty_list(self):
        args = self._parse(["--path", "some/path", "--task", "some-task", "--split", "train"])
        self.assertEqual(args.forward_environment_variable, [])

    def test_forward_environment_variable_is_parsed(self):
        args = self._parse(
            [
                "--path",
                "some/path",
                "--task",
                "some-task",
                "--split",
                "train",
                "--forward-environment-variable",
                "OPENAI_API_KEY",
                "OPENAI_BASE_URL",
            ]
        )
        self.assertEqual(args.forward_environment_variable, ["OPENAI_API_KEY", "OPENAI_BASE_URL"])

    @patch("tira.tira_cli.RestClient")
    def test_dataset_submission_command_forwards_environment_variable_to_client(self, mock_rest_client):
        mock_client = mock_rest_client.return_value
        mock_client.submit_dataset.return_value = {"inputs_zip": "some/path.zip"}

        dataset_submission_command(
            path="some/path",
            task="some-task",
            dry_run=False,
            split="train",
            skip_baseline=False,
            forward_environment_variable=["OPENAI_API_KEY"],
        )

        _, kwargs = mock_client.submit_dataset.call_args
        self.assertEqual(kwargs["forward_environment_variable"], ["OPENAI_API_KEY"])

    @patch("tira.tira_cli.RestClient")
    def test_dataset_submission_command_defaults_forward_environment_variable_to_none(self, mock_rest_client):
        mock_client = mock_rest_client.return_value
        mock_client.submit_dataset.return_value = {"inputs_zip": "some/path.zip"}

        dataset_submission_command(path="some/path", task="some-task", dry_run=False, split="train", skip_baseline=False)

        _, kwargs = mock_client.submit_dataset.call_args
        self.assertIsNone(kwargs["forward_environment_variable"])
