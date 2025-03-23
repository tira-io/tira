import json
import unittest

import yaml

from tira.check_format import check_format, lines_if_valid

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    IR_METADATA_INVALID,
    IR_METADATA_MULTIPLE_VALID,
    IR_METADATA_SINGLE_VALID,
    IR_QUERY_OUTPUT,
    TSV_OUTPUT_VALID,
    VALID_RUN_OUTPUT,
)


class TestCheckTsvForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "At least one valid ir_metadata file was expected, but there was none."]
        actual = check_format(EMPTY_OUTPUT, "ir_metadata")
        self.assertEqual(expected, actual)

    def test_invalid_validator_on_query_output(self):
        expected = [_ERROR, "At least one valid ir_metadata file was expected, but there was none."]
        actual = check_format(IR_QUERY_OUTPUT, "ir_metadata")
        self.assertEqual(expected, actual)

    def test_invalid_trec_run_file(self):
        expected = [_ERROR, "At least one valid ir_metadata file was expected, but there was none."]
        actual = check_format(VALID_RUN_OUTPUT, "ir_metadata")
        self.assertEqual(expected, actual)

    def test_invalid_tsv(self):
        expected = [_ERROR, "At least one valid ir_metadata file was expected, but there was none."]
        actual = check_format(TSV_OUTPUT_VALID, "ir_metadata")
        self.assertEqual(expected, actual)

    def test_invalid_ir_metadata(self):
        with open(IR_METADATA_INVALID / ".ir-metadata.yml", "r") as f:
            actual = yaml.safe_load(f)
            self.assertEqual({"test": {"foo": "Hello"}}, actual)

        expected = [_ERROR, "At least one valid ir_metadata file was expected, but there was none."]
        actual = check_format(IR_METADATA_INVALID, "ir_metadata")
        self.assertEqual(expected, actual)

    def test_valid_output_with_single_ir_metadata(self):
        expected = [_OK, "The output provides valid ir_metadata."]
        actual = check_format(IR_METADATA_SINGLE_VALID, "ir_metadata")
        self.assertEqual(expected, actual)

    def test_valid_output_with_multiple_ir_metadata(self):
        expected = [_OK, "The output provides valid ir_metadata."]
        actual = check_format(IR_METADATA_MULTIPLE_VALID, "ir_metadata")
        self.assertEqual(expected, actual)

    def test_lines_of_valid_single_ir_metadata(self):
        expected = ".ir-metadata.yml"
        actual = lines_if_valid(IR_METADATA_SINGLE_VALID, "ir_metadata")
        self.assertEqual(1, len(actual))
        self.assertEqual(expected, actual[0]["name"])
        self.assertEqual(json.loads(json.dumps(actual[0]["content"])), actual[0]["content"])

    def test_lines_of_valid_multiple_ir_metadata(self):
        actual = lines_if_valid(IR_METADATA_MULTIPLE_VALID, "ir_metadata")
        self.assertEqual(6, len(actual))
        for i in actual:
            self.assertIsNotNone(i["name"])
            self.assertEqual(json.loads(json.dumps(i["content"])), i["content"])
