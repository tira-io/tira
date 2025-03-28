import unittest

from tests.format_check import JSONL_OUTPUT_VALID

from tira.evaluators import evaluate


class TestHfEvaluator(unittest.TestCase):
    def test_evaluate_jsonl_01(self):
        config = {
            "run_format": "*.jsonl",
            "truth_format": "*.jsonl",
            "measures": ["recall", "precision", "f1"],
            "run_id_column": "id",
            "run_label_column": "id",
            "truth_id_column": "id",
            "truth_label_column": "id",
            "additional_args": {"average": "micro"},
        }

        expected = {"recall": 1, "precision": 1, "f1": 1}
        actual = evaluate(JSONL_OUTPUT_VALID, JSONL_OUTPUT_VALID, config)

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_jsonl_02(self):
        config = {
            "run_format": "*.jsonl",
            "truth_format": "*.jsonl",
            "measures": ["accuracy"],
            "run_id_column": "id",
            "run_label_column": "id",
            "truth_id_column": "id",
            "truth_label_column": "id",
        }

        expected = {"accuracy": 1}
        actual = evaluate(JSONL_OUTPUT_VALID, JSONL_OUTPUT_VALID, config)

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)
