import tempfile
import unittest
from pathlib import Path

from tira.check_format import check_format, lines_if_valid

from . import _ERROR, _OK, EMPTY_OUTPUT, IR_QUERY_OUTPUT, VALID_RUN_OUTPUT

EXAMPLE_01 = """
run-01 relstring             	979	'----------'
run-01 recall_5              	979	0.1
run-01 recall_10             	979	0.2
run-01 recall_15             	979	0.3
run-01 relstring             	all	'----------'
run-01 recall_5              	all	0.1
run-01 recall_10             	all	0.2
run-01 recall_15             	all	0.3
"""

EXAMPLE_02 = """
run-02 relstring             	979	'----------'
run-02 recall_5              	979	0.3
run-02 recall_10             	979	0.4
run-02 recall_15             	979	0.6
run-02 relstring             	all	'----------'
run-02 recall_5              	all	0.7
run-02 recall_10             	all	0.8
run-02 recall_15             	all	0.9
"""


class TestTrecEvalLeaderbaordFormat(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [
            _ERROR,
            "No unique file in trec-eval -q format was found, only the files ['.gitkeep'] were available.",
        ]
        actual = check_format(EMPTY_OUTPUT, "trec-eval-leaderboard")
        self.assertEqual(expected, actual)

    def test_invalid_validator_ir_query_output(self):
        expected = [
            _ERROR,
            "No unique file in trec-eval -q format was found, only the files ['queries.jsonl'] were available.",
        ]
        actual = check_format(IR_QUERY_OUTPUT, "trec-eval-leaderboard")
        self.assertEqual(expected, actual)

    def test_invalid_validator_run_output(self):
        expected = [
            _ERROR,
            "No unique file in trec-eval -q format was found, only the files ['run.txt'] were available.",
        ]
        actual = check_format(VALID_RUN_OUTPUT, "trec-eval-leaderboard")
        self.assertEqual(expected, actual)

    def test_valid_example_01(self):
        expected = [_OK, "Valid trec-eval-leaderboard."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(EXAMPLE_01 + EXAMPLE_02)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected, actual)

    def test_valid_example_02(self):
        expected = [_OK, "Valid trec-eval-leaderboard."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(EXAMPLE_02 + EXAMPLE_01)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected, actual)

    def test_invalid_example_single_system_01(self):
        expected = [_ERROR, "The trec-eval-leaderboard file contains only 1 systems, this is likely an error."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(EXAMPLE_01)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected[0], actual[0])
            self.assertEqual(expected[1], actual[1])

    def test_invalid_example_single_system_02(self):
        expected = [_ERROR, "The trec-eval-leaderboard file contains only 1 systems, this is likely an error."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(EXAMPLE_02)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected[0], actual[0])
            self.assertEqual(expected[1], actual[1])

    def test_invalid_example_02_missing_all(self):
        leaderboard = (
            """
run-03 relstring             	979	'----------'
run-03 recall_5              	979	0.3"""
            + EXAMPLE_02
            + EXAMPLE_01
        )

        expected = [
            _ERROR,
            "The trec-eval-leaderboard is not valid. The all entry for",
        ]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(leaderboard)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected[0], actual[0])
            self.assertIn(expected[1], actual[1])

    def test_invalid_example_03_different_measures(self):
        leaderboard = (
            "run-01 new-measure             	979	'----------'\n"
            + "run-01 new-measure             	all	'----------'"
            + EXAMPLE_02
            + EXAMPLE_01
        )

        expected = [
            _ERROR,
            "The trec-eval-leaderboard is not valid. Some measures are not available",
        ]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(leaderboard)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected[0], actual[0])
            self.assertIn(expected[1], actual[1])

    def test_invalid_example_03_different_query(self):
        leaderboard = "run-01 relstring             	980	'----------'" + EXAMPLE_02 + EXAMPLE_01

        expected = [
            _ERROR,
            "The trec-eval-leaderboard is not valid. Some queries are not evaluated",
        ]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(leaderboard)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected[0], actual[0])
            self.assertIn(expected[1], actual[1])
