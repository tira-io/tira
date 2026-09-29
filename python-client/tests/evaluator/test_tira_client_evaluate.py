import unittest
from pathlib import Path
from unittest.mock import patch

from tira.tira_client import TiraClient

VALID_EVAL_CONFIG = {
    "task_id": "some-task",
    "dataset_id": "some-dataset",
    "run_format": "LongEvalLags",
    "run_format_configuration": {"lags": ["lag-1"], "format": "run.txt"},
    "truth_format": "LongEvalLags",
    "truth_format_configuration": {"lags": ["lag-1"], "format": "qrels.txt"},
    "measures": ["nDCG@10"],
}

# This configuration has no "measures", so tira.evaluators.load_evaluator_config raises and
# TiraClient.evaluate is expected to fall back to the sandboxed (dockerized) evaluator.
INVALID_EVAL_CONFIG = {"task_id": "some-task", "dataset_id": "some-dataset"}


class FakeTiraClient(TiraClient):
    """A minimal TiraClient stub that returns a preconfigured dataset configuration
    and records calls to download_dataset, so that TiraClient.evaluate can be tested
    in isolation without any network access."""

    def __init__(self, dataset_config, download_dataset_return=None):
        self.dataset_config = dataset_config
        self.download_dataset_return = download_dataset_return
        self.download_dataset_calls = []
        self.get_dataset_calls = []

    def get_dataset(self, dataset):
        self.get_dataset_calls.append(dataset)
        return self.dataset_config

    def download_dataset(self, task, dataset, truth_dataset=False, allow_local_dataset=False, output=None):
        self.download_dataset_calls.append((task, dataset, truth_dataset))
        return self.download_dataset_return


class TestTiraClientEvaluate(unittest.TestCase):
    def test_evaluate_uses_unsandboxed_evaluator_for_valid_config(self):
        client = FakeTiraClient(VALID_EVAL_CONFIG)
        predictions = Path("/tmp/predictions")
        truths = Path("/tmp/truths")

        with patch("tira.evaluators.evaluate") as mocked_evaluate:
            mocked_evaluate.return_value = {"nDCG@10": 0.5}
            actual = client.evaluate(predictions, truths, "some-task/some-dataset")

        mocked_evaluate.assert_called_once_with(predictions, truths, VALID_EVAL_CONFIG, None)
        self.assertEqual({"nDCG@10": 0.5}, actual)
        self.assertEqual(["some-task/some-dataset"], client.get_dataset_calls)
        self.assertEqual([], client.download_dataset_calls)

    def test_evaluate_forwards_the_output_dir_to_the_unsandboxed_evaluator(self):
        client = FakeTiraClient(VALID_EVAL_CONFIG)
        predictions = Path("/tmp/predictions")
        truths = Path("/tmp/truths")
        output_dir = Path("/tmp/results")

        with patch("tira.evaluators.evaluate") as mocked_evaluate:
            mocked_evaluate.return_value = {"nDCG@10": 0.5}
            client.evaluate(predictions, truths, "some-task/some-dataset", output_dir)

        mocked_evaluate.assert_called_once_with(predictions, truths, VALID_EVAL_CONFIG, output_dir)

    def test_evaluate_falls_back_to_sandboxed_evaluator_for_invalid_config(self):
        client = FakeTiraClient(INVALID_EVAL_CONFIG)
        predictions = Path("/tmp/predictions")
        truths = Path("/tmp/truths")

        with (
            patch.object(TiraClient, "evaluate_sandboxed") as mocked_sandboxed,
            patch("tira.third_party_integrations.temporary_directory", return_value=Path("/tmp/eval-output")),
        ):
            actual = client.evaluate(predictions, truths, "some-task/some-dataset")

        mocked_sandboxed.assert_called_once_with(predictions, "some-task/some-dataset", Path("/tmp/eval-output"))
        self.assertEqual(Path("/tmp/eval-output"), actual)

    def test_evaluate_uses_the_passed_output_dir_for_the_sandboxed_evaluator_instead_of_a_temporary_directory(self):
        client = FakeTiraClient(INVALID_EVAL_CONFIG)
        predictions = Path("/tmp/predictions")
        truths = Path("/tmp/truths")
        output_dir = Path("/tmp/results")

        with (
            patch.object(TiraClient, "evaluate_sandboxed") as mocked_sandboxed,
            patch("tira.third_party_integrations.temporary_directory") as mocked_temporary_directory,
        ):
            actual = client.evaluate(predictions, truths, "some-task/some-dataset", output_dir)

        mocked_temporary_directory.assert_not_called()
        mocked_sandboxed.assert_called_once_with(predictions, "some-task/some-dataset", output_dir)
        self.assertEqual(output_dir, actual)

    def test_evaluate_downloads_truths_from_the_dataset_when_none_are_passed(self):
        client = FakeTiraClient(VALID_EVAL_CONFIG, download_dataset_return="/tmp/downloaded-truths")
        predictions = Path("/tmp/predictions")

        with patch("tira.evaluators.evaluate") as mocked_evaluate:
            mocked_evaluate.return_value = {"nDCG@10": 0.5}
            client.evaluate(predictions, None, "some-task/some-dataset")

        self.assertEqual([("some-task", "some-dataset", True)], client.download_dataset_calls)
        mocked_evaluate.assert_called_once_with(predictions, Path("/tmp/downloaded-truths"), VALID_EVAL_CONFIG, None)

    def test_evaluate_passes_the_dataset_argument_unchanged_to_get_dataset(self):
        # Regression test: TiraClient.evaluate must be called with the dataset identifier as a
        # string. Passing anything else (e.g., a Path, as previously happened in the worker's
        # celery evaluate task) is forwarded as-is to get_dataset/download_dataset, which
        # expect a string and will fail with e.g. AttributeError: 'PosixPath' object has no
        # attribute 'split'.
        client = FakeTiraClient(VALID_EVAL_CONFIG)
        predictions = Path("/tmp/predictions")
        truths = Path("/tmp/truths")

        with patch("tira.evaluators.evaluate") as mocked_evaluate:
            mocked_evaluate.return_value = {}
            client.evaluate(predictions, truths, "some-task/some-dataset")

        self.assertEqual(["some-task/some-dataset"], client.get_dataset_calls)
        for dataset_arg in client.get_dataset_calls:
            self.assertIsInstance(dataset_arg, str)


if __name__ == "__main__":
    unittest.main()
