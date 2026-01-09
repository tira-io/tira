import unittest

from tira.check_format import check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, IR_DATASET, TSV_OUTPUT_VALID, VALID_QREL_PATH


class TestCheckLsrCorpusFormat(unittest.TestCase):
    def test_invalid_validator_on_empty_output(self):
        actual = check_format(EMPTY_OUTPUT, "ir-dataset-corpus")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("No ir-dataset found.", actual[1])

    def test_invalid_tsv(self):
        actual = check_format(TSV_OUTPUT_VALID, "ir-dataset-corpus")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("No ir-dataset found.", actual[1])

    def test_invalid_qrel_file(self):
        actual = check_format(VALID_QREL_PATH, "ir-dataset-corpus")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("No ir-dataset found.", actual[1])

    def test_valid_ir_dataset(self):
        actual = check_format(IR_DATASET, "ir-dataset-corpus")
        self.assertEqual(_OK, actual[0])
        self.assertIn("Valid ir-dataset found.", actual[1])

    def test_valid_ir_dataset_01(self):
        actual = check_format(IR_DATASET, ["ir-dataset-corpus", "power-and-identification-truths"])
        self.assertEqual(_OK, actual[0], actual[1])
        self.assertIn("Valid ir-dataset found.", actual[1])

    def test_valid_ir_dataset_02(self):
        actual = check_format(
            IR_DATASET, ["ir-dataset-corpus", "power-and-identification-truths", "power-and-identification-predictions"]
        )
        self.assertEqual(_OK, actual[0], actual[1])
        self.assertIn("Valid ir-dataset found.", actual[1])
