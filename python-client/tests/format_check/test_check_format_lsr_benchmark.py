import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, LSR_BENCHMARK_INPUTS


class TestQueryProcessorFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        actual = check_format(EMPTY_OUTPUT, "lsr-benchmark-inputs")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("No such file or directory", actual[1])

    def test_for_valid_dataset(self):
        expected = [_OK, "The dataset is in the format for the lsr-benchmark."]
        actual = check_format(LSR_BENCHMARK_INPUTS, "lsr-benchmark-inputs")
        self.assertEqual(expected, actual)
