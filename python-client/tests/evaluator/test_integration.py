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
    "native-ads-2024-spot-check-20250414-training": {},
    "native-ads-2024-train-20250319-training": {},
    "native-ads-2024-validation-20250319-training": {},
    "webis-generated-native-ads-2024-20250120_0-training": {},
    "ads-in-rag-generation-spot-check-20250414-training": {},
    "touche-25-ads-in-rag-generation-20250404_0-training": {},
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
