import tempfile
import unittest
from pathlib import Path

import pandas as pd

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, GEN_IR_SIM_OUTPUT_VALID, JSONL_OUTPUT_VALID


def persist_run_to_file(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.txt").write_text(
        """1 Q0 doc-1 1 10 tag
1 Q0 doc-2 2 9 tag
3 Q0 doc-3 1 1 tag
5 Q0 doc-1 1 10 tag
5 Q0 doc-2 2 9 tag
5 Q0 doc-3 3 8 tag
5 Q0 doc-4 4 7 tag
5 Q0 doc-5 6 6 tag
5 Q0 doc-6 7 5 tag
5 Q0 doc-7 8 4 tag"""
    )


class TestLongEvalFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        expected = [_ERROR, "The Lag lag-1 is invalid: No file run.txt or run.txt.gz was found."]
        actual = check_format(EMPTY_OUTPUT, "LongEvalLags", {"lags": ["lag-1", "lag-2"]})
        self.assertEqual(expected, actual)

    def test_error_message_on_jsonl_output(self):
        expected = [_ERROR, "The Lag some-lag is invalid: No file run.txt or run.txt.gz was found."]
        actual = check_format(JSONL_OUTPUT_VALID, "LongEvalLags", {"lags": ["some-lag"]})
        self.assertEqual(expected, actual)

    def test_valid_single_long_eval_lags(self):
        expected = [_OK, "All lags ['some-lag'] are valid."]
        with tempfile.TemporaryDirectory() as d:
            persist_run_to_file(Path(d) / "some-lag")

            actual = check_format(Path(d), "LongEvalLags", {"lags": ["some-lag"]})
        self.assertEqual(expected, actual)

    def test_valid_multiple_long_eval_lag(self):
        expected = [_OK, "All lags ['some-lag', 'lag-2'] are valid."]
        with tempfile.TemporaryDirectory() as d:
            persist_run_to_file(Path(d) / "some-lag")
            persist_run_to_file(Path(d) / "lag-2")

            actual = check_format(Path(d), "LongEvalLags", {"lags": ["some-lag", "lag-2"]})
        self.assertEqual(expected, actual)

    def test_valid_multiple_single_missing_lag(self):
        expected = [_ERROR, "The Lag lag-3 is invalid: No file run.txt or run.txt.gz was found."]
        with tempfile.TemporaryDirectory() as d:
            persist_run_to_file(Path(d) / "some-lag")
            persist_run_to_file(Path(d) / "lag-2")

            actual = check_format(Path(d), "LongEvalLags", {"lags": ["some-lag", "lag-2", "lag-3"]})
        self.assertEqual(expected, actual)
