import unittest

from tira.rest_api_client import Client


class TestLocalExecutionIntegrationTest(unittest.TestCase):
    def test_pd_load_inputs_wows_re_ranking(self):
        tira = Client()
        actual = tira.pd.inputs("workshop-on-open-web-search", "re-ranking-20231027-training")
        self.assertEqual(6, len(actual))
        self.assertEqual("hubble telescope achievements", actual.iloc[0]["query"])
        self.assertEqual("The Hubble telescope discovered two moons of Pluto, Nix and Hydra.", actual.iloc[0]["text"])
        self.assertEqual(1, actual.iloc[0]["rank"])
        self.assertEqual("1", actual.iloc[0]["qid"])

    def test_pd_load_inputs_wows_re_ranking_02(self):
        tira = Client()
        actual = tira.pd.inputs("re-ranking-20231027-training")
        self.assertEqual(6, len(actual))
        self.assertEqual("hubble telescope achievements", actual.iloc[0]["query"])
        self.assertEqual("The Hubble telescope discovered two moons of Pluto, Nix and Hydra.", actual.iloc[0]["text"])
        self.assertEqual(1, actual.iloc[0]["rank"])
        self.assertEqual("1", actual.iloc[0]["qid"])

    def test_pd_load_truths_wows_re_ranking(self):
        tira = Client()
        actual = tira.pd.truths("workshop-on-open-web-search", "re-ranking-20231027-training")
        self.assertEqual(3, len(actual))
        self.assertEqual("hubble telescope achievements", actual.iloc[0]["query"])
        self.assertEqual("1", actual.iloc[0]["qid"])

    def test_pd_load_truths_wows_re_ranking_02(self):
        tira = Client()
        actual = tira.pd.truths("re-ranking-20231027-training")
        self.assertEqual(3, len(actual))
        self.assertEqual("hubble telescope achievements", actual.iloc[0]["query"])
        self.assertEqual("1", actual.iloc[0]["qid"])

    def test_pd_load_truths_local_cached_zip(self):
        tira = Client(tira_cache_dir="tests/resources/local_cached_zip")
        actual = tira.pd.truths("task-does-not-exist", "dataset-does-not-exist-20241201-training")
        self.assertEqual(13, len(actual))
        first_line = actual.iloc[0].to_dict()
        last_line = actual.iloc[12].to_dict()

        self.assertEqual("5a8865b0-19d7-4b33-bbe3-2f64ad54557f", first_line["id"])
        self.assertEqual("1051399", first_line["query_id"])
        self.assertEqual(3376628, first_line["unknown_doc_id"])
        self.assertEqual(0, first_line["qrel_unknown_doc"])

        self.assertEqual("449f69fa-df0e-4c9e-aead-61983ce9eaa8", last_line["id"])
        self.assertEqual("833860", last_line["query_id"])
        self.assertEqual(2830558, last_line["unknown_doc_id"])
        self.assertEqual(0, last_line["qrel_unknown_doc"])

    def test_pd_load_inputs_local_cached_zip(self):
        tira = Client(tira_cache_dir="tests/resources/local_cached_zip")
        actual = tira.pd.inputs("task-does-not-exist", "dataset-does-not-exist-20241201-training")
        self.assertEqual(13, len(actual))
        first_line = actual.iloc[0].to_dict()
        last_line = actual.iloc[12].to_dict()

        self.assertEqual("5a8865b0-19d7-4b33-bbe3-2f64ad54557f", first_line["id"])
        self.assertTrue("query_id" not in first_line)
        self.assertTrue("unknown_doc_id" not in first_line)
        self.assertTrue("qrel_unknown_doc" not in first_line)

        self.assertEqual("449f69fa-df0e-4c9e-aead-61983ce9eaa8", last_line["id"])
        self.assertTrue("query_id" not in last_line)
        self.assertTrue("unknown_doc_id" not in last_line)
        self.assertTrue("qrel_unknown_doc" not in last_line)

    def test_pd_load_truths_local_cached_zip_single_identifier(self):
        tira = Client(tira_cache_dir="tests/resources/local_cached_zip")
        actual = tira.pd.truths("task-does-not-exist/dataset-does-not-exist-20241201-training")
        self.assertEqual(13, len(actual))
        first_line = actual.iloc[0].to_dict()
        last_line = actual.iloc[12].to_dict()

        self.assertEqual("5a8865b0-19d7-4b33-bbe3-2f64ad54557f", first_line["id"])
        self.assertEqual("1051399", first_line["query_id"])
        self.assertEqual(3376628, first_line["unknown_doc_id"])
        self.assertEqual(0, first_line["qrel_unknown_doc"])

        self.assertEqual("449f69fa-df0e-4c9e-aead-61983ce9eaa8", last_line["id"])
        self.assertEqual("833860", last_line["query_id"])
        self.assertEqual(2830558, last_line["unknown_doc_id"])
        self.assertEqual(0, last_line["qrel_unknown_doc"])

    def test_pd_load_inputs_local_cached_zip_single_identifier(self):
        tira = Client(tira_cache_dir="tests/resources/local_cached_zip")
        actual = tira.pd.inputs("task-does-not-exist/dataset-does-not-exist-20241201-training")
        self.assertEqual(13, len(actual))
        first_line = actual.iloc[0].to_dict()
        last_line = actual.iloc[12].to_dict()

        self.assertEqual("5a8865b0-19d7-4b33-bbe3-2f64ad54557f", first_line["id"])
        self.assertTrue("query_id" not in first_line)
        self.assertTrue("unknown_doc_id" not in first_line)
        self.assertTrue("qrel_unknown_doc" not in first_line)

        self.assertEqual("449f69fa-df0e-4c9e-aead-61983ce9eaa8", last_line["id"])
        self.assertTrue("query_id" not in last_line)
        self.assertTrue("unknown_doc_id" not in last_line)
        self.assertTrue("qrel_unknown_doc" not in last_line)
