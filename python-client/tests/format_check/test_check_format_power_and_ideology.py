import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, IDEOLOGY_AND_POWER_LABELS, IDEOLOGY_AND_POWER_PREDICTIONS


class TestCheckFormatPowerAndIdeology(unittest.TestCase):
    def test_error_message_on_empty_output_for_truths(self):
        expected = "I did not find any files in the power and ideology pattern."
        actual = check_format(EMPTY_OUTPUT, "power-and-identification-truths")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_valid_output_for_truths(self):
        expected = [_OK, "I found 101 entries in the ideology and power task"]
        actual = check_format(IDEOLOGY_AND_POWER_LABELS, "power-and-identification-truths")
        self.assertEqual(expected, actual)

    def test_error_message_on_empty_output_for_predictions(self):
        expected = "I did not find any files in the power and ideology pattern."
        actual = check_format(EMPTY_OUTPUT, "power-and-identification-predictions")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_valid_output_for_predictions(self):
        expected = [_OK, "I found 100 entries in the ideology and power task"]
        actual = check_format(IDEOLOGY_AND_POWER_PREDICTIONS, "power-and-identification-predictions")
        self.assertEqual(expected, actual)
