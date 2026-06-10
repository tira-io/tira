import json
import tempfile
import unittest
from pathlib import Path

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT


class TestSisapFormat(unittest.TestCase):

    def test_error_message_on_empty_output(self):
        expected = [_ERROR, "I expected one or more *.h5 file(s), but there were none."]
        actual = check_format(EMPTY_OUTPUT, "sisap-predictions")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_valid_message_on_valid_output(self):
        expected = [_OK, "Valid *.h5 file(s) exists."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tmp.h5").write_text("hello world")
            actual = check_format(d, "sisap-predictions")
            self.assertEqual(expected[0], actual[0])
            self.assertIn(expected[1], actual[1])

    def test_valid_message_on_multiple_h5_files(self):
        expected = [_OK, "Valid *.h5 file(s) exists."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tmp-1.h5").write_text("hello world")
            (Path(d) / "tmp-2.h5").write_text("hello world")
            (Path(d) / "tmp-3.h5").write_text("hello world")
            actual = check_format(d, "sisap-predictions")
            self.assertEqual(expected[0], actual[0])
            self.assertIn(expected[1], actual[1])
