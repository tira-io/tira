import unittest

from tira.rest_api_client import Client


class TestExportFromZenodo(unittest.TestCase):
    def test_pd_load_truths_local_cached_zip(self):
        tira = Client(tira_cache_dir="tests/resources/local_cached_zip")
        actual = tira.pd.inputs("wows-eval-foooo", "pointwise-20250309-test-foooo")
        self.assertEqual(2, len(actual))
        first_line = actual.iloc[0].to_dict()
        last_line = actual.iloc[-1].to_dict()
        self.assertEqual("e1786a4d-2b3d-4fcf-ad84-443acf3696e2", first_line["id"])
        self.assertEqual("931bbd92-c9c7-48af-b91f-9cfb7c2abdcb", last_line["id"])

    def test_pd_load_truths_local_cached_zip_02(self):
        tira = Client(tira_cache_dir="tests/resources/local_cached_zip")
        actual = tira.pd.inputs("pointwise-20250309-test-foooo")
        self.assertEqual(2, len(actual))
        first_line = actual.iloc[0].to_dict()
        last_line = actual.iloc[-1].to_dict()
        self.assertEqual("e1786a4d-2b3d-4fcf-ad84-443acf3696e2", first_line["id"])
        self.assertEqual("931bbd92-c9c7-48af-b91f-9cfb7c2abdcb", last_line["id"])

    def test_pd_load_truths_local_cached_zip_03(self):
        tira = Client(tira_cache_dir="tests/resources/local_cached_zip")
        actual = tira.pd.inputs("pointwise")
        self.assertEqual(2, len(actual))
        first_line = actual.iloc[0].to_dict()
        last_line = actual.iloc[-1].to_dict()
        self.assertEqual("e1786a4d-2b3d-4fcf-ad84-443acf3696e2", first_line["id"])
        self.assertEqual("931bbd92-c9c7-48af-b91f-9cfb7c2abdcb", last_line["id"])
