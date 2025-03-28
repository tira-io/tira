import unittest

from tira.check_format import check_format

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    TSV_OUTPUT_VALID,
    VALID_QREL_PATH,
)


class TestCheckJsonlForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No unique qrels.txt file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "qrels.txt")
        self.assertEqual(expected, actual)

    def test_invalid_tsv(self):
        expected = [_ERROR, "No unique qrels.txt file was found, only the files ['predictions.tsv'] were available."]
        actual = check_format(TSV_OUTPUT_VALID, "qrels.txt")
        self.assertEqual(expected, actual)

    def test_valid_qrel_file(self):
        expected = [_OK, "The qrels are valid."]
        actual = check_format(VALID_QREL_PATH, "qrels.txt")
        self.assertEqual(expected, actual)
