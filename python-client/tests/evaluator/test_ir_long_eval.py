import tempfile
import unittest
from pathlib import Path
from typing import List

from tira.evaluators import evaluate as _eval


def persist_run_to_file(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.txt").write_text(
        """1 Q0 doc-1 1 10 tag
1 Q0 doc-2 2 9 tag
3 Q0 doc-3 1 1 tag
5 Q0 doc-1 1 10 tag
5 Q0 doc-2 2 9 tag
5 Q0 doc-3 3 8 tag
5 Q0 doc-4 4 7 tag
5 Q0 doc-5 6 6 tag
5 Q0 doc-6 7 5 tag
5 Q0 doc-7 8 4 tag"""
    )


def persist_qrels_to_file(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "qrels.txt").write_text(
        """1 0 doc-1 0
1 0 doc-2 1
1 0 doc-3 2
3 0 doc-5 1
5 0 doc-2 1
5 0 doc-3 0
5 0 doc-4 0
5 0 doc-5 0
5 0 doc-6 0
5 0 doc-7 0"""
    )


def persist_zero_qrels_to_file(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "qrels.txt").write_text(
        """1 0 doc-1 0
1 0 doc-2 0
1 0 doc-3 0
3 0 doc-5 0
5 0 doc-2 0
5 0 doc-3 0
5 0 doc-4 0
5 0 doc-5 0
5 0 doc-6 0
5 0 doc-7 0"""
    )


def evaluate(run: Path, truths: Path, lags: List[str]):
    return _eval(
        run,
        truths,
        {
            "run_format": "LongEvalLags",
            "run_format_configuration": {"lags": lags, "format": "run.txt"},
            "truth_format": "LongEvalLags",
            "truth_format_configuration": {"lags": lags, "format": "qrels.txt"},
            "measures": ["nDCG@10", "RR", "P@10"],
        },
    )


class TestIrLongEvalFormat(unittest.TestCase):
    def test_valid_single_long_eval_lags(self):
        expected = {"nDCG@10": 0.290247, "RR": 0.33333333, "P@10": 0.066666666666}
        lags = ["some-lag"]
        with tempfile.TemporaryDirectory() as d:
            persist_run_to_file(Path(d) / "preds" / "some-lag")
            persist_qrels_to_file(Path(d) / "truths" / "some-lag")

            actual_all_lags = evaluate(Path(d) / "preds", Path(d) / "truths", lags)

        for lag in lags:
            self.assertIn(lag, actual_all_lags)
            actual = actual_all_lags[lag]
            self.assertEqual(expected.keys(), actual.keys())
            for k, v in expected.items():
                self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_valid_multiple_long_eval_lags(self):
        expected = {"nDCG@10": 0.290247, "RR": 0.33333333, "P@10": 0.066666666666}
        lags = ["some-lag", "lag-1", "lag-3"]
        with tempfile.TemporaryDirectory() as d:
            persist_run_to_file(Path(d) / "preds" / "some-lag")
            persist_qrels_to_file(Path(d) / "truths" / "some-lag")

            persist_run_to_file(Path(d) / "preds" / "lag-1")
            persist_qrels_to_file(Path(d) / "truths" / "lag-1")

            persist_run_to_file(Path(d) / "preds" / "lag-3")
            persist_qrels_to_file(Path(d) / "truths" / "lag-3")

            actual_all_lags = evaluate(Path(d) / "preds", Path(d) / "truths", lags)

        self.assertEqual(3, len(actual_all_lags))
        for lag in lags:
            self.assertIn(lag, actual_all_lags)
            actual = actual_all_lags[lag]
            self.assertEqual(expected.keys(), actual.keys())
            for k, v in expected.items():
                self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_valid_multiple_long_eval_lags_all_0(self):
        expected = {"nDCG@10": 0.0, "RR": 0.0, "P@10": 0.0}
        lags = ["some-lag", "lag-1", "lag-3"]
        with tempfile.TemporaryDirectory() as d:
            persist_run_to_file(Path(d) / "preds" / "some-lag")
            persist_zero_qrels_to_file(Path(d) / "truths" / "some-lag")

            persist_run_to_file(Path(d) / "preds" / "lag-1")
            persist_zero_qrels_to_file(Path(d) / "truths" / "lag-1")

            persist_run_to_file(Path(d) / "preds" / "lag-3")
            persist_zero_qrels_to_file(Path(d) / "truths" / "lag-3")

            actual_all_lags = evaluate(Path(d) / "preds", Path(d) / "truths", lags)

        self.assertEqual(3, len(actual_all_lags))
        for lag in lags:
            self.assertIn(lag, actual_all_lags)
            actual = actual_all_lags[lag]
            self.assertEqual(expected.keys(), actual.keys())
            for k, v in expected.items():
                self.assertAlmostEqual(v, actual[k], delta=0.0001)
