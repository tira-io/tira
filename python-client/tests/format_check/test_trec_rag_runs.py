import unittest

from tira.check_format import check_format, lines_if_valid

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    JSONL_GZ_OUTPUT_VALID,
    JSONL_OUTPUT_VALID,
    TSV_OUTPUT_VALID,
    TREC_RAG_RESPONSES_VALID
)


class TestCheckJsonlForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No trec-rag-responses were found, "]
        actual = check_format(EMPTY_OUTPUT, "trec-rag-responses")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_valid_jsonl_output_directory(self):
        expected = [_ERROR, "No trec-rag-responses were found, "]
        actual = check_format(JSONL_OUTPUT_VALID, "trec-rag-responses")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_valid_jsonl_output_file(self):
        expected = [_ERROR, "No trec-rag-responses were found, "]
        actual = check_format(JSONL_OUTPUT_VALID / "predictions.jsonl", "trec-rag-responses")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_valid_jsonl_gz_output_directory(self):
        expected = [_ERROR, "No trec-rag-responses were found, "]
        actual = check_format(JSONL_GZ_OUTPUT_VALID, "trec-rag-responses")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_valid_jsonl_gz_output_file(self):
        expected = [_ERROR, "No trec-rag-responses were found, "]
        actual = check_format(JSONL_GZ_OUTPUT_VALID / "predictions.jsonl.gz", "trec-rag-responses")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_invalid_tsv(self):
        expected = [_ERROR, "No trec-rag-responses were found, "]
        actual = check_format(TSV_OUTPUT_VALID, "trec-rag-responses")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_valid_rag_responses(self):
        expected = [_OK, "valid "]
        actual = check_format(TREC_RAG_RESPONSES_VALID, "trec-rag-responses")
        #self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])
