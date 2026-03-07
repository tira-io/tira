import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, JSONL_OUTPUT_VALID, PAN26_TEXT_WATERMARKING


class TestCheckFormatPanTextWatermarking(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        expected = "I expected three directories '01-watermarking', '02-obfuscation', and '03-detection' that each contain jsonl files."
        actual = check_format(EMPTY_OUTPUT, "pan-text-watermarking")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_error_message_on_jsonl_output(self):
        expected = "I expected three directories '01-watermarking', '02-obfuscation', and '03-detection' that each contain jsonl files."
        actual = check_format(JSONL_OUTPUT_VALID, "pan-text-watermarking")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_valid(self):
        expected = "The output is valid for the PAN text watermarking task."
        actual = check_format(PAN26_TEXT_WATERMARKING, "pan-text-watermarking")
        self.assertEqual(_OK, actual[0])
        self.assertIn(expected, actual[1])
