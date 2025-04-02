import unittest

from tira.evaluators import get_evaluators_if_valid


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

    def test_all_live_evaluators_are_valid(self):
        # ToDo Integration test.
        pass
