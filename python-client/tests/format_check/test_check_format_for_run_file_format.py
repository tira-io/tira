import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, IR_QUERY_OUTPUT, VALID_RUN_OUTPUT


class TestCheckFormatForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No file run.txt was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "run.txt")
        self.assertEqual(expected, actual)

    def test_invalid_validator_on_query_output(self):
        expected = [_ERROR, "No file run.txt was found, only the files ['queries.jsonl'] were available."]
        actual = check_format(IR_QUERY_OUTPUT, "run.txt")
        self.assertEqual(expected, actual)

    def test_invalid_validator_on_valid_run_output_output(self):
        expected = [_OK, "The run.txt file has the correct format."]
        actual = check_format(VALID_RUN_OUTPUT, "run.txt")
        self.assertEqual(expected, actual)
