import tempfile
import unittest
from os import listdir
from pathlib import Path
from shutil import copy

from tests.format_check import EMPTY_OUTPUT, VALID_QREL_PATH, VALID_RUN_OUTPUT
from tests.format_check.test_check_format_for_long_eval import persist_run_to_file
from tira.evaluators import evaluate as _eval
from tira.io_utils import parse_prototext_key_values


def evaluate(run: Path, truths: Path):
    return _eval(
        run,
        truths,
        {
            "run_format": "run.txt",
            "truth_format": "qrels.txt",
            "measures": ["nDCG@10", "RR", "P@10"],
        },
    )


class TestIrEvaluators(unittest.TestCase):
    def test_evaluate_works_on_valid_run_with_qrels(self):
        expected = {"nDCG@10": 0.290247, "RR": 0.33333333, "P@10": 0.066666666666}
        actual = evaluate(VALID_RUN_OUTPUT, VALID_QREL_PATH)
        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_works_on_valid_run_with_qrels_monitored(self):
        expected = {"Ndcg@10": 0.290247, "Rr": 0.33333333, "P@10": 0.066666666666}
        config = {
            "run_format": "run.txt",
            "truth_format": "qrels.txt",
            "measures": ["nDCG@10", "RR", "P@10"],
        }
        actual = _eval(VALID_RUN_OUTPUT, VALID_QREL_PATH, config, monitored=True)

        self.assertEqual(sorted(["stderr.txt", "output", "stdout.txt"]), sorted(listdir(actual)))
        self.assertEqual(["evaluation.prototext"], listdir(actual / "output"))

        actual_prototext = {
            i["key"]: i["value"] for i in parse_prototext_key_values(actual / "output" / "evaluation.prototext")
        }

        self.assertEqual(expected.keys(), actual_prototext.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual_prototext[k], delta=0.0001)

    def test_evaluate_fails_on_invalid_input(self):
        with self.assertRaises(ValueError):
            evaluate(VALID_RUN_OUTPUT, VALID_RUN_OUTPUT)

        with self.assertRaises(ValueError):
            evaluate(VALID_QREL_PATH, VALID_QREL_PATH)

    def test_evaluate_docs_per_query(self):
        expected = {
            "Docs Per Query (Avg)": 3.3333333,
            "Docs Per Query (Min)": 1,
            "Docs Per Query (Max)": 7,
            "NumQueries": 3,
        }
        actual = _eval(
            VALID_RUN_OUTPUT,
            EMPTY_OUTPUT,
            {
                "run_format": "run.txt",
                "truth_format": None,
                "measures": ["Docs Per Query (Avg)", "Docs Per Query (Min)", "Docs Per Query (Max)", "NumQueries"],
            },
        )

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_docs_per_query_for_long_eval(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lags = ["2023-01"]
            copy(EMPTY_OUTPUT.parent.parent / "longeval-ir-metadata/ir-metadata.yml", Path(tmp_dir) / "ir-metadata.yml")
            for lag in lags:
                persist_run_to_file(Path(tmp_dir) / lag)

            expected = {
                "2023-01 Docs Per Query (Avg)": 3.3333333,
                "2023-01 Docs Per Query (Min)": 1,
                "2023-01 Docs Per Query (Max)": 7,
                "2023-01 NumQueries": 3,
            }
            actual = _eval(
                tmp_dir,
                EMPTY_OUTPUT,
                {
                    "run_format": "LongEvalLags",
                    "lags": lags,
                    "truth_format": None,
                    "measures": ["Docs Per Query (Avg)", "Docs Per Query (Min)", "Docs Per Query (Max)", "NumQueries"],
                },
            )

            self.assertEqual(expected.keys(), actual.keys())
            for k, v in expected.items():
                self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_docs_per_query_for_long_eval_with_size(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lags = ["2023-01"]
            copy(EMPTY_OUTPUT.parent.parent / "longeval-ir-metadata/ir-metadata.yml", Path(tmp_dir) / "ir-metadata.yml")
            for lag in lags:
                persist_run_to_file(Path(tmp_dir) / lag)

            expected = {
                "2023-01 Docs Per Query (Avg)": 3.3333333,
                "2023-01 Docs Per Query (Min)": 1,
                "2023-01 Docs Per Query (Max)": 7,
                "2023-01 NumQueries": 3,
            }
            actual = _eval(
                tmp_dir,
                EMPTY_OUTPUT,
                {
                    "run_format": "LongEvalLags",
                    "lags": lags,
                    "truth_format": None,
                    "max_size_mb": 1,
                    "measures": ["Docs Per Query (Avg)", "Docs Per Query (Min)", "Docs Per Query (Max)", "NumQueries"],
                },
            )

            self.assertEqual(expected.keys(), actual.keys())
            for k, v in expected.items():
                self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_docs_per_query_for_long_eval_for_tiny_max_run_size(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lags = ["2023-01"]
            copy(EMPTY_OUTPUT.parent.parent / "longeval-ir-metadata/ir-metadata.yml", Path(tmp_dir) / "ir-metadata.yml")
            for lag in lags:
                persist_run_to_file(Path(tmp_dir) / lag)

            with self.assertRaises(ValueError):
                _eval(
                    tmp_dir,
                    EMPTY_OUTPUT,
                    {
                        "run_format": "LongEvalLags",
                        "lags": lags,
                        "max_size_mb": 0,
                        "truth_format": None,
                        "measures": [
                            "Docs Per Query (Avg)",
                            "Docs Per Query (Min)",
                            "Docs Per Query (Max)",
                            "NumQueries",
                        ],
                    },
                )

    def test_evaluate_docs_per_query_for_long_eval_02(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lags = ["2023-01", "2023-02", "2023-05"]
            copy(EMPTY_OUTPUT.parent.parent / "longeval-ir-metadata/ir-metadata.yml", Path(tmp_dir) / "ir-metadata.yml")
            for lag in lags:
                persist_run_to_file(Path(tmp_dir) / lag)

            expected = {
                "2023-01 Docs Per Query (Avg)": 3.3333333,
                "2023-01 Docs Per Query (Max)": 7,
                "2023-02 Docs Per Query (Avg)": 3.3333333,
                "2023-02 Docs Per Query (Max)": 7,
                "2023-05 Docs Per Query (Avg)": 3.3333333,
                "2023-05 Docs Per Query (Max)": 7,
            }
            actual = _eval(
                tmp_dir,
                EMPTY_OUTPUT,
                {
                    "run_format": "LongEvalLags",
                    "lags": lags,
                    "truth_format": None,
                    "measures": ["Docs Per Query (Avg)", "Docs Per Query (Max)"],
                },
            )

            self.assertEqual(expected.keys(), actual.keys())
            for k, v in expected.items():
                self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_docs_per_query_with_qrels(self):
        expected = {
            "Docs Per Query (Avg)": 3.3333333,
            "Docs Per Query (Min)": 1,
            "Docs Per Query (Max)": 7,
            "NumQueries": 3,
        }
        actual = _eval(
            VALID_RUN_OUTPUT,
            VALID_QREL_PATH,
            {
                "run_format": "run.txt",
                "truth_format": "qrels.txt",
                "measures": ["Docs Per Query (Avg)", "Docs Per Query (Min)", "Docs Per Query (Max)", "NumQueries"],
            },
        )

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)
