import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, AGGREGATED_RESULTS_OUTPUT_VALID, EMPTY_OUTPUT, IR_QUERY_OUTPUT, VALID_RUN_OUTPUT


class TestCheckAggregatedResultsFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No aggregated-results.json files."]
        actual = check_format(EMPTY_OUTPUT, "aggregated-results.json")
        self.assertEqual(expected, actual)

    def test_invalid_validator_on_query_output(self):
        expected = [_ERROR, "No aggregated-results.json files."]
        actual = check_format(IR_QUERY_OUTPUT, "aggregated-results.json")
        self.assertEqual(expected, actual)

    def test_invalid_trec_run_file(self):
        expected = [_ERROR, "No aggregated-results.json files."]
        actual = check_format(VALID_RUN_OUTPUT, "aggregated-results.json")
        self.assertEqual(expected, actual)

    def test_valid_tsv(self):
        expected = [_OK, "The agregated-results.json file has the correct format."]
        actual = check_format(AGGREGATED_RESULTS_OUTPUT_VALID, "aggregated-results.json")
        self.assertEqual(expected, actual)
