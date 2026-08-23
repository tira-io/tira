import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tira.io_utils import persist_mount_metadata
from tira.tira_cli import (
    build_mount_combos,
    get_run_mount_metadata,
    matches_requirements,
    parse_args,
    parse_run_on,
    resolve_run_on_candidates,
    run_remote,
    runs_matching_requirements,
)


class FakeRunOnRestClient:
    """A fake TiraClient that models multiple approaches with runs on multiple datasets, where 'NUGGETS_*'
    approaches have persisted mount metadata (i.e., they were themselves run with --run-on) that can be
    downloaded/read back via download_zip_to_cache_directory + the mounted-directories-metadata.yml file.
    """

    calls = []
    run_calls = []
    private_calls = []

    def __init__(self, tmp_dir=None):
        self.tmp_dir = tmp_dir or type(self).tmp_dir

    @classmethod
    def reset(cls, tmp_dir):
        cls.calls = []
        cls.run_calls = []
        cls.private_calls = []
        cls.tmp_dir = tmp_dir
        # runs[(task, dataset, team, software)] -> list of run dicts
        cls.runs = {}
        # mounted[run_id] -> {"NUGGETS": "run-id-of-mounted-nuggets-run"}
        cls.mounted = {}

    @classmethod
    def add_run(cls, task, dataset, team, software, run_id, mounted=None):
        key = (task, dataset, team, software)
        cls.runs.setdefault(key, []).append(
            {
                "run_id": run_id,
                "task": task,
                "dataset": dataset,
                "team": team,
                "software": software,
                "evaluation": {"score": 1.0},
            }
        )
        if mounted:
            cls.mounted[run_id] = mounted

    def submissions_with_evaluation_or_none(self, task, dataset, team, software):
        type(self).calls.append((task, dataset, team, software))
        return list(type(self).runs.get((task, dataset, team, software), []))

    def private_system_details(self, approach):
        type(self).private_calls.append(approach)
        return {"forward_environment_variable": [], "mount_config": [], "docker_software_id": "1"}

    def run_software(self, approach, dataset, resources, rerank_dataset="none", software_id=None, json_payload={}):
        type(self).run_calls.append((approach, dataset, resources, software_id, json_payload))

        # Simulate that the execution completes immediately: register a new run (with the mount metadata that
        # would have been persisted by the worker for the given mount_config), so that a subsequent poll for
        # completion (runs_matching_requirements) can detect it.
        task, team, software = approach.split("/")
        run_id = f"started-run-{len(type(self).run_calls)}"
        mounted = {
            variable: mount["run_id"]
            for variable, mount in json_payload.get("mount_config", {}).items()
            if isinstance(mount, dict) and "run_id" in mount
        }
        self.add_run(task, dataset, team, software, run_id, mounted=mounted or None)

    def download_zip_to_cache_directory(self, task, dataset, team, run_id):
        run_dir = Path(self.tmp_dir) / run_id
        output_dir = run_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        mounted = type(self).mounted.get(run_id)
        if mounted:
            dynamic_mounts = {
                var: {"source": "OUTPUT_OF_OTHER_EXECUTION", "run_id": rid} for var, rid in mounted.items()
            }
            persist_mount_metadata(run_dir, dynamic_mounts)
        return output_dir


class TestParseRunOn(unittest.TestCase):
    def test_parse_single_entry(self):
        self.assertEqual(
            {"NUGGETS": ["task/team/approach-a"]},
            parse_run_on(["NUGGETS=task/team/approach-a"]),
        )

    def test_parse_entry_with_dollar_prefix(self):
        self.assertEqual(
            {"NUGGETS": ["task/team/approach-a"]},
            parse_run_on(["$NUGGETS=task/team/approach-a"]),
        )

    def test_parse_multiple_approaches_for_same_variable(self):
        self.assertEqual(
            {"NUGGETS": ["task/team/approach-a", "task/team/approach-b", "task/team/approach-c"]},
            parse_run_on(
                [
                    "NUGGETS=task/team/approach-a",
                    "NUGGETS=task/team/approach-b",
                    "NUGGETS=task/team/approach-c",
                ]
            ),
        )

    def test_parse_multiple_variables(self):
        self.assertEqual(
            {"NUGGETS": ["task/team/a"], "SUMMARY": ["task/team/b"]},
            parse_run_on(["NUGGETS=task/team/a", "SUMMARY=task/team/b"]),
        )

    def test_parse_none_returns_empty_dict(self):
        self.assertEqual({}, parse_run_on(None))

    def test_parse_invalid_entry_raises(self):
        with self.assertRaises(ValueError):
            parse_run_on(["invalid-entry-without-equals"])


class TestResolveRunOnCandidatesAndCombos(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        FakeRunOnRestClient.reset(self.tmp_dir)

    def test_resolves_run_ids_for_each_variable(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-a", "run-a-1")
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-b", "run-b-1")

        candidates = resolve_run_on_candidates(
            client, {"NUGGETS": ["task/team/approach-a", "task/team/approach-b"]}, "dataset-a"
        )

        self.assertEqual({"NUGGETS": ["run-a-1", "run-b-1"]}, candidates)

    def test_deduplicates_run_ids(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-a", "run-a-1")

        # Same approach configured for the variable twice must not duplicate the run_id.
        candidates = resolve_run_on_candidates(
            client, {"NUGGETS": ["task/team/approach-a", "task/team/approach-a"]}, "dataset-a"
        )

        self.assertEqual({"NUGGETS": ["run-a-1"]}, candidates)

    def test_build_mount_combos_without_run_on_returns_single_empty_combo(self):
        self.assertEqual([{}], build_mount_combos({}))

    def test_build_mount_combos_cartesian_product_across_variables(self):
        combos = build_mount_combos({"NUGGETS": ["run-1", "run-2"], "SUMMARY": ["run-a"]})

        self.assertEqual(
            [
                {"NUGGETS": "run-1", "SUMMARY": "run-a"},
                {"NUGGETS": "run-2", "SUMMARY": "run-a"},
            ],
            combos,
        )

    def test_build_mount_combos_returns_empty_list_if_a_variable_has_no_candidates(self):
        self.assertEqual([], build_mount_combos({"NUGGETS": []}))


class TestDynamicRequirement(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        FakeRunOnRestClient.reset(self.tmp_dir)

    def test_matches_requirements_true_when_mounted_run_id_matches_combo(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-1", "run-1", mounted={"NUGGETS": "run-a-1"})
        run = FakeRunOnRestClient.runs[("task", "dataset-a", "team", "approach-1")][0]

        self.assertTrue(matches_requirements(run, ["output.NUGGETS"], {"NUGGETS": "run-a-1"}, client))

    def test_matches_requirements_false_when_mounted_run_id_differs(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-1", "run-1", mounted={"NUGGETS": "run-a-1"})
        run = FakeRunOnRestClient.runs[("task", "dataset-a", "team", "approach-1")][0]

        self.assertFalse(matches_requirements(run, ["output.NUGGETS"], {"NUGGETS": "run-a-2"}, client))

    def test_matches_requirements_false_when_no_metadata_is_persisted(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-1", "run-1")
        run = FakeRunOnRestClient.runs[("task", "dataset-a", "team", "approach-1")][0]

        self.assertFalse(matches_requirements(run, ["output.NUGGETS"], {"NUGGETS": "run-a-1"}, client))

    def test_raises_without_matching_run_on_variable(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-1", "run-1")
        run = FakeRunOnRestClient.runs[("task", "dataset-a", "team", "approach-1")][0]

        with self.assertRaises(ValueError):
            matches_requirements(run, ["output.NUGGETS"], {}, client)

    def test_raises_for_invalid_requirement_format(self):
        with self.assertRaises(ValueError):
            matches_requirements({}, ["not-a-valid-requirement"])

    def test_metadata_cache_avoids_repeated_downloads(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-1", "run-1", mounted={"NUGGETS": "run-a-1"})
        run = FakeRunOnRestClient.runs[("task", "dataset-a", "team", "approach-1")][0]

        cache = {}
        get_run_mount_metadata(client, run, cache)
        with patch.object(FakeRunOnRestClient, "download_zip_to_cache_directory") as mock_download:
            get_run_mount_metadata(client, run, cache)
            mock_download.assert_not_called()

    def test_runs_matching_requirements_filters_by_combo(self):
        client = FakeRunOnRestClient()
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-1", "run-1", mounted={"NUGGETS": "run-a-1"})
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-1", "run-2", mounted={"NUGGETS": "run-a-2"})

        runs, matching = runs_matching_requirements(
            client, "task/team/approach-1", "dataset-a", ["output.NUGGETS"], {"NUGGETS": "run-a-1"}, {}
        )

        self.assertEqual(2, len(runs))
        self.assertEqual(["run-1"], [r["run_id"] for r in matching])


class TestRunRemoteWithRunOn(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        FakeRunOnRestClient.reset(self.tmp_dir)

    def test_expands_execution_queue_across_run_on_candidates(self):
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-a", "run-a-1")
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-b", "run-b-1")

        with patch("tira.tira_cli.RestClient", FakeRunOnRestClient), patch("tira.tira_cli.time.sleep"):
            with redirect_stdout(io.StringIO()):
                actual = run_remote(
                    approach=["task/team/main"],
                    dataset=["dataset-a"],
                    resources="medium-resources",
                    parallelism=4,
                    run_on=["NUGGETS=task/team/approach-a", "NUGGETS=task/team/approach-b"],
                )

        self.assertEqual(0, actual)
        started_run_ids = {call[4]["mount_config"]["NUGGETS"]["run_id"] for call in FakeRunOnRestClient.run_calls}
        self.assertEqual({"run-a-1", "run-b-1"}, started_run_ids)

    def test_skips_dataset_without_run_on_candidates(self):
        with patch("tira.tira_cli.RestClient", FakeRunOnRestClient), patch("tira.tira_cli.time.sleep"):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                actual = run_remote(
                    approach=["task/team/main"],
                    dataset=["dataset-a"],
                    resources="medium-resources",
                    parallelism=4,
                    run_on=["NUGGETS=task/team/approach-a"],
                )

        self.assertEqual(0, actual)
        self.assertIn("No --run-on candidates were found for dataset dataset-a", stdout.getvalue())
        self.assertEqual([], FakeRunOnRestClient.run_calls)

    def test_skips_combo_already_covered_via_require(self):
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-a", "run-a-1")
        # An existing main-approach run already used run-a-1 as NUGGETS mount.
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "main", "run-main-1", mounted={"NUGGETS": "run-a-1"})

        with patch("tira.tira_cli.RestClient", FakeRunOnRestClient), patch("tira.tira_cli.time.sleep"):
            with redirect_stdout(io.StringIO()):
                actual = run_remote(
                    approach=["task/team/main"],
                    dataset=["dataset-a"],
                    resources="medium-resources",
                    parallelism=4,
                    run_on=["NUGGETS=task/team/approach-a"],
                    require=["output.NUGGETS"],
                )

        self.assertEqual(0, actual)
        self.assertEqual([], FakeRunOnRestClient.run_calls)

    def test_reruns_until_runs_per_approach_covers_combo(self):
        FakeRunOnRestClient.add_run("task", "dataset-a", "team", "approach-a", "run-a-1")

        with patch("tira.tira_cli.RestClient", FakeRunOnRestClient), patch("tira.tira_cli.time.sleep"):
            with redirect_stdout(io.StringIO()):
                actual = run_remote(
                    approach=["task/team/main"],
                    dataset=["dataset-a"],
                    resources="medium-resources",
                    parallelism=4,
                    runs_per_approach=2,
                    run_on=["NUGGETS=task/team/approach-a"],
                    require=["output.NUGGETS"],
                )

        self.assertEqual(0, actual)
        # No runs of "main" exist yet at all, so 2 executions targeting run-a-1 must be queued.
        self.assertEqual(2, len(FakeRunOnRestClient.run_calls))
        for call in FakeRunOnRestClient.run_calls:
            self.assertEqual("run-a-1", call[4]["mount_config"]["NUGGETS"]["run_id"])


class TestParseArgsRunOn(unittest.TestCase):
    def test_parse_args_registers_run_on_argument(self):
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
                "--run-on",
                "NUGGETS=task/team/approach-a",
                "NUGGETS=task/team/approach-b",
            ]
            args = parse_args()
        finally:
            sys.argv = original_argv

        self.assertEqual(
            ["NUGGETS=task/team/approach-a", "NUGGETS=task/team/approach-b"],
            args.run_on,
        )

    def test_run_on_is_not_registered_for_local_command(self):
        original_argv = list(sys.argv)
        try:
            sys.argv = [
                "tira-cli",
                "run",
                "local",
                "--approach",
                "task/team-a/software-a",
                "--input",
                "dataset-a",
            ]
            args = parse_args()
        finally:
            sys.argv = original_argv

        self.assertFalse(hasattr(args, "run_on"))


if __name__ == "__main__":
    unittest.main()
