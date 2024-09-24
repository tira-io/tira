import unittest

import pandas as pd

from tira.local_client import Client


def query_segmentation(queries):
    queries = pd.DataFrame([{"qid": str(i)} for i in queries])
    tira = Client("tests/resources/")
    query_segmentation = tira.pt.transform_queries(
        "ir-benchmarks/webis-query-segmentation/wt-snp-baseline", dataset="d1"
    )

    ret = query_segmentation(queries)
    return {i["qid"]: i["segmentation"] for _, i in ret.iterrows()}


class TestQueryProcessingLoader(unittest.TestCase):
    def test_for_loading_query_segmentations_for_multiple_queries(self):
        expected = {"350": ["health and", "computer terminals"], "353": ["antarctica", "exploration"]}

        actual = query_segmentation([350, 353])

        self.assertEqual(len(actual), 2)
        self.assertEqual(actual["350"], expected["350"])
        self.assertEqual(actual["353"], expected["353"])

    def test_for_loading_query_segmentations_for_single_query(self):
        expected = {"351": ["falkland", "petroleum exploration"]}

        actual = query_segmentation([351])

        self.assertEqual(len(actual), 1)
        self.assertEqual(actual["351"], expected["351"])

    def test_pyterrier_can_be_loaded(self):
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()

    def test_rest_query_submission_with_rest_api_01(self):
        from tira.rest_api_client import Client

        tira = Client()

        q = tira.pt.transform_queries(
            "ir-benchmarks/ows/query-segmentation-wt-snp", "disks45-nocr-trec-robust-2004-20230209-training"
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "303"}]))), 1)
        self.assertEqual(
            q(pd.DataFrame([{"qid": "303"}])).iloc[0].to_dict()["segmentation"], ["hubble telescope achievements"]
        )

    def test_rest_query_submission_with_rest_api_02(self):
        from tira.rest_api_client import Client

        tira = Client()

        q = tira.pt.transform_queries(
            "ir-benchmarks/ows/query-segmentation-hyb-a", "disks45-nocr-trec-robust-2004-20230209-training"
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "303"}]))), 1)
        self.assertEqual(
            q(pd.DataFrame([{"qid": "303"}])).iloc[0].to_dict()["segmentation"], ["hubble telescope", "achievements"]
        )

    def test_rest_query_submission_with_rest_api_03(self):
        import pyterrier as pt

        from tira.rest_api_client import Client
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()
        tira = Client()

        q = tira.pt.transform_queries(
            "ir-benchmarks/fschlatt/query-health-classification", pt.get_dataset("irds:clueweb09/en/trec-web-2009")
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "26"}]))), 1)
        self.assertEqual(q(pd.DataFrame([{"qid": "26"}])).iloc[0].to_dict()["mean_health_score"], 168.416)
        self.assertEqual(q(pd.DataFrame([{"qid": "26"}])).iloc[0].to_dict()["median_health_score"], 130.3137)

    def test_rest_query_submission_with_rest_api_and_custom_selection(self):
        import pyterrier as pt

        from tira.rest_api_client import Client
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()
        tira = Client()

        q = tira.pt.transform_queries(
            "ir-benchmarks/fschlatt/query-health-classification",
            pt.get_dataset("irds:clueweb09/en/trec-web-2009"),
            "/q*.jsonl",
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "26"}]))), 1)
        self.assertEqual(q(pd.DataFrame([{"qid": "26"}])).iloc[0].to_dict()["mean_health_score"], 168.416)
        self.assertEqual(q(pd.DataFrame([{"qid": "26"}])).iloc[0].to_dict()["median_health_score"], 130.3137)

    def test_rest_query_submission_with_rest_api_04(self):
        import pyterrier as pt

        from tira.rest_api_client import Client
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()
        tira = Client()

        q = tira.pt.transform_queries(
            "ir-benchmarks/qpptk/fixed-sealer", pt.get_dataset("irds:disks45/nocr/trec-robust-2004")
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "301"}]))), 1)
        self.assertEqual(q(pd.DataFrame([{"qid": "301"}])).iloc[0].to_dict()["max-idf"], 3.5629408815)
        self.assertEqual(q(pd.DataFrame([{"qid": "301"}])).iloc[0].to_dict()["avg-idf"], 2.4740487603)

    def test_rest_query_features(self):
        import pyterrier as pt

        from tira.rest_api_client import Client
        from tira.third_party_integrations import ensure_pyterrier_is_loaded

        ensure_pyterrier_is_loaded()
        tira = Client()

        q = tira.pt.query_features(
            "ir-benchmarks/qpptk/fixed-sealer", pt.get_dataset("irds:disks45/nocr/trec-robust-2004")
        )
        self.assertEqual(len(q(pd.DataFrame([{"qid": "301"}]))), 1)
        self.assertEqual(q(pd.DataFrame([{"qid": "301"}])).iloc[0].to_dict()["features"][0], 3.5629408815)
        self.assertEqual(q(pd.DataFrame([{"qid": "301"}])).iloc[0].to_dict()["features"][1], 2.4740487603)
