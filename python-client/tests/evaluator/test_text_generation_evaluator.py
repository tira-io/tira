import tempfile
import unittest
from pathlib import Path

import pandas as pd


def evaluate(predictions, truth_data):
    from tira.evaluators import evaluate as _eval

    config = {
        "run_format": "*.jsonl",
        "run_format_configuration": {"required_field": ["id", "response"], "id_field": "id", "value_field": "response"},
        "truth_format": None,
        "measures": ["Words (Min)", "Words (Avg)", "Words (Max)"],
    }

    with tempfile.TemporaryDirectory() as d:
        pred_dir = Path(d) / "preds" / "preds.jsonl"
        truth_dir = Path(d) / "truth" / "truth.jsonl"
        pred_dir.parent.mkdir()
        truth_dir.parent.mkdir()

        pd.DataFrame(predictions).to_json(pred_dir, lines=True, orient="records")

        if truth_data:
            pd.DataFrame(truth_data).to_json(truth_dir, lines=True, orient="records")
            config["truth_format"] = "*.jsonl"
            config["truth_format_configuration"] = {
                "required_field": ["id"],
                "id_field": "id",
                "value_field": "id",
            }

        return _eval(pred_dir.parent, truth_dir.parent, config)


class TestTextGenerationEvaluator(unittest.TestCase):
    def test_example_without_truth_01(self):
        expected = {"Words (Min)": 1.0, "Words (Avg)": 2.2, "Words (Max)": 4.0}

        predictions = [
            {"id": "1", "response": "hello world"},
            {"id": "2", "response": "1 2 3 4"},
            {"id": "3", "response": "1"},
            {"id": "4", "response": "123"},
            {"id": "5", "response": "1 3 4"},
        ]

        actual = evaluate(predictions, None)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_example_without_truth_02(self):
        expected = {"Words (Min)": 1.0, "Words (Avg)": 1.0, "Words (Max)": 1.0}

        predictions = [
            {"id": "1", "response": "hello-world"},
            {"id": "3", "response": "1"},
            {"id": "4", "response": "123"},
        ]

        actual = evaluate(predictions, None)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_example_with_truth_01(self):
        expected = {"Words (Min)": 1.0, "Words (Avg)": 1.0, "Words (Max)": 1.0}

        predictions = [
            {"id": "1", "response": "hello-world"},
            {"id": "3", "response": "1"},
            {"id": "4", "response": "123"},
        ]

        truths = [
            {"id": "1"},
            {"id": "3"},
            {"id": "4"},
        ]

        actual = evaluate(predictions, truths)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_example_with_truth_02(self):
        expected = {"Words (Min)": 1.0, "Words (Avg)": 2.333333333, "Words (Max)": 4.0}

        predictions = [
            {"id": "1", "response": "hello-world 2 3 4"},
            {"id": "3", "response": "1 2"},
            {"id": "4", "response": "123"},
        ]

        truths = [
            {"id": "1"},
            {"id": "3"},
            {"id": "4"},
        ]

        actual = evaluate(predictions, truths)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_example_with_missing_predictions(self):
        predictions = [
            {"id": "1", "response": "hello-world 2 3 4"},
            {"id": "3", "response": "1 2"},
            {"id": "4", "response": "123"},
        ]

        truths = [
            {"id": "1"},
            {"id": "3"},
            {"id": "4"},
            {"id": "5"},
        ]

        with self.assertRaises(ValueError):
            evaluate(predictions, truths)
