import json
import tempfile
import unittest
from pathlib import Path

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT


class TestSisapFormat(unittest.TestCase):

    def test_error_message_on_empty_output(self):
        expected = [_ERROR, "I expected an *.h5 file, but there was no such file."]
        actual = check_format(EMPTY_OUTPUT, "sisap-predictions")
        self.assertEqual(expected[0], actual[0])
        self.assertIn(expected[1], actual[1])

    def test_valid_message_on_valid_output(self):
        expected = [_OK, "A valid *.h5 file exists."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tmp.h5").write_text("hello world")
            actual = check_format(d, "sisap-predictions")
            self.assertEqual(expected[0], actual[0])
            self.assertIn(expected[1], actual[1])
