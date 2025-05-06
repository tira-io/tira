import tempfile
import unittest
from pathlib import Path

from tests.format_check.test_integration import ALL_DATASETS, DATASET_TO_MINIMAL_EXAMPLE
from tira.evaluators import evaluate, unsandboxed_evaluation_is_allowed

APPROVED_EVAL_DATASETS = {
    "pairwise-20250309-test": {},
    "pairwise-smoke-test-20250210-training": {},
    "pointwise-20250309-test": {},
    "pointwise-smoke-test-20250128-training": {},
    "ads-in-rag-task-1-generation-spot-check-20250423_1-training": {},
    "ads-in-rag-task-1-generation-test-20250506-test": {},
    "ads-in-rag-task-1-generation-training-20250423-training": {},
    "ads-in-rag-task-2-classification-spot-check-20250423-training": {},
    "ads-in-rag-task-2-classification-test-20250428-test": {},
    "ads-in-rag-task-2-classification-training-20250423-training": {},
}

from parameterized import parameterized


def datasets_with_evaluator():
    ret = {}
    for k, v in ALL_DATASETS.items():
        if unsandboxed_evaluation_is_allowed(v):
            ret[k] = v
    return ret


class TestIntegration(unittest.TestCase):
    def test_datasets_with_evaluators_are_avalaible(self):
        expected = APPROVED_EVAL_DATASETS.keys()
        actual = datasets_with_evaluator().keys()

        for k in expected:
            self.assertIn(k, actual)

        self.assertEqual(expected, actual)

    @parameterized.expand(datasets_with_evaluator().items())
    def test_datasets_with_evaluators_work(self, k, v):
        with tempfile.TemporaryDirectory() as d:
            data = DATASET_TO_MINIMAL_EXAMPLE[k]
            inputs = Path(d) / "inputs"
            truths = Path(d) / "truths"
            inputs.mkdir(exist_ok=True, parents=True)
            truths.mkdir(exist_ok=True, parents=True)

            (inputs / "predictions.jsonl").write_text(data["run"])
            (truths / "truths.jsonl").write_text(data["truth"])

            self.assertIsNotNone(evaluate(inputs, truths, v))
