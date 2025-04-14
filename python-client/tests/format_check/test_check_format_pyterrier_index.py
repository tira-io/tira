import json
import tempfile
import unittest
from pathlib import Path

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT


class TestQueryProcessorFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        expected = [_ERROR, "The directory is no valid terrier index, it misses an index directory."]
        actual = check_format(EMPTY_OUTPUT, "terrier-index")
        self.assertEqual(expected, actual)

    def test_error_message_on_incomplete_output(self):
        expected = [_ERROR, "The directory is no valid terrier index, it misses an index/data.properties file."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index").mkdir(parents=True, exist_ok=True)
            actual = check_format(Path(d), "terrier-index")
            self.assertEqual(expected, actual)

    def test_valid_output(self):
        expected = [_OK, "The directory seems to be a valid pyterrier index."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index").mkdir(parents=True, exist_ok=True)
            (Path(d) / "index" / "data.properties").write_text("")
            (Path(d) / "index" / "data.meta.idx").write_text("")
            actual = check_format(Path(d), "terrier-index")
            self.assertEqual(expected, actual)
