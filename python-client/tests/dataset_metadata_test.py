import unittest
from pathlib import Path

from tira.rest_api_client import Client

RESOURCES = Path(__file__).parent.parent / "resources"
CACHE_DIR_WITH_DATASETS = RESOURCES / "cache-dir-with-datasets"


class DatasetMetadataTest(unittest.TestCase):
    def test_error_message_for_non_existing_dataset(self):
        expected_message = 'The dataset "does-not-exist" is not publicly available in TIRA. Please visit https://tira.io/datasets for an overview of all public datasets.'
        tira = Client()

        with self.assertRaises(Exception) as context:
            tira.get_dataset("does-not-exist")

        self.assertTrue(expected_message in str(repr(context.exception)))

    def test_ir_dataset_with_tira_id_and_wrong_task(self):
        expected_message = 'The dataset "does-not-exist/clueweb09-en-trec-web-2009-20230107-training" is not publicly available in TIRA. Please visit https://tira.io/datasets for an overview of all public datasets.'
        tira = Client()

        with self.assertRaises(Exception) as context:
            tira.get_dataset("does-not-exist/clueweb09-en-trec-web-2009-20230107-training")

        self.assertTrue(expected_message in str(repr(context.exception)))

    def test_ir_dataset_with_tira_id(self):
        tira = Client()
        expected = "clueweb09-en-trec-web-2009-20230107-training"
        actual = tira.get_dataset("clueweb09-en-trec-web-2009-20230107-training")

        self.assertIsNotNone(actual)
        self.assertEqual(expected, actual["id"])

    def test_ir_dataset_with_tira_id_and_task(self):
        tira = Client()
        expected = "clueweb09-en-trec-web-2009-20230107-training"
        actual = tira.get_dataset("ir-benchmarks/clueweb09-en-trec-web-2009-20230107-training")

        self.assertIsNotNone(actual)
        self.assertEqual(expected, actual["id"])

    def test_ir_dataset_with_ir_datasets_id_01(self):
        tira = Client()
        expected = "clueweb09-en-trec-web-2009-20230107-training"
        actual = tira.get_dataset("clueweb09/en/trec-web-2009")

        self.assertIsNotNone(actual)
        self.assertEqual(expected, actual["id"])

    def test_ir_dataset_with_ir_datasets_id_02(self):
        tira = Client()
        expected = "clueweb09-en-trec-web-2010-20230107-training"
        actual = tira.get_dataset("clueweb09/en/trec-web-2010")

        self.assertIsNotNone(actual)
        self.assertEqual(expected, actual["id"])
