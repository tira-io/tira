import unittest

from tira.check_format import check_format, lines_if_valid

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    STYLE_CHANGE_CORPUS_VALID
)


class TestPan24StyleChangeDetectionFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "The style-change-detection directory contains only 0 instances, this is likely an error."]
        actual = check_format(EMPTY_OUTPUT, "style-change-detection-corpus")
        self.assertEqual(expected, actual)

    def test_valid_style_change_detection_corpus(self):
        expected = [_OK, "The directory has the correct format."]
        actual = check_format(STYLE_CHANGE_CORPUS_VALID, "style-change-detection-corpus")
        self.assertEqual(expected, actual)

    def test_valid_style_change_detection_corpus(self):
        expected = [
            {'id': 'problem-1', 'text': 'problem 1 text\n'},
            {'id': 'problem-2', 'text': 'problem-2 text\n'},
            {'id': 'problem-3', 'text': 'problem-3 text\n'},
        ]
        actual = lines_if_valid(STYLE_CHANGE_CORPUS_VALID, "style-change-detection-corpus")

        self.assertEqual(expected, actual)
