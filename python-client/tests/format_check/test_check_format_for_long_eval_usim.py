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

    def test_invalid_unexpected_file(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e"]}')
        (tmp_dir / "unexpected").write_text('')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file unexpected is not expected. Please remove it.", actual[1])

    def test_invalid_two_long_eval_lags(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1", "3"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json is missing query 3.", actual[1])

    def test_invalid_two_long_eval_lags_too_many_predictions(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e"], "3": ["a"], "4": ["1"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1", "3"]}})
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The file some-lag.json contains predictions for the query 4, but no such query exists.", actual[1])

    def test_valid_single_long_eval_lags(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1"]}})
        self.assertEqual(_OK, actual[0])

    def test_valid_two_long_eval_lags(self):
        tmp_dir = temporary_directory()
        (tmp_dir / "some-lag.json").write_text('{"meta": {"team_name": "T1", "description": "descr.", "run_name": "my-run3"}, "1": ["a", "b", "c", "d", "e"], "3": ["a"]}')

        actual = check_format(tmp_dir, "LongEvalUsimLags", {"lags": {"some-lag": ["1", "3"]}})
        self.assertEqual(_OK, actual[0])