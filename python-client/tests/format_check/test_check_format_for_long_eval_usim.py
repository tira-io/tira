import tempfile
import unittest
from pathlib import Path
from shutil import copy

import pandas as pd

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, JSONL_OUTPUT_VALID


from tira.third_party_integrations import temporary_directory


class TestLongEvalFormat(unittest.TestCase):
    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):
            check_format(EMPTY_OUTPUT, "LongEvalUsimLags", {})

    def test_error_message_on_empty_output(self):
        actual = check_format(EMPTY_OUTPUT, "LongEvalUsimLags", {"lags": {"lag-1": ["1", "2"], "lag-2": ["3"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file lag-1.json in the directory.", actual[1])

    def test_error_message_on_jsonl_output(self):
        actual = check_format(JSONL_OUTPUT_VALID, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file some-lag.json in the directory.", actual[1])


    def test_single_long_eval_lags_with_invalid_json(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {sasa"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json is not a valid json file.", actual[1])

    def test_invalid_single_long_eval_lags_wrong_predictions(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": "[]"}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json contains predictions of type <class 'str'> for query 1. I expected a list.", actual[1])

    def test_invalid_single_long_eval_lags_too_few_predictions(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": []}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json contains no predictions for query 1.", actual[1])

    def test_invalid_single_long_eval_lags_too_many_predictions(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e", "f"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})

        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json contains too many predictions for query 1.", actual[1])

    def test_invalid_single_long_eval_lags_wrong_data_type(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", 1]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})

        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json contains predictions that are no strings for query 1.", actual[1])

    def test_invalid_no_metadata(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"1": ["a", "b", "c", "d", "e"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json does not contain the required field meta.", actual[1])

    def test_invalid_no_run(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"1": ["a", "b", "c", "d", "e"], "meta": {}}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json does not contain the required field run_name in meta.", actual[1])

    def test_invalid_no_description(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"1": ["a", "b", "c", "d", "e"], "meta": {"run_name": "a"}}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json does not contain the required field description in meta.", actual[1])

    def test_invalid_no_team_name(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"1": ["a", "b", "c", "d", "e"], "meta": {"run_name": "a", "description": "a"}}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json does not contain the required field team_name in meta.", actual[1])

    def test_valid_single_long_eval_lags(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_OK, actual[0])

#
#    def test_valid_multiple_long_eval_lag(self):
#        actual = check_longeval_data(["some-lag", "lag-2"], "longeval-ir-metadata/ir-metadata.yml")
#        self.assertEqual(_OK, actual[0])
#
#    def test_valid_multiple_single_missing_lag(self):
#        with tempfile.TemporaryDirectory() as d:
#            persist_run_to_file(Path(d) / "some-lag")
#            persist_run_to_file(Path(d) / "lag-2")
#
#            actual = check_format(Path(d), "LongEvalLags", {"lags": ["some-lag", "lag-2", "lag-3"]})
#        self.assertEqual(_ERROR, actual[0])
#        self.assertIn("I expected a file ir-metadata.yml in the directory", actual[1])
#
#    def test_valid_single_long_eval_lags_with_wrong_ir_metadata(self):
#        actual = check_longeval_data(["some-lag"], "longeval-ir-metadata/ir-metadata-incomplete.yml")
#        self.assertEqual(_ERROR, actual[0])
#        self.assertIn("is not valid", actual[1])
#        self.assertIn("The required field tag still contains the default value ENTER_VALUE_HERE", actual[1])
#        self.assertIn(
#            "The required field method.indexing.stopwords still contains the default value ENTER_VALUE_HERE.", actual[1]
#        )
#
#    def test_valid_multiple_long_eval_lag_with_wrong_ir_metadata(self):
#        actual = check_longeval_data(["some-lag", "lag-2"], "longeval-ir-metadata/ir-metadata-incomplete.yml")
#        self.assertEqual(_ERROR, actual[0])
#        self.assertIn("is not valid", actual[1])
#        self.assertIn("The required field tag still contains the default value ENTER_VALUE_HERE", actual[1])
#        self.assertIn(
#            "The required field method.indexing.stopwords still contains the default value ENTER_VALUE_HERE.", actual[1]
#        )
#
#    def test_boolean_value_01(self):
#        expected = ["The required field foo.automatic is missing."]
#        actual = IrMetadataFormat().report_missing_fields(
#            {"foo": True}, {"foo": {"automatic": {"type": bool, "default": "ENTER_VALUE_HERE"}}}
#        )
#        self.assertEqual(expected, actual)
#
#    def test_boolean_value_02(self):
#        expected = []
#        actual = IrMetadataFormat().report_missing_fields(
#            {"foo": {"automatic": True}}, {"foo": {"automatic": {"type": bool, "default": "ENTER_VALUE_HERE"}}}
#        )
#        self.assertEqual(expected, actual)
#
#    def test_boolean_value_03(self):
#        expected = ["The required field foo.automatic still contains the default value ENTER_VALUE_HERE."]
#        actual = IrMetadataFormat().report_missing_fields(
#            {"foo": {"automatic": "ENTER_VALUE_HERE"}},
#            {"foo": {"automatic": {"type": bool, "default": "ENTER_VALUE_HERE"}}},
#        )
#        self.assertEqual(len(expected), len(actual))
#        self.assertEqual(expected[0], actual[0])
#
#    def test_boolean_value_04(self):
#        expected = ["The required field foo still contains the default value ENTER_VALUE_HERE."]
#        actual = IrMetadataFormat().report_missing_fields(
#            {"foo": "ENTER_VALUE_HERE"},
#            {"foo": {"type": bool, "default": "ENTER_VALUE_HERE"}},
#        )
#        self.assertEqual(len(expected), len(actual))
#        self.assertEqual(expected[0], actual[0])
#
#    def test_boolean_value_05(self):
#        expected = ["The required field foo has the wrong type <class 'str'>. I expected <class 'bool'>."]
#        actual = IrMetadataFormat().report_missing_fields(
#            {"foo": "foo"},
#            {"foo": {"type": bool, "default": "ENTER_VALUE_HERE"}},
#        )
#        self.assertEqual(len(expected), len(actual))
#        self.assertEqual(expected[0], actual[0])
