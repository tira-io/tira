import unittest
from pathlib import Path

from tira.check_format import QueryProcessorFormat, check_format, lines_if_valid

from . import (
    _ERROR, 
    _OK, 
    EMPTY_OUTPUT,
    IR_QUERY_OUTPUT,
    )

class TestQueryProcessorFormat(unittest.TestCase):
    def test_valid_query_processor_format(self):
        """Test that a valid query processor output directory passes validation."""
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(IR_QUERY_OUTPUT, "query-processor")
        self.assertEqual(expected, actual)
    
    def test_error_message_on_empty_output(self):
        """Test error message when no jsonl file is found."""
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "query-processor")
        self.assertEqual(expected, actual)
    
    def test_query_processor_segmentation_must_be_list(self):
        """Test validation fails when segmentation is not a list."""
        validator = QueryProcessorFormat()
        with self.assertRaises(ValueError) as context:
            validator.fail_if_json_line_is_not_valid({
                "qid": "123",
                "originalQuery": "test query",
                "segmentationApproach": "test-approach",
                "segmentation": "not a list"  # This should fail
            })
        
        self.assertIn("must be a list", str(context.exception))
    
    def test_query_processor_segmentation_cannot_be_empty(self):
        """Test validation fails when segmentation is an empty list."""
        validator = QueryProcessorFormat()
        with self.assertRaises(ValueError) as context:
            validator.fail_if_json_line_is_not_valid({
                "qid": "123",
                "originalQuery": "test query",
                "segmentationApproach": "test-approach",
                "segmentation": []  # This should fail
            })
        
        self.assertIn("cannot be empty", str(context.exception))