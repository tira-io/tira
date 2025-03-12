import unittest

from tira.check_format import GenIrSimulationFormat, check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, GEN_IR_SIM_OUTPUT_VALID, JSONL_OUTPUT_VALID


class TestGenIrSimulationFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "GenIR-Simulation")
        self.assertEqual(expected, actual)

    def test_error_message_for_other_jsonl_format(self):
        expected = [_ERROR, 'The json line misses the required field "simulation".']
        actual = check_format(JSONL_OUTPUT_VALID, "GenIR-Simulation")
        self.assertEqual(expected, actual)

    def test_invalid_validator_on_empty_output(self):
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(GEN_IR_SIM_OUTPUT_VALID, "GenIR-Simulation")
        self.assertEqual(expected, actual)

    def test_simulation_alone_is_not_valid(self):
        f = GenIrSimulationFormat()
        with self.assertRaises(ValueError):
            f.fail_if_json_line_is_not_valid({"simulation": {}})

    def test_simulation_without_user_turns_is_not_valid(self):
        f = GenIrSimulationFormat()
        with self.assertRaises(ValueError):
            f.fail_if_json_line_is_not_valid({"simulation": {"configuration": {}}})
