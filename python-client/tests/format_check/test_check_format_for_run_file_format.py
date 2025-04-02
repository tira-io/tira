import unittest

from tira.check_format import check_format, lines_if_valid

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    IR_QUERY_OUTPUT,
    RUN_OUTPUT_WITH_DUPLICATE_DOCUMENTS,
    RUN_OUTPUT_WITH_TOO_FEW_COLUMNS,
    RUN_OUTPUT_WITH_TOO_FEW_QUERIES,
    VALID_RUN_OUTPUT,
)


class TestCheckFormatForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No file run.txt or run.txt.gz was found. Only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "run.txt")
        self.assertEqual(expected, actual)

    def test_invalid_validator_on_query_output(self):
        expected = [_ERROR, "No file run.txt or run.txt.gz was found. Only the files ['queries.jsonl'] were available."]
        actual = check_format(IR_QUERY_OUTPUT, "run.txt")
        self.assertEqual(expected, actual)

    def test_on_valid_run_output_output(self):
        expected = [_OK, "The run.txt file has the correct format."]
        actual = check_format(VALID_RUN_OUTPUT, "run.txt")
        self.assertEqual(expected, actual)

    def test_lines_on_valid_run_output(self):
        expected = 10
        actual = lines_if_valid(VALID_RUN_OUTPUT, "run.txt")
        self.assertEqual(expected, len(actual))

    def test_lines_on_invalid_run_output(self):
        with self.assertRaises(Exception):
            lines_if_valid(RUN_OUTPUT_WITH_TOO_FEW_QUERIES, "run.txt")

    def test_on_invalid_run_with_too_few_queries(self):
        expected = [_ERROR, "The run file has only 1 queries which is likely an error."]
        actual = check_format(RUN_OUTPUT_WITH_TOO_FEW_QUERIES, "run.txt")
        self.assertEqual(expected, actual)

    def test_on_invalid_run_with_duplicate_documents(self):
        expected = [
            _ERROR,
            'The run file has duplicate documents: the document with id "doc-1" appears multiple times for query "5".',
        ]
        actual = check_format(RUN_OUTPUT_WITH_DUPLICATE_DOCUMENTS, "run.txt")
        self.assertEqual(expected, actual)

    def test_on_invalid_run_with_too_short_column(self):
        expected = [
            _ERROR,
            'Invalid line in the run file, expected 6 columns, but found a line "5 doc-1 10 tag" with 4 columns.',
        ]
        actual = check_format(RUN_OUTPUT_WITH_TOO_FEW_COLUMNS, "run.txt")
        self.assertEqual(expected, actual)
