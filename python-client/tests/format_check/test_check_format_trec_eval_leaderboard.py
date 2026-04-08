import tempfile
import unittest
from pathlib import Path

from tira.check_format import check_format, lines_if_valid

from . import _ERROR, _OK, EMPTY_OUTPUT, IR_QUERY_OUTPUT, VALID_RUN_OUTPUT

EXAMPLE_01 = """
run-01 979	relstring	'----------'
run-01 979	recall_5	0.1
run-01 979	recall_10	0.2
run-01 979	recall_15	0.3
run-01 all	relstring       '----------'
run-01 all	recall_5	0.1
run-01 all	recall_10	0.2
run-01 all	recall_15	0.3
"""

EXAMPLE_02 = """
run_id	query_id	measure	value
run-02 979 relstring '----------'
run-02 979 recall_5 0.3
run-02 979 recall_10 0.4
run-02 979 recall_15 0.6
run-02 all relstring '----------'
run-02 all recall_5 0.7
run-02 all recall_10 0.8
run-02 all recall_15 0.9
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

    def test_valid_example_recursive_01(self):
        expected = [_OK, "Valid trec-eval-leaderboard."]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "dir").mkdir()
            (Path(d) / "dir" / "trec-leaderboard").write_text(EXAMPLE_01 + EXAMPLE_02)
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
run-03              	979 relstring	'----------'
run-03 979 recall_5              	0.3"""
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
            "run-01 979 new-measure             	'----------'\n"
            + "run-01 all new-measure             	'----------'"
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
        leaderboard = "run-01             	980 relstring	'----------'" + EXAMPLE_02 + EXAMPLE_01

        expected = [
            _ERROR,
            "The trec-eval-leaderboard is not valid. Some queries are not evaluated",
        ]
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "trec-leaderboard").write_text(leaderboard)
            actual = check_format(Path(d), "trec-eval-leaderboard")
            self.assertEqual(expected[0], actual[0])
            self.assertIn(expected[1], actual[1])
