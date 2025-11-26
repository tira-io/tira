import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, JSONL_OUTPUT_VALID, WOWS26_COMPLETE, WOWS26_INCOMPLETE


class TestRunWithIrMetadataFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        actual = check_format(EMPTY_OUTPUT, "run-with-metadata")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file ir-metadata.yml in the directory", actual[1])

    def test_error_message_on_jsonl_output(self):
        actual = check_format(JSONL_OUTPUT_VALID, "run-with-metadata")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file ir-metadata.yml in the directory", actual[1])

    def test_error_message_on_incomplete_metadata(self):
        actual = check_format(WOWS26_INCOMPLETE, "run-with-metadata")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The required field actor.team still contains", actual[1])

    def test_ok_message_on_complete_metadata(self):
        actual = check_format(WOWS26_COMPLETE, "run-with-metadata")
        self.assertEqual(_OK, actual[0])
        self.assertIn("/complete is valid.", actual[1])
        self.assertIn("ir-metadata.yml is valid.", actual[1])
