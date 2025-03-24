import json
import unittest

from . import _ERROR, _OK, EMPTY_OUTPUT, TEXT_ALIGNMENT_FEATURES_VALID


def check_format(dir):
    from tira.check_format import check_format as cf

    return cf(dir, "text-alignment-features")


def lines_if_valid(dir):
    from tira.check_format import lines_if_valid as lf

    return lf(dir, "text-alignment-features")


class TestCheckTextAlignmentFeaturesFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "The text-alignment-feature directory contains only 0 instances, this is likely an error."]
        actual = check_format(EMPTY_OUTPUT)
        self.assertEqual(expected, actual)

    def test_valid_directory(self):
        expected = [_OK, "The directory has the correct format."]
        actual = check_format(TEXT_ALIGNMENT_FEATURES_VALID)
        self.assertEqual(expected, actual)

    def test_parsed_lines(self):
        lines = lines_if_valid(TEXT_ALIGNMENT_FEATURES_VALID)
        expected = sorted(
            [
                "suspicious-document00028.txt",
                "suspicious-document00028.txt",
                "suspicious-document00172.txt",
                "suspicious-document00172.txt",
            ]
        )
        self.assertEqual(sorted([i["this_reference"] for i in lines]), expected)
