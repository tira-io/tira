import json
import tempfile
import unittest
from pathlib import Path

from approvaltests import verify_as_json

from tira.check_format import check_format, lines_if_valid

from . import _ERROR, _OK, EMPTY_OUTPUT, IR_QUERY_OUTPUT, JSONL_GZ_OUTPUT_VALID, TOUCHE_IMAGE_RETRIEVAL


class TestQueryProcessorFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "touche-image-retrieval")
        self.assertEqual(expected, actual)

    def test_error_message_on_ir_query_output(self):
        expected = "The json line misses the required field"
        actual = check_format(IR_QUERY_OUTPUT, "touche-image-retrieval")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_error_message_on_json_gz_output(self):
        expected = "The json line misses the required field"
        actual = check_format(JSONL_GZ_OUTPUT_VALID, "touche-image-retrieval")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_error_message_on_valid_output(self):
        expected = "The jsonl file has the correct format."
        actual = check_format(TOUCHE_IMAGE_RETRIEVAL, "touche-image-retrieval")
        self.assertEqual(_OK, actual[0])
        self.assertIn(expected, actual[1])

    def test_lines_for_valid_output(self):
        expected = {
            "qid": "1-5",
            "docno": "I002e616104f6ec04fd1a24d5",
            "q0": "0",
            "rank": 1,
            "score": 999,
            "system": "touche organizers - example submission for image retrieval; manual selection of images",
        }
        actual = lines_if_valid(TOUCHE_IMAGE_RETRIEVAL, "touche-image-retrieval")
        self.assertEqual(3, len(actual))
        self.assertEqual(expected, actual[0])
