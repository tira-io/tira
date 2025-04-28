import unittest

from tira.check_format import check_format, lines_if_valid

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    IR_QUERY_OUTPUT,
    JSONL_GZ_OUTPUT_VALID,
    JSONL_OUTPUT_INVALID,
    JSONL_OUTPUT_VALID,
    TSV_OUTPUT_VALID,
    VALID_RUN_OUTPUT,
)


class TestCheckJsonlForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "*.jsonl")
        self.assertEqual(expected, actual)

    def test_valid_jsonl_output_directory(self):
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(JSONL_OUTPUT_VALID, "*.jsonl")
        self.assertEqual(expected, actual)

    def test_valid_jsonl_output_file(self):
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(JSONL_OUTPUT_VALID / "predictions.jsonl", "*.jsonl")
        self.assertEqual(expected, actual)

    def test_valid_jsonl_gz_output_directory(self):
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(JSONL_GZ_OUTPUT_VALID, "*.jsonl")
        self.assertEqual(expected, actual)

    def test_valid_jsonl_gz_output_file(self):
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(JSONL_GZ_OUTPUT_VALID / "predictions.jsonl.gz", "*.jsonl")
        self.assertEqual(expected, actual)

    def test_valid_jsonl_gz_output_file_with_modified_configuration(self):
        expected = [_ERROR, 'The json line misses the required field "foo"']
        actual = check_format(JSONL_GZ_OUTPUT_VALID / "predictions.jsonl.gz", "*.jsonl", {"required_fields": ["foo"]})
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_invalid_jsonl_output_directory(self):
        actual = check_format(JSONL_OUTPUT_INVALID, "*.jsonl")
        self.assertEqual(actual[0], _ERROR)
        self.assertTrue("contains a line that could not be parsed" in actual[1])

    def test_invalid_jsonl_output_file(self):
        actual = check_format(JSONL_OUTPUT_INVALID / "predictions.jsonl", "*.jsonl")
        self.assertEqual(actual[0], _ERROR)
        self.assertTrue("contains a line that could not be parsed" in actual[1])

    def test_invalid_on_query_output_directory(self):
        actual = check_format(IR_QUERY_OUTPUT, "*.jsonl", {"required_fields": ["id"]})
        self.assertEqual(actual[0], _ERROR)
        self.assertTrue('The json line misses the required field "id"' in actual[1])

    def test_invalid_on_query_output_file(self):
        actual = check_format(IR_QUERY_OUTPUT / "queries.jsonl", "*.jsonl", {"required_fields": ["id"]})
        self.assertEqual(actual[0], _ERROR)
        self.assertTrue('The json line misses the required field "id"' in actual[1])

    def test_valid_on_query_output_file(self):
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(IR_QUERY_OUTPUT / "queries.jsonl", "*.jsonl", {"required_fields": ["qid"]})
        self.assertEqual(actual[0], expected[0])
        self.assertEqual(actual[1], expected[1])

    def test_invalid_trec_run_file(self):
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['run.txt'] were available."]
        actual = check_format(VALID_RUN_OUTPUT, "*.jsonl")
        self.assertEqual(expected, actual)

    def test_invalid_tsv(self):
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['predictions.tsv'] were available."]
        actual = check_format(TSV_OUTPUT_VALID, "*.jsonl")
        self.assertEqual(expected, actual)
