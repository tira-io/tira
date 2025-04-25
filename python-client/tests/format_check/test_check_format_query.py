import json
import tempfile
import unittest
from pathlib import Path

from approvaltests import verify_as_json

from tira.check_format import QueryProcessorFormat, check_format, lines_if_valid

from . import _ERROR, _OK, EMPTY_OUTPUT, IR_QUERY_OUTPUT


class TestQueryProcessorFormat(unittest.TestCase):
    def test_valid_query_processor_format(self):
        """Test that a valid query processor output directory passes validation."""
        expected = [_OK, "The jsonl file has the correct format."]
        actual = check_format(IR_QUERY_OUTPUT, "query-processor")
        self.assertEqual(expected, actual)

    def test_lines_for_valid_query_processor_format(self):
        """Test that a valid query processor output directory passes validation."""
        actual = lines_if_valid(IR_QUERY_OUTPUT, "query-processor")
        verify_as_json(actual)

    def test_error_message_on_empty_output(self):
        """Test error message when no jsonl file is found."""
        expected = [_ERROR, "No unique *.jsonl file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT, "query-processor")
        self.assertEqual(expected, actual)

    def test_query_processor_missing_query_id(self):
        """Test validation fails when an id is missing."""
        validator = QueryProcessorFormat()
        with self.assertRaises(ValueError) as context:
            validator.fail_if_json_line_is_not_valid(
                {
                    "wrong_id": "123",
                    "originalQuery": "test query",
                    "segmentationApproach": "test-approach",
                    "segmentation": ["segmen", "tation"],
                }
            )

        self.assertIn("At least one of ", str(context.exception))

    def test_query_processor_unequal_queries(self):
        """Test validation fails both possible id names are present and unequal."""
        validator = QueryProcessorFormat()
        with self.assertRaises(ValueError) as context:
            validator.fail_if_json_line_is_not_valid(
                {
                    "query_id": "123",
                    "qid": "456",
                    "originalQuery": "test query",
                    "segmentationApproach": "test-approach",
                    "segmentation": ["stuff", "more stuff"],
                }
            )

        self.assertIn("they must be equal", str(context.exception))

    def test_query_processor_duplicate_query_ids(self):
        """Test validation fails when duplicate query IDs are found."""
        # Create a temporary directory with a JSONL file containing duplicate query IDs
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Create JSONL file with duplicate query IDs
            jsonl_file = temp_dir_path / "queries.jsonl"
            with open(jsonl_file, "w") as f:
                f.write(
                    json.dumps({"qid": "123", "originalQuery": "first query", "segmentation": ["part1", "part2"]})
                    + "\n"
                )
                f.write(
                    json.dumps(
                        {"qid": "456", "originalQuery": "second query", "segmentation": ["segment1", "segment2"]}
                    )
                    + "\n"
                )
                f.write(
                    json.dumps(
                        {
                            "qid": "123",  # Duplicate ID
                            "originalQuery": "duplicate query",
                            "segmentation": ["foo", "bar"],
                        }
                    )
                    + "\n"
                )

            # Verify that validation fails
            validator = QueryProcessorFormat()
            with self.assertRaises(ValueError) as context:
                list(validator.yield_next_entry(temp_dir_path))

            self.assertIn("Query ID 123 is not unique", str(context.exception))
