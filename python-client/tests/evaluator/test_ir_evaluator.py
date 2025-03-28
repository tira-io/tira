import unittest
from pathlib import Path

from tests.format_check import VALID_QREL_PATH, VALID_RUN_OUTPUT


def evaluate(run: Path, truths: Path):
    from tira.evaluators import evaluate as _eval

    return _eval(
        run,
        truths,
        {
            "run_format": "run.txt",
            "truth_format": "qrels.txt",
            "evaluator": "ir",
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

    def test_evaluate_fails_on_invalid_input(self):
        with self.assertRaises(ValueError):
            evaluate(VALID_RUN_OUTPUT, VALID_RUN_OUTPUT)
