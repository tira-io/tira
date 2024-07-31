import unittest

import pandas as pd

from tira.local_client import Client

# .. todo:: this file still uses "unclean" assertions and should be converted to use unittest assertions


def keyphrase_extraction(docs):
    queries = pd.DataFrame([{"docno": str(i)} for i in docs])
    tira = Client("tests/resources/")
    query_segmentation = tira.pt.transform_documents(
        "ir-benchmarks/webis-keyphrase-extraction/BCExtractorFO", dataset="d1"
    )

    ret = query_segmentation(queries)
    return {i["docno"]: i["keyphrases"] for _, i in ret.iterrows()}


def doc_processor(docs, name):
    queries = pd.DataFrame([{"docno": str(i)} for i in docs])
    tira = Client("tests/resources/")
    query_segmentation = tira.pt.transform_documents("ir-benchmarks/tira-ir-starters/" + name, dataset="d1")

    ret = query_segmentation(queries)
    return {i["docno"]: i["key"] for _, i in ret.iterrows()}


class TestPtDocumentProcessingLoaderTest(unittest.TestCase):
    def test_for_loading_keyphrase_extraction_for_multiple_documents(self):
        expected = {
            "FT921-3964": [
                "increased economic aid",
                "king hussein",
                "increase aid",
                "president george bush",
                "tariq aziz iraq's deputy prime minister",
            ],
            "LA061489-0137": [
                "public appearances gorbachev",
                "crowds",
                "government ministries gorbachev",
                "place gorbachev",
                "west german well-wishers",
            ],
        }

        actual = keyphrase_extraction(["FT921-3964", "LA061489-0137"])

        assert len(actual) == 2
        assert actual["FT921-3964"] == expected["FT921-3964"]
        assert actual["LA061489-0137"] == expected["LA061489-0137"]

    def test_for_loading_keyphrase_extraction_for_single_documents(self):
        expected = {
            "LA120390-0047": [
                "even friendly technology takeovers",
                "largest technology takeover",
                "computer industry takeover",
                "statement sunday",
                "attempts",
            ]
        }

        actual = keyphrase_extraction(["LA120390-0047"])

        assert len(actual) == 1
        assert actual["LA120390-0047"] == expected["LA120390-0047"]

    def test_pyterrier_can_be_loaded(self):
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()

    def test_document_transformation_with_docno(self):
        expected = {"doc-01": "value"}
        actual = doc_processor(["doc-01"], "tiny-example-01")

        self.assertEqual(expected, actual)

    def test_document_transformation_with_doc_id(self):
        expected = {"doc-01": "value"}
        actual = doc_processor(["doc-01"], "tiny-example-02")

        self.assertEqual(expected, actual)

    def test_document_features_with_doc_id(self):
        expected = ["value"]

        documents = pd.DataFrame([{"docno": str(i)} for i in ["doc-01"]])
        tira = Client("tests/resources/")
        doc_features = tira.pt.doc_features("ir-benchmarks/tira-ir-starters/tiny-example-02", dataset="d1")

        actual = doc_features(documents)

        self.assertEqual(1, len(actual))
        self.assertEqual(expected, actual.iloc[0].to_dict()["features"])

    def test_document_features_with_docno(self):
        expected = ["value"]

        documents = pd.DataFrame([{"docno": str(i)} for i in ["doc-01"]])
        tira = Client("tests/resources/")
        doc_features = tira.pt.doc_features("ir-benchmarks/tira-ir-starters/tiny-example-01", dataset="d1")

        actual = doc_features(documents)

        self.assertEqual(1, len(actual))
        self.assertEqual(expected, actual.iloc[0].to_dict()["features"])
