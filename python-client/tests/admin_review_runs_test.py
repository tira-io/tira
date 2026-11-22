import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from tira.admin_review_agent import (
    _batch_mounts,
    format_summary,
    load_reviews,
    needs_human_attention,
    shorten,
    upload_reviews,
)
from tira.admin_review_runs import find_example_runs, find_unreviewed_runs, prepare_review_directory


def run_row(run_id, team="team", valid=None, evaluation_of=None):
    """A row of client.submissions(): valid=None means unreviewed, True valid, False has errors."""
    return {
        "run_id": run_id,
        "team": team,
        "software": "sw",
        "is_docker": True,
        "is_evaluation": evaluation_of is not None,
        "input_run_id": evaluation_of,
        "review_hasNoErrors": valid is True,
        "review_hasErrors": valid is False,
        "review_hasWarnings": False,
        "review_published": False,
        "review_blinded": True,
    }


class FakeClient:
    def __init__(self, rows_by_dataset):
        self.rows = rows_by_dataset

    def datasets(self, task, return_only_names):
        return list(self.rows)

    def submissions(self, task, dataset):
        return pd.DataFrame(self.rows.get(dataset, []))

    def download_zip_to_cache_directory(self, task, dataset, team, run_id):
        output = Path(tempfile.mkdtemp()) / run_id / "output"
        output.mkdir(parents=True)
        (output / "run.txt").write_text("1 Q0 d 1 1.0 x\n")
        return output


def valid_examples(dataset_prefix=""):
    return [run_row(f"{dataset_prefix}2024-01-0{i}", valid=True) for i in (3, 1, 2)]


class FindRunsTest(unittest.TestCase):
    def test_unreviewed_runs_and_runs_with_unreviewed_evaluations(self):
        rows = [
            run_row("2024-01-01-a"),  # unreviewed
            run_row("2024-01-02-b", valid=True),  # reviewed, but its evaluation is not
            run_row("2024-01-02-b-eval", valid=True, evaluation_of="2024-01-02-b"),
            run_row("2024-01-02-b-eval2", evaluation_of="2024-01-02-b"),
            run_row("2024-01-03-c", valid=True),  # completely reviewed
            run_row("2024-01-03-c-eval", valid=True, evaluation_of="2024-01-03-c"),
        ]
        runs = find_unreviewed_runs(FakeClient({"d": rows}), "task", ["d"])

        self.assertEqual(["2024-01-01-a", "2024-01-02-b"], [r["run_id"] for r in runs])
        self.assertEqual([False, True], [r["only_evaluations"] for r in runs])
        self.assertEqual(["2024-01-02-b-eval2"], runs[1]["evaluation_run_ids"])

    def test_examples_are_the_three_earliest_valid_runs(self):
        rows = valid_examples() + [run_row("2024-01-04", valid=True), run_row("2023-12-31", valid=False)]
        examples = find_example_runs(FakeClient({"d": rows}), "task", ["d"])

        self.assertEqual(["2024-01-01", "2024-01-02", "2024-01-03"], [e["run_id"] for e in examples])

    def test_examples_fail_if_there_are_less_than_three_valid_runs(self):
        with self.assertRaises(ValueError):
            find_example_runs(FakeClient({"d": valid_examples()[:2]}), "task", ["d"])


class PrepareReviewDirectoryTest(unittest.TestCase):
    def prepare(self, rows_by_dataset, **kwargs):
        output = Path(tempfile.mkdtemp())
        prepare_review_directory(FakeClient(rows_by_dataset), "task", output=output, **kwargs)
        return output

    def test_batches_contain_runs_of_one_dataset_and_the_examples_of_this_dataset(self):
        rows_a = valid_examples("a-") + [run_row(f"a-run-{i}") for i in range(3)]
        rows_b = valid_examples("b-") + [run_row("b-run-0")]
        output = self.prepare({"a": rows_a, "b": rows_b}, batch_size=2)

        batches = sorted((output / "batches").iterdir())
        manifests = [json.loads((b / "manifest.json").read_text()) for b in batches]
        self.assertEqual([2, 1, 1], [len(m["runs"]) for m in manifests])
        self.assertEqual([["a"], ["a"], ["b"]], [m["datasets"] for m in manifests])
        for manifest in manifests:
            dataset = manifest["datasets"][0]
            self.assertEqual(3, len(manifest["example_runs"]))
            self.assertTrue(all(r["dataset"] == dataset for r in manifest["runs"] + manifest["example_runs"]))
            self.assertTrue(all(r["run_id"].startswith(dataset + "-") for r in manifest["example_runs"]))

        self.assertIn("example", (batches[0] / "README.md").read_text().lower())

    def test_fails_without_enough_examples(self):
        with self.assertRaises(ValueError):
            self.prepare({"a": [run_row("a-run-0")]})

    def test_batch_mounts_only_contain_the_files_of_the_batch(self):
        rows = valid_examples("a-") + [run_row(f"a-run-{i}") for i in range(3)]
        output = self.prepare({"a": rows}, batch_size=2)

        mounts = _batch_mounts(output, output / "batches" / "0000")
        binds = sorted(m["bind"] for m in mounts.values())
        self.assertEqual({"ro"}, {m["mode"] for m in mounts.values()})
        self.assertIn("/tira-data/input/README.md", binds)
        self.assertIn("/tira-data/input/manifest.json", binds)
        self.assertEqual(2, sum("/runs/a/team/a-run-" in b for b in binds))
        self.assertEqual(3, sum("/example-runs/a/team/" in b for b in binds))
        self.assertFalse(any(b == "/tira-data/input" for b in binds))


def valid_review(run_id, evaluations=()):
    ok = {"status": "ok", "summary": "s"}
    return {
        "verdict": "valid",
        "output_reasonable": ok,
        "software_failure": ok,
        "hacking_attempt": ok,
        "data_leak_attempt": ok,
        "tira_review": {"no_errors": True, "output_error": False, "software_error": False, "comment": "fine"},
        "evaluations": [{"run_id": e, "status": "ok", "summary": "s"} for e in evaluations],
    }


class ReviewLoadingAndUploadTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.output = Path(tempfile.mkdtemp())

    def write_manifest(self, runs):
        (self.directory / "manifest.json").write_text(json.dumps({"runs": runs}))

    def write_review(self, run, review):
        path = self.output / "reviews" / run["dataset"] / run["team"] / f"{run['run_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(review if isinstance(review, str) else json.dumps(review))

    def run_entry(self, run_id, evaluations=(), only_evaluations=False):
        return {
            "dataset": "d",
            "team": "t",
            "run_id": run_id,
            "only_evaluations": only_evaluations,
            "evaluations": [{"run_id": e} for e in evaluations],
        }

    def test_problems_of_reviews(self):
        runs = [self.run_entry("missing"), self.run_entry("broken"), self.run_entry("no-eval", ["e1"])]
        self.write_manifest(runs)
        self.write_review(runs[1], "{not json")
        self.write_review(runs[2], valid_review("no-eval"))

        results = load_reviews(self.directory, self.output)

        self.assertIn("missing review file", results[0]["problems"][0])
        self.assertIn("invalid JSON", results[1]["problems"][0])
        self.assertEqual(["evaluations not reviewed: ['e1']"], results[2]["problems"])

    def test_suspicious_without_evidence_and_missing_comment_are_problems(self):
        run = self.run_entry("r")
        review = valid_review("r")
        review["hacking_attempt"] = {"status": "suspicious", "summary": "s"}
        review["tira_review"]["comment"] = " "
        self.write_manifest([run])
        self.write_review(run, review)

        problems = load_reviews(self.directory, self.output)[0]["problems"]

        self.assertEqual(2, len(problems))

    def test_runs_with_only_evaluations_need_no_run_review(self):
        run = self.run_entry("r", ["e1"], only_evaluations=True)
        self.write_manifest([run])
        self.write_review(run, {"verdict": "valid", "evaluations": [{"run_id": "e1", "status": "ok"}]})

        self.assertEqual([], load_reviews(self.directory, self.output)[0]["problems"])

    def test_upload_skips_runs_that_need_a_human(self):
        runs = [self.run_entry(i, [f"{i}-e"]) for i in ("good", "suspicious", "bad-eval", "invalid")]
        self.write_manifest(runs)
        for run in runs:
            self.write_review(run, valid_review(run["run_id"], [run["run_id"] + "-e"]))
        suspicious = valid_review("suspicious", ["suspicious-e"])
        suspicious["data_leak_attempt"] = {"status": "suspicious", "evidence": ["x"]}
        self.write_review(runs[1], suspicious)
        bad_eval = valid_review("bad-eval", ["bad-eval-e"])
        bad_eval["evaluations"][0]["status"] = "suspicious"
        self.write_review(runs[2], bad_eval)
        self.write_review(runs[3], "{")

        results = load_reviews(self.directory, self.output)
        calls = []

        class Client:
            def review_run(self, *args):
                calls.append(args)

        uploaded = upload_reviews(Client(), results)

        self.assertEqual(["good"], [u["run"]["run_id"] for u in uploaded])
        self.assertEqual(["good", "good-e"], [c[0] for c in calls])
        self.assertEqual("fine", calls[0][6])
        self.assertEqual("Automatic review of the evaluation.", calls[1][6])
        self.assertTrue(needs_human_attention(results[1]))
        self.assertFalse(needs_human_attention(results[0]))

    def test_upload_of_runs_with_only_evaluations_skips_the_run_review(self):
        run = self.run_entry("r", ["e1"], only_evaluations=True)
        self.write_manifest([run])
        self.write_review(run, {"verdict": "valid", "evaluations": [{"run_id": "e1", "status": "ok"}]})
        calls = []

        class Client:
            def review_run(self, *args):
                calls.append(args)

        upload_reviews(Client(), load_reviews(self.directory, self.output))

        self.assertEqual(["e1"], [c[0] for c in calls])

    def test_summary_and_shorten(self):
        self.assertEqual("a b", shorten("a\n  b"))
        self.assertEqual(10, len(shorten("x" * 50, 10)))
        self.assertTrue(shorten("x" * 50, 10).endswith("…"))

        run = self.run_entry("r")
        self.write_manifest([run])
        self.write_review(run, valid_review("r"))
        summary = format_summary(load_reviews(self.directory, self.output))

        self.assertIn("Reviewed 1 run(s)", summary)
        self.assertIn("valid: 1", summary)
