import unittest
from tira.ir_datasets_loader import translate_irds_id_to_tirex

class TestHfMountsAreParsed(unittest.TestCase):
    def test_translation_does_change_nothing_for_unknown_id(self):
        expected = 'tmp'
        actual = translate_irds_id_to_tirex('tmp')

        self.assertEqual(expected, actual)

    def test_translation_changes_for_tirex_id(self):
        expected = 'nfcorpus-test-20230107-training'
        actual = translate_irds_id_to_tirex('nfcorpus/test')

        self.assertEqual(expected, actual)
