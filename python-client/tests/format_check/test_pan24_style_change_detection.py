import unittest

from tira.check_format import check_format, lines_if_valid

from . import _ERROR, _OK, EMPTY_OUTPUT, STYLE_CHANGE_CORPUS_VALID, STYLE_CHANGE_PREDICTIONS_VALID


class TestPan24StyleChangeDetectionFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "The style-change-detection directory contains only 0 instances, this is likely an error."]
        actual = check_format(EMPTY_OUTPUT, "style-change-detection-corpus")
        self.assertEqual(expected, actual)

    def test_valid_style_change_detection_corpus(self):
        expected = [_OK, "The directory has the correct format."]
        actual = check_format(STYLE_CHANGE_CORPUS_VALID, "style-change-detection-corpus")
        self.assertEqual(expected, actual)

    def test_lines_of_style_change_detection_corpus(self):
        expected = [
            {"id": "problem-1", "text": "problem 1 text\n"},
            {"id": "problem-2", "text": "problem-2 text\n"},
            {"id": "problem-3", "text": "problem-3 text\n"},
        ]
        actual = lines_if_valid(STYLE_CHANGE_CORPUS_VALID, "style-change-detection-corpus")

        self.assertEqual(expected, actual)

    def test_invalid_prediction_validator_on_empty_output(self):
        expected = [_ERROR, "The style-change-detection directory contains only 0 instances, this is likely an error."]
        actual = check_format(EMPTY_OUTPUT, "style-change-detection-predictions")
        self.assertEqual(expected, actual)

    def test_invalid_prediction_validator_on_corpus(self):
        expected = [_ERROR, "The style-change-detection directory contains only 0 instances, this is likely an error."]
        actual = check_format(STYLE_CHANGE_CORPUS_VALID, "style-change-detection-predictions")
        self.assertEqual(expected, actual)

    def test_valid_style_change_detection_predictions(self):
        expected = [_OK, "The directory has the correct format."]
        actual = check_format(STYLE_CHANGE_PREDICTIONS_VALID, "style-change-detection-predictions")
        self.assertEqual(expected, actual)

    def test_lines_style_change_detection_predictions(self):
        expected = [
            {"authors": 2, "changes": [0, 0, 1, 0, 1], "problem": "1", "type": "solution"},
            {"authors": 2, "changes": [0, 0, 1, 0, 1], "problem": "1", "type": "truth"},
            {"authors": 2, "changes": [0, 0, 1, 0, 1], "problem": "2", "type": "solution"},
        ]
        actual = lines_if_valid(STYLE_CHANGE_PREDICTIONS_VALID, "style-change-detection-predictions")
        self.assertEqual(expected, actual)
