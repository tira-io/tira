import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tira.tira_cli import parse_args, run_remote


class FakeRestClient:
    calls = []
    private_calls = []
    started = set()
    run_calls = []

    def __init__(self):
        pass

    @classmethod
    def reset(cls):
        cls.calls = []
        cls.private_calls = []
        cls.started = set()
        cls.run_calls = []

    def submissions_with_evaluation_or_none(self, task, dataset, team, software):
        type(self).calls.append((task, dataset, team, software))
        model = "Qwen/Qwen2.5-7B-Instruct" if software == "software-a" else "other-model"
        if (task, dataset, team, software) in type(self).started:
            model = "Qwen/Qwen2.5-7B-Instruct"
        return [
            {
                "run_id": f"{software}-{dataset}",
                "task": task,
                "dataset": dataset,
                "team": team,
                "software": software,
                "evaluation": {"score": 1.0, "Model": model},
            }
        ]

    def private_system_details(self, approach):
        type(self).private_calls.append(approach)
        if approach.endswith("/software-b"):
            return {
                "forward_environment_variable": ["OPENAI_API_KEY"],
                "mount_config": ["WORK_DIR"],
                "docker_software_id": "42",
            }

        return {"forward_environment_variable": [], "mount_config": [], "docker_software_id": "41"}

    def run_software(self, approach, dataset, resources, rerank_dataset="none", software_id=None, json_payload={}):
        task, team, software = approach.split("/")
        type(self).run_calls.append((approach, dataset, resources, software_id, json_payload))
        type(self).started.add((task, dataset, team, software))


class TestRunRemote(unittest.TestCase):
    def test_parse_args_registers_remote_run_command(self):
        original_argv = list(sys.argv)
        try:
            sys.argv = [
                "tira-cli",
                "run",
                "remote",
                "--approach",
                "task/team-a/software-a",
                "task/team-b/software-b",
                "--dataset",
                "dataset-a",
                "dataset-b",
                "--resources",
                "medium-resources",
                "--parallelism",
                "3",
            ]
            args = parse_args()
        finally:
            sys.argv = original_argv

        self.assertEqual(
            ["task/team-a/software-a", "task/team-b/software-b"],
            args.approach,
        )
        self.assertEqual(["dataset-a", "dataset-b"], args.dataset)
        self.assertEqual("medium-resources", args.resources)
        self.assertEqual(3, args.parallelism)
        self.assertIsNone(args.require)
        self.assertEqual([], args.forward_environment_variable)
        self.assertEqual([], args.mount_directory)
        self.assertEqual([], args.mount_cache)

    def test_parse_args_registers_require_filter(self):
        original_argv = list(sys.argv)
        try:
            sys.argv = [
                "tira-cli",
                "run",
                "remote",
                "--approach",
                "task/team-a/software-a",
                "--dataset",
                "dataset-a",
                "--require",
                "evaluation.Model==Qwen/Qwen2.5-7B-Instruct",
                "--require",
                "team==team-a",
            ]
            args = parse_args()
        finally:
            sys.argv = original_argv

        self.assertEqual(
            [
                "evaluation.Model==Qwen/Qwen2.5-7B-Instruct",
                "team==team-a",
            ],
            args.require,
        )

    def test_parse_args_registers_forwarding_arguments(self):
        original_argv = list(sys.argv)
        try:
            sys.argv = [
                "tira-cli",
                "run",
                "remote",
                "--approach",
                "task/team-a/software-a",
                "--dataset",
                "dataset-a",
                "--forward-environment-variable",
                "OPENAI_API_KEY",
                "OPENAI_MODEL",
                "--mount-directory",
                "$INPUT_RUN=/tmp/input-run",
                "--mount-cache",
                "$WORK_DIR=/tmp/work-dir",
            ]
            args = parse_args()
        finally:
            sys.argv = original_argv

        self.assertEqual(["OPENAI_API_KEY", "OPENAI_MODEL"], args.forward_environment_variable)
        self.assertEqual(["$INPUT_RUN=/tmp/input-run"], args.mount_directory)
        self.assertEqual(["$WORK_DIR=/tmp/work-dir"], args.mount_cache)

    def test_run_remote_counts_finished_and_pending_executions(self):
        FakeRestClient.reset()

        with patch("tira.tira_cli.RestClient", FakeRestClient):
            stdout = io.StringIO()
            with patch.dict(os.environ, {}, clear=False), redirect_stdout(stdout):
                actual = run_remote(
                    approach=["task/team-a/software-a", "task/team-b/software-b"],
                    dataset=["dataset-a", "dataset-b"],
                    resources="medium-resources",
                    parallelism=2,
                )

        self.assertEqual(0, actual)
        self.assertEqual(4, len(FakeRestClient.calls))
        self.assertEqual(
            [
                "4 executions have already been finished, 0 executions are about to be started.",
                "No executions are waiting to be started.",
            ],
            stdout.getvalue().strip().splitlines(),
        )
        self.assertEqual([], FakeRestClient.private_calls)
        self.assertEqual([], FakeRestClient.run_calls)

    def test_run_remote_queues_executions_not_meeting_requirement(self):
        FakeRestClient.reset()

        with patch("tira.tira_cli.RestClient", FakeRestClient), patch("tira.tira_cli.time.sleep") as sleep_mock:
            stdout = io.StringIO()
            with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-secret"}, clear=False), redirect_stdout(stdout):
                actual = run_remote(
                    approach=["task/team-a/software-a", "task/team-b/software-b"],
                    dataset=["dataset-a", "dataset-b"],
                    resources="medium-resources",
                    parallelism=2,
                    require=["evaluation.Model==Qwen/Qwen2.5-7B-Instruct"],
                    forward_environment_variable=["OPENAI_API_KEY"],
                    mount_cache=["$WORK_DIR=EMPTY_DIR"],
                )

        self.assertEqual(0, actual)
        self.assertEqual(
            [
                "2 executions have already been finished, 2 executions are about to be started.",
                "The following executions are about to be started:",
                "- task/team-b/software-b on dataset-a with medium-resources",
                "- task/team-b/software-b on dataset-b with medium-resources",
                "Waiting 15 seconds before starting executions...",
                "Started task/team-b/software-b on dataset-a. 1 executions are still waiting to be started.",
                "Started task/team-b/software-b on dataset-b. 0 executions are still waiting to be started.",
                "Finished task/team-b/software-b on dataset-a.",
                "Finished task/team-b/software-b on dataset-b.",
                "No executions are waiting to be started.",
            ],
            stdout.getvalue().strip().splitlines(),
        )
        self.assertEqual(
            ["task/team-b/software-b"],
            FakeRestClient.private_calls,
        )
        self.assertEqual(
            [
                (
                    "task/team-b/software-b",
                    "dataset-a",
                    "medium-resources",
                    "42",
                    {
                        "forward_environment_variable": {"OPENAI_API_KEY": "openai-secret"},
                        "mount_config": {"WORK_DIR": "EMPTY_DIR"},
                    },
                ),
                (
                    "task/team-b/software-b",
                    "dataset-b",
                    "medium-resources",
                    "42",
                    {
                        "forward_environment_variable": {"OPENAI_API_KEY": "openai-secret"},
                        "mount_config": {"WORK_DIR": "EMPTY_DIR"},
                    },
                ),
            ],
            FakeRestClient.run_calls,
        )
        sleep_mock.assert_any_call(15)

    def test_run_remote_fails_if_pending_execution_misses_forwarding(self):
        FakeRestClient.reset()

        with patch("tira.tira_cli.RestClient", FakeRestClient):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                actual = run_remote(
                    approach=["task/team-a/software-a", "task/team-b/software-b"],
                    dataset=["dataset-a", "dataset-b"],
                    resources="medium-resources",
                    parallelism=2,
                    require=["evaluation.Model==Qwen/Qwen2.5-7B-Instruct"],
                )

        self.assertEqual(1, actual)
        self.assertEqual(
            ["task/team-b/software-b"],
            FakeRestClient.private_calls,
        )
        self.assertEqual([], FakeRestClient.run_calls)

    def test_run_remote_accepts_pending_execution_with_required_forwarding(self):
        FakeRestClient.reset()

        with patch("tira.tira_cli.RestClient", FakeRestClient), patch("tira.tira_cli.time.sleep") as sleep_mock:
            stdout = io.StringIO()
            with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-secret"}, clear=False), redirect_stdout(stdout):
                actual = run_remote(
                    approach=["task/team-a/software-a", "task/team-b/software-b"],
                    dataset=["dataset-a", "dataset-b"],
                    resources="medium-resources",
                    parallelism=1,
                    require=["evaluation.Model==Qwen/Qwen2.5-7B-Instruct"],
                    forward_environment_variable=["OPENAI_API_KEY"],
                    mount_cache=["$WORK_DIR=EMPTY_DIR"],
                )

        self.assertEqual(0, actual)
        self.assertEqual(
            [
                "2 executions have already been finished, 2 executions are about to be started.",
                "The following executions are about to be started:",
                "- task/team-b/software-b on dataset-a with medium-resources",
                "- task/team-b/software-b on dataset-b with medium-resources",
                "Waiting 15 seconds before starting executions...",
                "Started task/team-b/software-b on dataset-a. 1 executions are still waiting to be started.",
                "Finished task/team-b/software-b on dataset-a.",
                "Started task/team-b/software-b on dataset-b. 0 executions are still waiting to be started.",
                "Finished task/team-b/software-b on dataset-b.",
                "No executions are waiting to be started.",
            ],
            stdout.getvalue().strip().splitlines(),
        )
        self.assertEqual(
            [
                ("task/team-b/software-b", "dataset-a", "medium-resources"),
                ("task/team-b/software-b", "dataset-b", "medium-resources"),
            ],
            [(call[0], call[1], call[2]) for call in FakeRestClient.run_calls],
        )
        sleep_mock.assert_any_call(15)

    def test_run_remote_fails_if_forwarded_environment_value_is_missing(self):
        FakeRestClient.reset()

        with patch("tira.tira_cli.RestClient", FakeRestClient):
            stdout = io.StringIO()
            with patch.dict(os.environ, {}, clear=False), redirect_stdout(stdout):
                with self.assertRaises(ValueError):
                    run_remote(
                        approach=["task/team-a/software-a", "task/team-b/software-b"],
                        dataset=["dataset-a", "dataset-b"],
                        resources="medium-resources",
                        parallelism=2,
                        require=["evaluation.Model==Qwen/Qwen2.5-7B-Instruct"],
                        forward_environment_variable=["OPENAI_API_KEY"],
                        mount_cache=["$WORK_DIR=EMPTY_DIR"],
                    )
