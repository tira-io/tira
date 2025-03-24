import unittest

from tira.check_format import check_format, lines_if_valid

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    IR_QUERY_OUTPUT,
    TSV_OUTPUT_VALID,
    TSV_OUTPUT_WITH_VARYING_COLUMNS,
    VALID_RUN_OUTPUT,
)


class TestCheckTsvForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No unique *.tsv file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "*.tsv")
        self.assertEqual(expected, actual)

    def test_invalid_validator_on_query_output(self):
        expected = [_ERROR, "No unique *.tsv file was found, only the files ['queries.jsonl'] were available."]
        actual = check_format(IR_QUERY_OUTPUT, "*.tsv")
        self.assertEqual(expected, actual)

    def test_invalid_trec_run_file(self):
        expected = [_ERROR, "No unique *.tsv file was found, only the files ['run.txt'] were available."]
        actual = check_format(VALID_RUN_OUTPUT, "*.tsv")
        self.assertEqual(expected, actual)

    def test_invalid_tsv_with_varying_columns(self):
        expected = [_ERROR, "The *.tsv file is invalid: The number of columns varies."]
        actual = check_format(TSV_OUTPUT_WITH_VARYING_COLUMNS, "*.tsv")
        self.assertEqual(expected, actual)

    def test_valid_tsv(self):
        expected = [_OK, "The tsv file has the correct format."]
        actual = check_format(TSV_OUTPUT_VALID, "*.tsv")
        self.assertEqual(expected, actual)

    def test_lines_of_valid_tsv(self):
        expected = [["column 1", "column 2", "column 3"]] * 5
        actual = lines_if_valid(TSV_OUTPUT_VALID, "*.tsv")
        self.assertEqual(expected, actual)
