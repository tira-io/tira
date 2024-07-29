import json
import unittest

import pandas as pd
from approvaltests import verify_as_json

from tira.local_client import Client


def retrieval_submission(queries):
    queries = pd.DataFrame([{"qid": str(i)} for i in queries])
    tira = Client("tests/resources/")
    retriever = tira.pt.from_retriever_submission("ir-benchmarks/tira-ir-starters/retriever", dataset="d1")

    ret = retriever(queries)
    return [{"qid": i["qid"], "docno": i["docno"], "score": i["score"]} for _, i in ret.iterrows()]


class TestPtFromRetrieverSubmissionLoaderTest(unittest.TestCase):
    def test_for_multiple_queries(self):
        expected = [
            {"qid": "1", "docno": "doc-1", "score": 10},
            {"qid": "1", "docno": "doc-2", "score": 9},
            {"qid": "3", "docno": "doc-3", "score": 1},
        ]

        actual = retrieval_submission([1, 3])

        self.assertEqual(len(actual), 3)
        self.assertEqual(actual[0], expected[0])
        self.assertEqual(actual[1], expected[1])
        self.assertEqual(actual[2], expected[2])

    def test_cascading_with_retriever_is_idempotent_01(self):
        queries = pd.DataFrame([{"qid": str(i)} for i in [1]])
        tira = Client("tests/resources/")
        retriever = tira.pt.from_retriever_submission("ir-benchmarks/tira-ir-starters/retriever", dataset="d1")

        ret = (retriever >> retriever).search(queries)
        ret = [json.loads((i.to_json())) for _, i in ret.iterrows()]
        verify_as_json(ret)

    def test_cascading_with_retriever_is_idempotent_02(self):
        queries = pd.DataFrame([{"qid": str(i)} for i in [1]])
        tira = Client("tests/resources/")
        retriever = tira.pt.from_retriever_submission("ir-benchmarks/tira-ir-starters/retriever", dataset="d1")

        ret = (retriever >> retriever >> retriever >> retriever).search(queries)
        ret = [json.loads((i.to_json())) for _, i in ret.iterrows()]
        verify_as_json(ret)

    def test_cascading_with_retriever_is_idempotent_03(self):
        queries = pd.DataFrame([{"qid": str(i)} for i in [1]])
        tira = Client("tests/resources/")
        retriever = tira.pt.from_retriever_submission("ir-benchmarks/tira-ir-starters/retriever", dataset="d1")

        ret = (
            (retriever >> retriever >> retriever >> retriever) >> (retriever >> retriever >> retriever >> retriever)
        ).search(queries)
        ret = [json.loads((i.to_json())) for _, i in ret.iterrows()]
        verify_as_json(ret)

    def test_feature_union_from_retriever_01(self):
        queries = pd.DataFrame([{"qid": str(i)} for i in [1]])
        tira = Client("tests/resources/")
        retriever = tira.pt.from_retriever_submission("ir-benchmarks/tira-ir-starters/retriever", dataset="d1")

        ret = (retriever >> (retriever**retriever)).search(queries)
        ret = [json.loads((i.to_json())) for _, i in ret.iterrows()]
        verify_as_json(ret)

    def test_feature_union_from_retriever_02(self):
        queries = pd.DataFrame([{"qid": str(i)} for i in [1]])
        tira = Client("tests/resources/")
        retriever = tira.pt.from_retriever_submission("ir-benchmarks/tira-ir-starters/retriever", dataset="d1")

        ret = (retriever >> (retriever**retriever**retriever**retriever)).search(queries)
        ret = [json.loads((i.to_json())) for _, i in ret.iterrows()]
        verify_as_json(ret)

    def test_for_single_query_no_1(self):
        expected = [
            {"qid": "1", "docno": "doc-1", "score": 10},
            {"qid": "1", "docno": "doc-2", "score": 9},
        ]

        actual = retrieval_submission([1])

        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0], expected[0])
        self.assertEqual(actual[1], expected[1])

    def test_for_single_query_no_3(self):
        expected = [
            {"qid": "3", "docno": "doc-3", "score": 1},
        ]

        actual = retrieval_submission([3])

        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0], expected[0])

    def test_retrieval_submission_from_rest_api(self):
        import pyterrier as pt

        from tira.rest_api_client import Client
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()
        tira = Client()

        q = tira.pt.from_submission(
            "ir-benchmarks/tira-ir-starter/BM25 Re-Rank (tira-ir-starter-pyterrier)",
            pt.get_dataset("irds:disks45/nocr/trec-robust-2004"),
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "306"}]))), 1000)
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[0].to_dict()["docno"], "LA021790-0114")
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[0].to_dict()["qid"], "306")
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[999].to_dict()["docno"], "FBIS4-47956")
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[999].to_dict()["qid"], "306")

    def test_retrieval_submission_from_rest_api_different_id(self):
        import pyterrier as pt

        from tira.rest_api_client import Client
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()
        tira = Client()

        q = tira.pt.from_submission(
            "ir-benchmarks/tira-ir-starter/BM25 Re-Rank (tira-ir-starter-pyterrier)",
            pt.get_dataset("irds:ir-benchmarks/disks45-nocr-trec-robust-2004-20230209-training"),
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "306"}]))), 1000)
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[0].to_dict()["docno"], "LA021790-0114")
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[0].to_dict()["qid"], "306")
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[999].to_dict()["docno"], "FBIS4-47956")
        self.assertEqual(q(pd.DataFrame([{"qid": "306"}])).iloc[999].to_dict()["qid"], "306")
