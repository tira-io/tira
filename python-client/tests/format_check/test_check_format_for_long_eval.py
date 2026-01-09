import tempfile
import unittest
from pathlib import Path
from shutil import copy

import pandas as pd

from tira.check_format import IrMetadataFormat, check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, JSONL_OUTPUT_VALID


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


from tira.third_party_integrations import temporary_directory


def persist_longeval_data(lags, ir_metadata="longeval-ir-metadata/ir-metadata.yml") -> Path:
    d = temporary_directory()
    copy(JSONL_OUTPUT_VALID.parent / ir_metadata, Path(d) / "ir-metadata.yml")
    for lag in lags:
        persist_run_to_file(Path(d) / lag)
    return d


def check_longeval_data(lags, ir_metadata):
    d = persist_longeval_data(lags, ir_metadata)
    return check_format(Path(d), "LongEvalLags", {"lags": lags})


class TestLongEvalFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        actual = check_format(EMPTY_OUTPUT, "LongEvalLags", {"lags": ["lag-1", "lag-2"]})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file ir-metadata.yml in the directory", actual[1])

    def test_error_message_on_jsonl_output(self):
        actual = check_format(JSONL_OUTPUT_VALID, "LongEvalLags", {"lags": ["some-lag"]})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file ir-metadata.yml in the directory", actual[1])

    def test_valid_single_long_eval_lags(self):
        actual = check_longeval_data(["some-lag"], "longeval-ir-metadata/ir-metadata.yml")
        self.assertEqual(_OK, actual[0])

    def test_valid_multiple_long_eval_lag(self):
        actual = check_longeval_data(["some-lag", "lag-2"], "longeval-ir-metadata/ir-metadata.yml")
        self.assertEqual(_OK, actual[0])

    def test_valid_multiple_single_missing_lag(self):
        with tempfile.TemporaryDirectory() as d:
            persist_run_to_file(Path(d) / "some-lag")
            persist_run_to_file(Path(d) / "lag-2")

            actual = check_format(Path(d), "LongEvalLags", {"lags": ["some-lag", "lag-2", "lag-3"]})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file ir-metadata.yml in the directory", actual[1])

    def test_valid_single_long_eval_lags_with_wrong_ir_metadata(self):
        actual = check_longeval_data(["some-lag"], "longeval-ir-metadata/ir-metadata-incomplete.yml")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("is not valid", actual[1])
        self.assertIn("The required field tag still contains the default value ENTER_VALUE_HERE", actual[1])
        self.assertIn(
            "The required field method.indexing.stopwords still contains the default value ENTER_VALUE_HERE.", actual[1]
        )

    def test_valid_multiple_long_eval_lag_with_wrong_ir_metadata(self):
        actual = check_longeval_data(["some-lag", "lag-2"], "longeval-ir-metadata/ir-metadata-incomplete.yml")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("is not valid", actual[1])
        self.assertIn("The required field tag still contains the default value ENTER_VALUE_HERE", actual[1])
        self.assertIn(
            "The required field method.indexing.stopwords still contains the default value ENTER_VALUE_HERE.", actual[1]
        )

    def test_boolean_value_01(self):
        expected = ["The required field foo.automatic is missing."]
        actual = IrMetadataFormat().report_missing_fields(
            {"foo": True}, {"foo": {"automatic": {"type": bool, "default": "ENTER_VALUE_HERE"}}}
        )
        self.assertEqual(expected, actual)

    def test_boolean_value_02(self):
        expected = []
        actual = IrMetadataFormat().report_missing_fields(
            {"foo": {"automatic": True}}, {"foo": {"automatic": {"type": bool, "default": "ENTER_VALUE_HERE"}}}
        )
        self.assertEqual(expected, actual)

    def test_boolean_value_03(self):
        expected = ["The required field foo.automatic still contains the default value ENTER_VALUE_HERE."]
        actual = IrMetadataFormat().report_missing_fields(
            {"foo": {"automatic": "ENTER_VALUE_HERE"}},
            {"foo": {"automatic": {"type": bool, "default": "ENTER_VALUE_HERE"}}},
        )
        self.assertEqual(len(expected), len(actual))
        self.assertEqual(expected[0], actual[0])

    def test_boolean_value_04(self):
        expected = ["The required field foo still contains the default value ENTER_VALUE_HERE."]
        actual = IrMetadataFormat().report_missing_fields(
            {"foo": "ENTER_VALUE_HERE"},
            {"foo": {"type": bool, "default": "ENTER_VALUE_HERE"}},
        )
        self.assertEqual(len(expected), len(actual))
        self.assertEqual(expected[0], actual[0])

    def test_boolean_value_05(self):
        expected = ["The required field foo has the wrong type <class 'str'>. I expected <class 'bool'>."]
        actual = IrMetadataFormat().report_missing_fields(
            {"foo": "foo"},
            {"foo": {"type": bool, "default": "ENTER_VALUE_HERE"}},
        )
        self.assertEqual(len(expected), len(actual))
        self.assertEqual(expected[0], actual[0])
