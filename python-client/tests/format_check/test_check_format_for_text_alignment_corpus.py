import unittest

from . import (
    _ERROR,
    _OK,
    EMPTY_OUTPUT,
    TEXT_ALIGNMENT_CORPUS_INVALID,
    TEXT_ALIGNMENT_CORPUS_VALID_1,
    TEXT_ALIGNMENT_CORPUS_VALID_2,
)


def check_format(dir):
    from tira.check_format import check_format as cf

    return cf(dir, "text-alignment-corpus")


def lines_if_valid(dir):
    from tira.check_format import lines_if_valid as lf

    return lf(dir, "text-alignment-corpus")


class TestCheckJsonlForNonExistingFormats(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        expected = [_ERROR, "No unique pair file was found, only the files ['.gitkeep'] were available."]
        actual = check_format(EMPTY_OUTPUT)
        self.assertEqual(expected, actual)

    def test_invalid_text_alignment_corpus(self):
        expected = [
            _ERROR,
            "No unique text file was found for id suspicious-document00218.txt. Only ['pairs'] were available.",
        ]
        actual = check_format(TEXT_ALIGNMENT_CORPUS_INVALID)
        self.assertEqual(expected, actual)

    def test_valid_text_alignment_corpus_01(self):
        expected = [_OK, "The directory has the correct format."]
        actual = check_format(TEXT_ALIGNMENT_CORPUS_VALID_1)
        self.assertEqual(expected, actual)

    def test_valid_text_alignment_corpus_02(self):
        expected = [_OK, "The directory has the correct format."]
        actual = check_format(TEXT_ALIGNMENT_CORPUS_VALID_2)
        self.assertEqual(expected, actual)

    def test_lines_for_valid_corpus(self):
        expected = [
            {
                "suspicious_document_id": "suspicious-document00218",
                "suspicious_document_text": "suspicious-document00218\n",
                "source_document_id": "source-document00218",
                "source_document_text": "source-document00218\n",
            },
            {
                "suspicious_document_id": "suspicious-document00487",
                "suspicious_document_text": "suspicious-document00487\n",
                "source_document_id": "source-document00487",
                "source_document_text": "source-document00487\n",
            },
            {
                "suspicious_document_id": "suspicious-document00185",
                "suspicious_document_text": "suspicious-document00185\n",
                "source_document_id": "source-document00185",
                "source_document_text": "source-document00185\n",
            },
        ]
        actual = lines_if_valid(TEXT_ALIGNMENT_CORPUS_VALID_1)
        self.assertEqual(expected, actual)
