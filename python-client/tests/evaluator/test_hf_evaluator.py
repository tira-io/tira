import unittest

from tests.format_check import JSONL_OUTPUT_VALID
from tira.evaluators import evaluate


class TestHfEvaluator(unittest.TestCase):
    def test_evaluate_jsonl_01(self):
        config = {
            "run_format": "*.jsonl",
            "run_format_configuration": {"id_field": "id", "value_field": "id"},
            "truth_format": "*.jsonl",
            "truth_format_configuration": {"id_field": "id", "value_field": "id"},
            "measures": ["recall", "precision", "f1"],
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
            "run_format_configuration": {"id_field": "id", "value_field": "id"},
            "truth_format": "*.jsonl",
            "truth_format_configuration": {"id_field": "id", "value_field": "id"},
            "measures": ["accuracy"],
        }

        expected = {"accuracy": 1}
        actual = evaluate(JSONL_OUTPUT_VALID, JSONL_OUTPUT_VALID, config)

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_jsonl_03(self):
        config = {
            "run_format": ["*.jsonl"],
            "run_format_configuration": {"id_field": "id", "value_field": "id"},
            "truth_format": ["*.jsonl"],
            "truth_format_configuration": {"id_field": "id", "value_field": "id"},
            "measures": ["accuracy"],
        }

        expected = {"accuracy": 1}
        actual = evaluate(JSONL_OUTPUT_VALID, JSONL_OUTPUT_VALID, config)

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_jsonl_error_message_01(self):
        config = {
            "run_format": "*.jsonl",
            "run_format_configuration": {"id_field": "id", "value_fields": "id"},
            "truth_format": "*.jsonl",
            "truth_format_configuration": {"id_field": "id", "value_fields": "id"},
            "measures": ["accuracy"],
        }

        with self.assertRaises(ValueError) as e:
            evaluate(JSONL_OUTPUT_VALID, JSONL_OUTPUT_VALID, config)

        self.assertIn("Got id_field = id and value_field = None.", str(repr(e.exception)))

    def test_evaluate_jsonl_error_message_02(self):
        config = {
            "run_format": "*.jsonl",
            "run_format_configuration": {"value_field": "my-value"},
            "truth_format": "*.jsonl",
            "truth_format_configuration": {"value_field": "my-value"},
            "measures": ["accuracy"],
        }

        with self.assertRaises(ValueError) as e:
            evaluate(JSONL_OUTPUT_VALID, JSONL_OUTPUT_VALID, config)

        self.assertIn("Got id_field = None and value_field = my-value.", str(repr(e.exception)))
