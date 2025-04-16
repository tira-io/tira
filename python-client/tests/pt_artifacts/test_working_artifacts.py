import unittest

import pandas as pd

from . import load_artifact


class TestWorkingArtifacts(unittest.TestCase):
    def test_bm25_artifact(self):
        expected = {
            "qid": "51",
            "docno": "S885c6b4f-Ad3259e81",
            "rank": 1,
            "score": 26.07818108898493,
            "name": "pyterrier.default_pipelines.wmodel_batch_retrieve",
        }
        bm25 = load_artifact(
            "tira:argsme/2020-04-01/touche-2021-task-1/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)"
        )

        run = bm25.transform(pd.DataFrame([{"qid": "51"}]))
        actual = run.iloc[0].to_dict()
        self.assertEqual(expected, actual)

    def test_hyb_a_query_segmentation_artifact(self):
        expected = ["should", "blood donations", "be financially compensated"]
        hyb_a = load_artifact("tira:argsme/2020-04-01/touche-2021-task-1/ows/query-segmentation-hyb-a")

        self.assertIsNotNone(hyb_a)
        actual = hyb_a.transform(pd.DataFrame([{"qid": "53"}])).iloc[0].to_dict()
        self.assertIn("segmentation", actual)
        self.assertEqual(expected, actual["segmentation"])

    def test_doc_t5_query_artifact(self):
        expected = "including fluid motion"
        docT5Query = load_artifact("tira:cranfield/seanmacavaney/DocT5Query (Local)")

        self.assertIsNotNone(docT5Query)
        actual = docT5Query.transform(pd.DataFrame([{"docno": "873"}])).iloc[0].to_dict()
        self.assertIn("text", actual)
        self.assertIn(expected, actual["text"])

    def test_index_artifact(self):
        import pyterrier as pt

        index = load_artifact("tira:cranfield/tira-ir-starter/Index (tira-ir-starter-pyterrier)")

        self.assertIn("IndexRef", str(index))
        run = pt.terrier.Retriever(index).search("chemical reactions")
        actual = run.iloc[0].to_dict()
        self.assertIsNotNone(actual)
        self.assertEqual("488", actual["docno"])
