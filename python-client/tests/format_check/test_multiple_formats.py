import unittest
from pathlib import Path

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    IR_METADATA_INVALID,
    IR_METADATA_SINGLE_VALID,
    VALID_RUN_OUTPUT,
    VALID_RUN_WITH_METADATA_OUTPUT,
)


def check_format(run_output: Path):
    from tira.check_format import check_format as cf

    return cf(run_output, ["run.txt", "ir_metadata"])


class TestMultipleFormats(unittest.TestCase):
    def test_error_for_empty_dir(self):
        expected = [_ERROR, "The output is not valid. Problems: No file run.txt or run.txt.gz was"]
        actual = check_format(EMPTY_OUTPUT)
        self.assertEqual(expected[0], actual[0])
        self.assertTrue(actual[1].startswith(expected[1]))

    def test_error_for_ir_metadata_invalid(self):
        expected = [_ERROR, "The output is not valid. Problems: No file run.txt or run.txt.gz was"]
        actual = check_format(IR_METADATA_INVALID)
        self.assertEqual(expected[0], actual[0])
        self.assertTrue(actual[1].startswith(expected[1]))

    def test_error_for_run_invalid(self):
        expected = [_ERROR, "The output is not valid. Problems: No file run.txt or run.txt.gz was"]
        actual = check_format(IR_METADATA_SINGLE_VALID)
        self.assertEqual(expected[0], actual[0])
        self.assertTrue(actual[1].startswith(expected[1]))

    def test_error_for_metadata_invalid(self):
        expected = [_ERROR, "The output is not valid. Problems: At least one valid ir_metadata file was expected"]
        actual = check_format(VALID_RUN_OUTPUT)
        self.assertEqual(expected[0], actual[0])
        self.assertTrue(actual[1].startswith(expected[1]))

    def test_valid_input(self):
        expected = [_OK, "The output is valid."]
        actual = check_format(VALID_RUN_WITH_METADATA_OUTPUT)
        self.assertEqual(expected[0], actual[0])
        self.assertTrue(actual[1].startswith(expected[1]))
