import unittest

import pandas as pd

from tira.check_format import lines_if_valid
from tira.serialize_format import serialize_in_temporary_directory

from ..format_check import VALID_RUN_OUTPUT

VALID_TRECTOOLS_RUN = pd.DataFrame(
    [
        {"query": 1, "q0": "Q0", "docid": "d-1", "rank": 1, "score": 10, "system": "s"},
        {"query": 1, "q0": "Q0", "docid": "d-2", "rank": 2, "score": 9, "system": "s"},
        {"query": 1, "q0": "Q0", "docid": "d-3", "rank": 3, "score": 8, "system": "s"},
        {"query": 1, "q0": "Q0", "docid": "d-4", "rank": 4, "score": 7, "system": "s"},
        {"query": 2, "q0": "Q0", "docid": "d-1", "rank": 1, "score": 10, "system": "s"},
        {"query": 2, "q0": "Q0", "docid": "d-2", "rank": 2, "score": 9, "system": "s"},
        {"query": 2, "q0": "Q0", "docid": "d-3", "rank": 3, "score": 8, "system": "s"},
        {"query": 2, "q0": "Q0", "docid": "d-4", "rank": 4, "score": 7, "system": "s"},
        {"query": 3, "q0": "Q0", "docid": "d-1", "rank": 1, "score": 10, "system": "s"},
        {"query": 3, "q0": "Q0", "docid": "d-2", "rank": 2, "score": 9, "system": "s"},
        {"query": 3, "q0": "Q0", "docid": "d-3", "rank": 3, "score": 8, "system": "s"},
        {"query": 3, "q0": "Q0", "docid": "d-4", "rank": 4, "score": 7, "system": "s"},
    ]
)


VALID_PYTERRIER_RUN = pd.DataFrame(
    [
        {"qid": 1, "q0": "Q0", "docno": "d-1", "rank": 1, "score": 10, "system": "s"},
        {"qid": 1, "q0": "Q0", "docno": "d-2", "rank": 2, "score": 9, "system": "s"},
        {"qid": 1, "q0": "Q0", "docno": "d-4", "rank": 4, "score": 7, "system": "s"},
        {"qid": 2, "q0": "Q0", "docno": "d-1", "rank": 1, "score": 10, "system": "s"},
        {"qid": 2, "q0": "Q0", "docno": "d-2", "rank": 2, "score": 9, "system": "s"},
        {"qid": 2, "q0": "Q0", "docno": "d-3", "rank": 3, "score": 8, "system": "s"},
        {"qid": 2, "q0": "Q0", "docno": "d-4", "rank": 4, "score": 7, "system": "s"},
        {"qid": 3, "q0": "Q0", "docno": "d-1", "rank": 1, "score": 10, "system": "s"},
        {"qid": 3, "q0": "Q0", "docno": "d-2", "rank": 2, "score": 9, "system": "s"},
        {"qid": 3, "q0": "Q0", "docno": "d-3", "rank": 3, "score": 8, "system": "s"},
        {"qid": 3, "q0": "Q0", "docno": "d-4", "rank": 4, "score": 7, "system": "s"},
    ]
)


class TrecToolsRunMock:
    def __init__(self, run):
        self.run_data = run


class TestSerializationOfRunFiles(unittest.TestCase):
    def test_for_valid_run_file_as_path(self):
        input_file = VALID_RUN_OUTPUT / "run.txt"
        expected = 10
        actual_dir = serialize_in_temporary_directory(input_file, "run.txt")
        lines = lines_if_valid(actual_dir, "run.txt")

        self.assertEqual(expected, len(lines))

    def test_for_trectools_run(self):
        expected = 12
        actual_dir = serialize_in_temporary_directory(VALID_TRECTOOLS_RUN, "run.txt")
        lines = lines_if_valid(actual_dir, "run.txt")

        self.assertEqual(expected, len(lines))

    def test_for_pyterrier_run(self):
        expected = 11
        actual_dir = serialize_in_temporary_directory(VALID_PYTERRIER_RUN, "run.txt")
        lines = lines_if_valid(actual_dir, "run.txt")

        self.assertEqual(expected, len(lines))

    def test_for_trectools_run_in_rundata(self):
        expected = 12
        actual_dir = serialize_in_temporary_directory(TrecToolsRunMock(VALID_TRECTOOLS_RUN), "run.txt")
        lines = lines_if_valid(actual_dir, "run.txt")

        self.assertEqual(expected, len(lines))

    def test_for_pyterrier_run_in_rundata(self):
        expected = 11
        actual_dir = serialize_in_temporary_directory(TrecToolsRunMock(VALID_PYTERRIER_RUN), "run.txt")
        lines = lines_if_valid(actual_dir, "run.txt")

        self.assertEqual(expected, len(lines))

    def test_for_valid_run_file_as_str(self):
        input_file = str(VALID_RUN_OUTPUT / "run.txt")
        expected = 10
        actual_dir = serialize_in_temporary_directory(input_file, "run.txt")
        lines = lines_if_valid(actual_dir, "run.txt")

        self.assertEqual(expected, len(lines))

    def test_for_non_existing_file_as_path(self):
        input_file = VALID_RUN_OUTPUT / "does-not-exist"

        with self.assertRaises(Exception) as context:
            serialize_in_temporary_directory(input_file, "run.txt")

        self.assertTrue("The passed run file" in str(repr(context.exception)))

    def test_for_invalid_trectools_dataframe(self):
        input_dataframe = VALID_TRECTOOLS_RUN.copy()
        del input_dataframe["query"]

        with self.assertRaises(Exception) as context:
            serialize_in_temporary_directory(input_dataframe, "run.txt")

        self.assertTrue("The passed run is missing the required columns " in str(repr(context.exception)))

    def test_for_invalid_pyterrier_dataframe(self):
        input_dataframe = VALID_PYTERRIER_RUN.copy()
        del input_dataframe["qid"]

        with self.assertRaises(Exception) as context:
            serialize_in_temporary_directory(input_dataframe, "run.txt")

        self.assertTrue("The passed run is missing the required columns " in str(repr(context.exception)))
