import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, IR_DOCUMENT_OUTPUT


class TestDocumentProcessorFormat(unittest.TestCase):
    def test_valid_document_processor_format(self):
        """Test that a valid query processor output directory passes validation."""
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(IR_DOCUMENT_OUTPUT, "document-processor")
        self.assertEqual(expected, actual)

    def test_error_message_on_empty_output(self):
        """Test error message when no jsonl file is found."""
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "document-processor")
        self.assertEqual(expected, actual)
