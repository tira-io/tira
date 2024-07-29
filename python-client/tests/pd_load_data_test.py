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

    def test_pd_load_truths_wows_re_ranking(self):
        tira = Client()
        actual = tira.pd.truths("workshop-on-open-web-search", "re-ranking-20231027-training")
        self.assertEqual(3, len(actual))
        self.assertEqual("hubble telescope achievements", actual.iloc[0]["query"])
        self.assertEqual("1", actual.iloc[0]["qid"])
