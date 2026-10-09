import unittest
from pathlib import Path
from unittest.mock import patch

from tira.tira_cli import (
    _evaluation_timestamp,
    _parse_tira_id_timestamp,
    _reconstruct_code_submission_command,
    admin_re_run_evaluations,
    code_submission_command,
    dataset_submission_command,
    parse_metadata_args,
    requires_mount_workflow,
    setup_dataset_submission_command,
    setup_upload_command,
)


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

        dataset_submission_command(
            path="some/path", task="some-task", dry_run=False, split="train", skip_baseline=False
        )

        _, kwargs = mock_client.submit_dataset.call_args
        self.assertIsNone(kwargs["forward_environment_variable"])


class TestReconstructCodeSubmissionCommand(unittest.TestCase):
    def _reconstruct(self, **overrides):
        defaults = {
            "path": Path("some/path"),
            "task": "some-task",
            "dry_run": False,
            "allow_network": False,
            "command": None,
            "dataset": None,
            "mount_hf_model": None,
            "tira_vm_id": None,
            "set_properties": None,
            "file": None,
            "external_docker_registry": None,
            "forward_environment_variable": None,
            "build_args": None,
            "mount_directory": None,
            "mount_cache": None,
            "platform": None,
            "cache_behaviour": None,
        }
        defaults.update(overrides)
        return _reconstruct_code_submission_command(**defaults)

    def test_reconstructs_minimal_command(self):
        actual = self._reconstruct()
        self.assertEqual(actual, "tira-cli code-submission --path some/path --task some-task")

    def test_reconstructs_dry_run_and_allow_network_flags(self):
        actual = self._reconstruct(dry_run=True, allow_network=True)
        self.assertIn("--dry-run", actual)
        self.assertIn("--allow-network", actual)

    def test_omits_flags_that_are_not_set(self):
        actual = self._reconstruct()
        for flag in (
            "--dry-run",
            "--allow-network",
            "--command",
            "--dataset",
            "--set",
            "--build-args",
            "--external-docker-registry",
            "--mount-hf-model",
            "--mount-directory",
            "--mount-cache",
            "--forward-environment-variable",
            "--tira-vm-id",
            "--file",
            "--platform",
            "--cache-behaviour",
            "--skip-code-upload",
        ):
            self.assertNotIn(flag, actual)

    def test_reconstructs_skip_code_upload_flag(self):
        actual = self._reconstruct(skip_code_upload=True)
        self.assertIn("--skip-code-upload", actual)

    def test_reconstructs_all_scalar_options(self):
        actual = self._reconstruct(
            command="python3 run.py",
            dataset="my-dataset",
            tira_vm_id="team-1",
            file=Path("Dockerfile.gpu"),
            external_docker_registry="ghcr.io/some/registry",
            build_args="--output type=docker",
            platform="linux/amd64",
            cache_behaviour="deterministic",
        )
        self.assertEqual(
            actual,
            'tira-cli code-submission --path some/path --task some-task --command "python3 run.py" '
            '--dataset my-dataset --build-args "--output type=docker" '
            "--external-docker-registry ghcr.io/some/registry --tira-vm-id team-1 --file Dockerfile.gpu "
            "--platform linux/amd64 --cache-behaviour deterministic",
        )

    def test_reconstructs_repeated_list_options(self):
        actual = self._reconstruct(
            mount_hf_model=["model/a", "model/b"],
            mount_directory=["$IN=some/run"],
            mount_cache=["$CACHE=some/cache"],
            forward_environment_variable=["OPENAI_API_KEY", "OPENAI_BASE_URL"],
            set_properties=["key1=value 1", "key2=value2"],
        )
        self.assertIn("--mount-hf-model model/a model/b", actual)
        self.assertIn("--mount-directory $IN=some/run", actual)
        self.assertIn("--mount-cache $CACHE=some/cache", actual)
        self.assertIn("--forward-environment-variable OPENAI_API_KEY OPENAI_BASE_URL", actual)
        self.assertIn('--set "key1=value 1" --set key2=value2', actual)

    def test_quotes_values_containing_spaces(self):
        actual = self._reconstruct(path=Path("some path with spaces"), command="python3 run.py --verbose")
        self.assertIn('--path "some path with spaces"', actual)
        self.assertIn('--command "python3 run.py --verbose"', actual)

    def test_does_not_quote_values_without_spaces(self):
        actual = self._reconstruct(dataset="my-dataset")
        self.assertIn("--dataset my-dataset", actual)
        self.assertNotIn('"my-dataset"', actual)


class TestCodeSubmissionCommandForwardsReconstructedCliCommand(unittest.TestCase):
    @patch("tira.tira_cli.RestClient")
    def test_code_submission_command_forwards_tira_cli_command_to_client(self, mock_rest_client):
        mock_client = mock_rest_client.return_value

        code_submission_command(
            path=Path("some/path"),
            task="some-task",
            dry_run=True,
            allow_network=False,
            command=None,
            dataset=None,
            mount_hf_model=None,
            tira_vm_id=None,
            set=None,
            file=None,
            external_docker_registry=None,
            forward_environment_variable=None,
            build_args=None,
            mount_directory=None,
            mount_cache=None,
            platform=None,
            cache_behaviour=None,
        )

        _, kwargs = mock_client.submit_code.call_args
        self.assertEqual(
            kwargs["tira_cli_command"],
            "tira-cli code-submission --path some/path --task some-task --dry-run",
        )

    @patch("tira.tira_cli.RestClient")
    def test_code_submission_command_forwards_skip_code_upload_to_client(self, mock_rest_client):
        mock_client = mock_rest_client.return_value

        code_submission_command(
            path=Path("some/path"),
            task="some-task",
            dry_run=True,
            allow_network=False,
            command=None,
            dataset=None,
            mount_hf_model=None,
            tira_vm_id=None,
            set=None,
            file=None,
            external_docker_registry=None,
            forward_environment_variable=None,
            build_args=None,
            mount_directory=None,
            mount_cache=None,
            platform=None,
            cache_behaviour=None,
            skip_code_upload=True,
        )

        _, kwargs = mock_client.submit_code.call_args
        self.assertTrue(kwargs["skip_code_upload"])
        self.assertIn("--skip-code-upload", kwargs["tira_cli_command"])

    @patch("tira.tira_cli.RestClient")
    def test_code_submission_command_does_not_use_unrelated_arguments_from_sys_argv(self, mock_rest_client):
        mock_client = mock_rest_client.return_value

        with patch("sys.argv", ["tira-cli", "code-submission", "--path", "unrelated/path", "--secret-token", "abc"]):
            code_submission_command(
                path=Path("some/path"),
                task="some-task",
                dry_run=False,
                allow_network=False,
                command=None,
                dataset=None,
                mount_hf_model=None,
                tira_vm_id=None,
                set=None,
                file=None,
                external_docker_registry=None,
                forward_environment_variable=None,
                build_args=None,
                mount_directory=None,
                mount_cache=None,
                platform=None,
                cache_behaviour=None,
            )

        _, kwargs = mock_client.submit_code.call_args
        self.assertNotIn("unrelated/path", kwargs["tira_cli_command"])
        self.assertNotIn("--secret-token", kwargs["tira_cli_command"])
        self.assertEqual(
            kwargs["tira_cli_command"],
            "tira-cli code-submission --path some/path --task some-task",
        )


class TestParseMetadataArgs(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(parse_metadata_args(None))

    def test_empty_list_returns_none(self):
        self.assertIsNone(parse_metadata_args([]))

    def test_single_entry_is_parsed(self):
        self.assertEqual({"track": "main"}, parse_metadata_args(["track=main"]))

    def test_multiple_entries_are_parsed(self):
        self.assertEqual(
            {"track": "main", "team_name": "Group 42"},
            parse_metadata_args(["track=main", "team_name=Group 42"]),
        )

    def test_value_may_contain_equals_sign(self):
        self.assertEqual({"formula": "a=b+c"}, parse_metadata_args(["formula=a=b+c"]))

    def test_missing_equals_sign_raises(self):
        with self.assertRaises(ValueError):
            parse_metadata_args(["track"])


class TestUploadCommandMetadataArgument(unittest.TestCase):
    def _parse(self, argv):
        import argparse

        parser = argparse.ArgumentParser()
        setup_upload_command(parser)
        return parser.parse_args(argv)

    def test_metadata_defaults_to_none(self):
        args = self._parse(["--directory", "some/path"])
        self.assertIsNone(args.metadata)

    def test_metadata_can_be_passed_multiple_times(self):
        args = self._parse(["--directory", "some/path", "--metadata", "track=main", "--metadata", "team_name=Group 42"])
        self.assertEqual(["track=main", "team_name=Group 42"], args.metadata)


class TestUploadCommandAttachesMetadata(unittest.TestCase):
    """Covers the authenticated-upload flow that calls update_upload_metadata() after claim_ownership()."""

    def _run_upload_command(self, tmp_path, metadata, mock_rest_client, system_description="auto-detected description"):
        mock_client = mock_rest_client.return_value
        mock_client.api_key_is_valid.return_value = True
        mock_client.get_dataset.return_value = {"default_task": "some-task"}
        mock_client.validate_upload_metadata.side_effect = lambda task_id, md: md
        mock_client.upload_run_anonymous.return_value = {"uuid": "some-uuid"}
        mock_client.claim_ownership.return_value = {"status": "0", "upload_group": "some-upload-id"}

        with patch("tira.tira_cli.guess_system_details") as mock_guess_system_details, patch(
            "tira.tira_cli.guess_vm_id_of_user"
        ) as mock_guess_vm_id_of_user:
            mock_guess_system_details.return_value = {
                "tag": "my-system",
                "description": system_description,
                "team": "my-team",
            }
            mock_guess_vm_id_of_user.return_value = "my-team"

            from tira.tira_cli import upload_command

            ret = upload_command(
                dataset="some-dataset",
                directory=tmp_path,
                dry_run=False,
                system=None,
                metadata=metadata,
            )

        self.assertEqual(0, ret)
        return mock_client

    @patch("tira.tira_cli.RestClient")
    def test_metadata_with_description_overrides_auto_detected_description(self, mock_rest_client):
        mock_client = self._run_upload_command(
            Path("."), ["description=my cool description goes here", "track=main"], mock_rest_client
        )

        args, _ = mock_client.update_upload_metadata.call_args
        self.assertEqual("my cool description goes here", args[4])

    @patch("tira.tira_cli.RestClient")
    def test_metadata_without_description_falls_back_to_auto_detected_description(self, mock_rest_client):
        mock_client = self._run_upload_command(Path("."), ["track=main"], mock_rest_client)

        args, _ = mock_client.update_upload_metadata.call_args
        self.assertEqual("auto-detected description", args[4])

    @patch("tira.tira_cli.RestClient")
    def test_update_upload_metadata_is_not_called_without_metadata(self, mock_rest_client):
        mock_client = self._run_upload_command(Path("."), None, mock_rest_client)

        mock_client.update_upload_metadata.assert_not_called()


class TestParseTiraIdTimestamp(unittest.TestCase):
    def test_valid_timestamp_is_parsed(self):
        from datetime import datetime

        self.assertEqual(datetime(2026, 10, 2, 21, 9, 11), _parse_tira_id_timestamp("2026-10-02-21-09-11"))

    def test_invalid_timestamp_returns_none(self):
        self.assertIsNone(_parse_tira_id_timestamp("not-a-timestamp"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_parse_tira_id_timestamp(""))


class TestEvaluationTimestamp(unittest.TestCase):
    def test_extracts_timestamp_from_evaluation_run_id(self):
        from datetime import datetime

        run_id = "2026-10-02-21-09-11-evaluates-2026-10-02-23-08-58"
        self.assertEqual(datetime(2026, 10, 2, 21, 9, 11), _evaluation_timestamp(run_id))

    def test_returns_none_without_evaluates_marker(self):
        self.assertIsNone(_evaluation_timestamp("2026-10-02-21-09-11"))

    def test_returns_none_for_unparsable_prefix(self):
        self.assertIsNone(_evaluation_timestamp("not-a-timestamp-evaluates-2026-10-02-23-08-58"))


class TestAdminReRunEvaluations(unittest.TestCase):
    def _submissions_df(self, rows):
        import pandas as pd

        return pd.DataFrame(rows)

    def _evaluations_df(self, rows):
        import pandas as pd

        return pd.DataFrame(rows)

    def _run_and_capture_stdout(self, **kwargs):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = admin_re_run_evaluations(**kwargs)
        return ret, buf.getvalue()

    @patch("tira.tira_cli.RestClient")
    def test_invalid_after_datetime_returns_error_without_calling_client(self, mock_rest_client):
        mock_client = mock_rest_client.return_value

        ret = admin_re_run_evaluations(dataset="some-dataset", after="not-a-datetime")

        self.assertEqual(1, ret)
        mock_client.get_dataset.assert_not_called()

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_run_without_any_evaluation_is_reported_and_re_evaluated(self, mock_rest_client, mock_sleep):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-10-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df([])

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-01-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertIn("2026-10-01-00-00-00", output)
        self.assertIn("no evaluation", output)
        mock_client.submissions.assert_called_once_with("my-task", "my-dataset")
        mock_client.evaluations.assert_called_once_with("my-task", "my-dataset", join_submissions=False)
        mock_client.evaluate_run.assert_called_once_with("team-1", "my-dataset", "2026-10-01-00-00-00")
        mock_sleep.assert_called_once_with(10)

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_run_with_stale_evaluation_is_reported_and_re_evaluated(self, mock_rest_client, mock_sleep):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-01-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df(
            [
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2025-12-31-00-00-00-evaluates-2026-01-01-00-00-00",
                }
            ]
        )

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-02-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertIn("2026-01-01-00-00-00", output)
        self.assertIn("last evaluated at", output)
        mock_client.evaluate_run.assert_called_once_with("team-1", "my-dataset", "2026-01-01-00-00-00")

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_run_with_recent_evaluation_is_not_reported_nor_re_evaluated(self, mock_rest_client, mock_sleep):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-01-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df(
            [
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2026-03-01-00-00-00-evaluates-2026-01-01-00-00-00",
                }
            ]
        )

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-02-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertIn("All runs", output)
        self.assertNotIn("2026-01-01-00-00-00", output)
        mock_client.evaluate_run.assert_not_called()

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_evaluation_runs_are_excluded_from_submissions_check(self, mock_rest_client, mock_sleep):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [
                {"run_id": "2026-01-01-00-00-00", "team": "team-1", "is_evaluation": False},
                {
                    "run_id": "2025-12-31-00-00-00-evaluates-2026-01-01-00-00-00",
                    "team": "team-1",
                    "is_evaluation": True,
                },
            ]
        )
        mock_client.evaluations.return_value = self._evaluations_df(
            [
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2026-03-01-00-00-00-evaluates-2026-01-01-00-00-00",
                }
            ]
        )

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-02-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertIn("All runs", output)
        self.assertNotIn("2025-12-31-00-00-00-evaluates", output)
        mock_client.evaluate_run.assert_not_called()

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_deleted_runs_without_evaluation_are_not_reported_nor_re_evaluated(self, mock_rest_client, mock_sleep):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [
                {
                    "run_id": "2026-10-01-00-00-00",
                    "team": "team-1",
                    "is_evaluation": False,
                    "deleted": True,
                }
            ]
        )
        mock_client.evaluations.return_value = self._evaluations_df([])

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-01-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertIn("All runs", output)
        self.assertNotIn("2026-10-01-00-00-00", output)
        mock_client.evaluate_run.assert_not_called()

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_runs_of_deleted_software_without_evaluation_are_not_reported_nor_re_evaluated(
        self, mock_rest_client, mock_sleep
    ):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [
                {
                    "run_id": "2026-10-01-00-00-00",
                    "team": "team-1",
                    "is_evaluation": False,
                    "deleted": False,
                    "software_deleted": True,
                }
            ]
        )
        mock_client.evaluations.return_value = self._evaluations_df([])

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-01-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertIn("All runs", output)
        self.assertNotIn("2026-10-01-00-00-00", output)
        mock_client.evaluate_run.assert_not_called()

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_re_evaluation_is_retried_and_eventually_reported_as_failed(self, mock_rest_client, mock_sleep):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-10-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df([])
        mock_client.evaluate_run.side_effect = ValueError("evaluator is unavailable")

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-01-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertEqual(3, mock_client.evaluate_run.call_count)
        self.assertIn("Failed to start evaluation", output)
        self.assertIn("evaluator is unavailable", output)

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_re_evaluation_succeeds_after_a_retry(self, mock_rest_client, mock_sleep):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-10-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df([])
        mock_client.evaluate_run.side_effect = [ValueError("transient error"), None]

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-01-01-00-00-00")

        self.assertEqual(0, ret)
        self.assertEqual(2, mock_client.evaluate_run.call_count)
        self.assertNotIn("Failed to start evaluation", output)

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_old_evaluation_of_an_untriggered_run_is_deleted(self, mock_rest_client, mock_sleep):
        # The run already has a recent evaluation, so no new evaluation is triggered for it. Its older,
        # now-superseded evaluation should be deleted.
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-01-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df(
            [
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2025-01-01-00-00-00-evaluates-2026-01-01-00-00-00",
                },
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2026-03-01-00-00-00-evaluates-2026-01-01-00-00-00",
                },
            ]
        )

        ret, output = self._run_and_capture_stdout(dataset="my-dataset", after="2026-02-01-00-00-00")

        self.assertEqual(0, ret)
        mock_client.evaluate_run.assert_not_called()
        mock_client.delete_run.assert_called_once_with(
            "team-1", "my-dataset", "2025-01-01-00-00-00-evaluates-2026-01-01-00-00-00"
        )
        self.assertIn("Deleting outdated evaluation", output)
        self.assertIn("2025-01-01-00-00-00-evaluates-2026-01-01-00-00-00", output)
        mock_sleep.assert_called_once_with(5)

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_old_evaluation_of_a_triggered_run_is_not_deleted(self, mock_rest_client, mock_sleep):
        # The run has no recent evaluation, so a new one is triggered for it. Its only (stale) evaluation
        # must not be deleted, regardless of whether the triggered re-evaluation succeeds.
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-01-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df(
            [
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2025-12-31-00-00-00-evaluates-2026-01-01-00-00-00",
                }
            ]
        )

        ret, _ = self._run_and_capture_stdout(dataset="my-dataset", after="2026-02-01-00-00-00")

        self.assertEqual(0, ret)
        mock_client.evaluate_run.assert_called_once_with("team-1", "my-dataset", "2026-01-01-00-00-00")
        mock_client.delete_run.assert_not_called()

    @patch("time.sleep")
    @patch("tira.tira_cli.RestClient")
    def test_failure_to_delete_an_old_evaluation_is_logged_and_does_not_fail_the_command(
        self, mock_rest_client, mock_sleep
    ):
        mock_client = mock_rest_client.return_value
        mock_client.get_dataset.return_value = {"default_task": "my-task"}
        mock_client.submissions.return_value = self._submissions_df(
            [{"run_id": "2026-01-01-00-00-00", "team": "team-1", "is_evaluation": False}]
        )
        mock_client.evaluations.return_value = self._evaluations_df(
            [
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2025-01-01-00-00-00-evaluates-2026-01-01-00-00-00",
                },
                {
                    "run_id": "2026-01-01-00-00-00",
                    "team": "team-1",
                    "evaluation_run_id": "2026-03-01-00-00-00-evaluates-2026-01-01-00-00-00",
                },
            ]
        )
        mock_client.delete_run.side_effect = ValueError("run is still needed")

        ret, _ = self._run_and_capture_stdout(dataset="my-dataset", after="2026-02-01-00-00-00")

        self.assertEqual(0, ret)
        mock_client.delete_run.assert_called_once()
