import unittest

from tira.check_format import check_format

from . import EMPTY_OUTPUT, IR_QUERY_OUTPUT, VALID_RUN_OUTPUT


class TestCheckFormatForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        with self.assertRaises(Exception):
            check_format(EMPTY_OUTPUT, "does-not-exist")

    def test_invalid_validator_on_query_output(self):
        with self.assertRaises(Exception):
            check_format(IR_QUERY_OUTPUT, "does-not-exist")

    def test_invalid_validator_on_valid_run_output_output(self):
        with self.assertRaises(Exception):
            check_format(VALID_RUN_OUTPUT, "does-not-exist")

    def test_multiple_invalid_validators_on_empty_output(self):
        with self.assertRaises(Exception):
            check_format(EMPTY_OUTPUT, ["d1", "d2"])

    def test_multiple_invalid_validators_on_query_output(self):
        with self.assertRaises(Exception):
            check_format(IR_QUERY_OUTPUT, ["d1", "d2"])

    def test_multiple_invalid_validators_on_valid_run_output_output(self):
        with self.assertRaises(Exception):
            check_format(VALID_RUN_OUTPUT, ["d1", "d2"])
