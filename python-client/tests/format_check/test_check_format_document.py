import unittest
from pathlib import Path
from tira.check_format import DocumentProcessorFormat, check_format, lines_if_valid

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    DOCUMENT_PROCESSING_OUTPUT,
)

class TestDocumentProcessorFormat(unittest.TestCase):
    def test_valid_document_processor_format(self):
            """Test that a valid document processor output directory passes validation."""
            expected = [_OK, "The jsonl file has the correct format."]
            actual = check_format(DOCUMENT_PROCESSING_OUTPUT, "document-processor")
            self.assertEqual(expected, actual)  

    def test_error_message_on_empty_output(self):
        """Test error message when no jsonl file is found."""
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "query-processor")
        self.assertEqual(expected, actual)

    def test_missing_required_field(self):
        """Test validation fails when arguments are missing"""
        validator = DocumentProcessorFormat()
        with self.assertRaises(ValueError) as context: 
            validator.fail_if_json_line_is_not_valid({
                "key": "test"})
            
        self.assertIn("misses the required field", str(context.exception))
