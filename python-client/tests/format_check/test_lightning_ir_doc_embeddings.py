import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, LIGTHNING_IR_DOCUMENT_EMBEDDINGS, TSV_OUTPUT_VALID, VALID_QREL_PATH


class TestLightningIrDocEmbeddingFormat(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        actual = check_format(EMPTY_OUTPUT, "lightning-ir-document-embeddings")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("No lightning-ir embeddings found.", actual[1])

    def test_invalid_tsv(self):
        actual = check_format(TSV_OUTPUT_VALID, "lightning-ir-document-embeddings")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("No lightning-ir embeddings found.", actual[1])

    def test_invalid_qrel_file(self):
        actual = check_format(VALID_QREL_PATH, "lightning-ir-document-embeddings")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("No lightning-ir embeddings found.", actual[1])

    def test_valid_doc_embeddings(self):
        actual = check_format(LIGTHNING_IR_DOCUMENT_EMBEDDINGS, "lightning-ir-document-embeddings")
        self.assertEqual(_OK, actual[0])
        self.assertIn("Valid lightning-ir embeddings found", actual[1])

    def test_valid_doc_embeddings_recursive(self):
        actual = check_format(LIGTHNING_IR_DOCUMENT_EMBEDDINGS.parent, "lightning-ir-document-embeddings")
        self.assertEqual(_OK, actual[0])
        self.assertIn("Valid lightning-ir embeddings found", actual[1])
