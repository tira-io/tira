import tempfile
import unittest
from pathlib import Path

from tira.check_format import check_format_configuration_if_valid


class TestCheckFormatIfValid(unittest.TestCase):
    def test_01(self):
        expected = {"id_field": "id", "value_field": "label"}
        inp = {"id_field": "id", "value_field": "label"}
        actual = check_format_configuration_if_valid("*.jsonl", inp)
        self.assertEqual(expected, inp)
        self.assertIn("JsonlFormat", str(actual))

    def test_02(self):
        inp = None
        actual = check_format_configuration_if_valid("*.jsonl", inp)
        self.assertIsNone(inp)
        self.assertIn("JsonlFormat", str(actual))
