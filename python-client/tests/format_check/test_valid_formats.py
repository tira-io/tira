import unittest

from tira.check_format import report_valid_formats

from . import (
    EMPTY_OUTPUT,
    IR_METADATA_INVALID,
    IR_METADATA_MULTIPLE_VALID,
    IR_METADATA_SINGLE_VALID,
    IR_QUERY_OUTPUT,
    TSV_OUTPUT_VALID,
    VALID_RUN_OUTPUT,
)


class TestValidFormats(unittest.TestCase):
    def test_empty_output(self):
        expected = {}
        actual = report_valid_formats(EMPTY_OUTPUT)
        self.assertEqual(expected, actual)

    def test_ir_metadata_invalid(self):
        expected = {}
        actual = report_valid_formats(IR_METADATA_INVALID)
        self.assertEqual(expected, actual)

    def test_query_output(self):
        expected = {}
        actual = report_valid_formats(IR_QUERY_OUTPUT)
        self.assertEqual(expected, actual)

    def test_tsv_output(self):
        expected = {}
        actual = report_valid_formats(TSV_OUTPUT_VALID)
        self.assertEqual(expected, actual)

    def test_run_output(self):
        expected = {}
        actual = report_valid_formats(VALID_RUN_OUTPUT)
        self.assertEqual(expected, actual)

    def test_ir_metadata_multiple_valid(self):
        expected = {
            "ir_metadata": [
                ".ir-metadata.yml",
                "foo-metadata.yml",
                "foo-metadata.yml",
                "m.yaml",
                "m.yaml",
                "metadata.yaml",
            ]
        }
        actual = report_valid_formats(IR_METADATA_MULTIPLE_VALID)
        self.assertEqual(expected, actual)

    def test_ir_metadata_single_valid(self):
        expected = {
            "ir_metadata": [
                ".ir-metadata.yml",
            ]
        }
        actual = report_valid_formats(IR_METADATA_SINGLE_VALID)
        self.assertEqual(expected, actual)
