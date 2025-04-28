import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, MAWSA_PROBLEMS, MAWSA_SOLUTIONS, MAWSA_TRUTHS


class TestMultiAuthorStyle(unittest.TestCase):
    def test_invalid_validator_on_empty_output_for_problems(self):
        expected = "no files matching the multi-author-style file pattern of 'problem-*.txt' in the directory"
        actual = check_format(EMPTY_OUTPUT, "multi-author-writing-style-analysis-problems")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_validator_on_empty_output_for_truths(self):
        expected = "no files matching the multi-author-style file pattern of 'truth-problem-*.json' in the directory"
        actual = check_format(EMPTY_OUTPUT, "multi-author-writing-style-analysis-truths")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_validator_on_empty_output_for_solutions(self):
        expected = "no files matching the multi-author-style file pattern of 'solution-problem-*.json' in the directory"
        actual = check_format(EMPTY_OUTPUT, "multi-author-writing-style-analysis-solutions")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_output_for_problems_01(self):
        expected = "no files matching the multi-author-style file pattern of 'truth-problem-*.json' in the directory"
        actual = check_format(MAWSA_PROBLEMS, "multi-author-writing-style-analysis-truths")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_output_for_problems_02(self):
        expected = "no files matching the multi-author-style file pattern of 'solution-problem-*.json' in the directory"
        actual = check_format(MAWSA_PROBLEMS, "multi-author-writing-style-analysis-solutions")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_output_for_solutions_01(self):
        expected = "no files matching the multi-author-style file pattern"
        actual = check_format(MAWSA_SOLUTIONS, "multi-author-writing-style-analysis-problems")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_output_for_solutions_02(self):
        expected = "no files matching the multi-author-style file pattern"
        actual = check_format(MAWSA_SOLUTIONS, "multi-author-writing-style-analysis-truths")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_output_for_truths_01(self):
        expected = "no files matching the multi-author-style file pattern"
        actual = check_format(MAWSA_TRUTHS, "multi-author-writing-style-analysis-problems")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn(expected, actual[1])

    def test_invalid_output_for_truths_02(self):
        expected = "no files matching the multi-author-style file pattern"
        actual = check_format(MAWSA_TRUTHS, "multi-author-writing-style-analysis-solutions")
        self.assertIn(expected, actual[1])
        self.assertEqual(_ERROR, actual[0])

    def test_valid_output_for_problems(self):
        expected = "Valid Multi-Author-Writing-Style directory"
        actual = check_format(MAWSA_PROBLEMS, "multi-author-writing-style-analysis-problems")
        self.assertIn(expected, actual[1])
        self.assertEqual(_OK, actual[0])

    def test_valid_output_for_truths(self):
        expected = "Valid Multi-Author-Writing-Style directory with"
        actual = check_format(MAWSA_TRUTHS, "multi-author-writing-style-analysis-truths")
        self.assertIn(expected, actual[1])
        self.assertEqual(_OK, actual[0])

    def test_valid_output_for_solutions(self):
        expected = "Valid Multi-Author-Writing-Style directory"
        actual = check_format(MAWSA_SOLUTIONS, "multi-author-writing-style-analysis-solutions")
        self.assertIn(expected, actual[1])
        self.assertEqual(_OK, actual[0])
