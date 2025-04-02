import unittest

from tira.evaluators import get_evaluators_if_valid, unsandboxed_evaluation_is_allowed


class TestGetEvaluatorsIfValid(unittest.TestCase):
    def test_long_eval(self):
        actual = get_evaluators_if_valid(
            {
                "run_format": "LongEvalLags",
                "run_format_configuration": {"lags": ["lag-1"], "format": "run.txt"},
                "truth_format": "LongEvalLags",
                "truth_format_configuration": {"lags": ["lag-1"], "format": "qrels.txt"},
                "measures": ["nDCG@10"],
            }
        )
        self.assertIsNotNone(actual)

    def test_unsandboxed_evaluation_is_allowed_01(self):
        configuration = {
            "run_format": "LongEvalLags",
            "run_format_configuration": {"lags": ["lag-1"], "format": "run.txt"},
            "truth_format": "LongEvalLags",
            "truth_format_configuration": {"lags": ["lag-1"], "format": "qrels.txt"},
            "measures": ["nDCG@10"],
        }
        actual = unsandboxed_evaluation_is_allowed(configuration)
        self.assertTrue(actual)

    def test_unsandboxed_evaluation_is_allowed_02(self):
        configuration = {"run_format": "LongEvalLags", "truth_format": "LongEvalLags", "measures": ["foo"]}
        actual = unsandboxed_evaluation_is_allowed(configuration)
        self.assertTrue(actual)

    def test_unsandboxed_evaluation_is_not_allowed_01(self):
        configuration = {
            "run_format": "LongEvalLags",
            "run_format_configuration": {"lags": ["lag-1"], "format": "run.txt"},
            "truth_format": "LongEvalLags",
            "truth_format_configuration": {"lags": ["lag-1"], "format": "qrels.txt"},
        }
        actual = unsandboxed_evaluation_is_allowed(configuration)
        self.assertFalse(actual)

    def test_unsandboxed_evaluation_is_not_allowed_02(self):
        configuration = {"run_format": "LongEvalLags", "truth_format": "LongEvalLags", "measures": []}
        actual = unsandboxed_evaluation_is_allowed(configuration)
        self.assertFalse(actual)

    def test_all_live_evaluators_are_valid(self):
        # ToDo Integration test.
        pass
