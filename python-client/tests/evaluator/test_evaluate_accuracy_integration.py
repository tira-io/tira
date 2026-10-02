import json
import tempfile
import unittest
from pathlib import Path

from tira.tira_client import TiraClient


class FakeTiraClient(TiraClient):
    """A minimal TiraClient stub that returns a fixed dataset/evaluator configuration,
    regardless of the (non-existing) dataset identifier that is passed in. This allows
    TiraClient.evaluate to run the real, unsandboxed accuracy evaluator end-to-end
    without any network access."""

    def __init__(self, config):
        self.config = config

    def get_dataset(self, dataset):
        return self.config


class TestEvaluateAccuracyIntegration(unittest.TestCase):
    CONFIG = {
        "run_format": "*.jsonl",
        "run_format_configuration": {"id_field": "id", "value_field": "label"},
        "truth_format": "*.jsonl",
        "truth_format_configuration": {"id_field": "id", "value_field": "label"},
        "measures": ["accuracy"],
    }

    PREDICTIONS = [
        {"id": "1", "label": 1},
        {"id": "2", "label": 0},
        {"id": "3", "label": 1},  # wrong, ground truth is 0
    ]
    TRUTHS = [
        {"id": "1", "label": 1},
        {"id": "2", "label": 0},
        {"id": "3", "label": 0},
    ]

    def write_predictions_and_truths(self, tmp: Path):
        predictions_dir = Path(tmp) / "predictions"
        truths_dir = Path(tmp) / "truths"
        predictions_dir.mkdir()
        truths_dir.mkdir()

        (predictions_dir / "predictions.jsonl").write_text("\n".join(json.dumps(i) for i in self.PREDICTIONS))
        (truths_dir / "truths.jsonl").write_text("\n".join(json.dumps(i) for i in self.TRUTHS))

        return predictions_dir, truths_dir

    def test_evaluate_computes_accuracy_for_generated_jsonl_predictions_and_truths(self):
        client = FakeTiraClient(self.CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            predictions_dir, truths_dir = self.write_predictions_and_truths(Path(tmp))
            result = client.evaluate(predictions_dir, truths_dir, "some-not-existing-dataset")

        self.assertAlmostEqual(2 / 3, result["accuracy"], delta=0.0001)

    def test_evaluate_fills_the_passed_output_dir_with_the_evaluation_results(self):
        client = FakeTiraClient(self.CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            predictions_dir, truths_dir = self.write_predictions_and_truths(Path(tmp))
            output_dir = Path(tmp) / "output"
            output_dir.mkdir()

            client.evaluate(predictions_dir, truths_dir, "some-not-existing-dataset", output_dir)

            evaluation_file = output_dir / "evaluation.prototext"
            self.assertTrue(evaluation_file.exists())

            content = evaluation_file.read_text()
            self.assertIn('key: "Accuracy"', content)
            self.assertIn('value: "0.6666666666666666"', content)

    def test_evaluate_returns_correct_scores_and_writes_no_evaluation_file_when_no_output_dir_is_passed(self):
        client = FakeTiraClient(self.CONFIG)

        with tempfile.TemporaryDirectory() as tmp:
            predictions_dir, truths_dir = self.write_predictions_and_truths(Path(tmp))

            result = client.evaluate(predictions_dir, truths_dir, "some-not-existing-dataset")

            self.assertAlmostEqual(2 / 3, result["accuracy"], delta=0.0001)
            self.assertFalse(list(Path(tmp).glob("**/evaluation.prototext")))


if __name__ == "__main__":
    unittest.main()
