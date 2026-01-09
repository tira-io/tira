import unittest

from tira.rest_api_client import Client

# .. todo:: this file still uses "unclean" assertions and should be converted to use unittest assertions


class TestRestAPI(unittest.TestCase):
    tira: Client

    @classmethod
    def setUpClass(cls):
        TestRestAPI.tira = Client()

    def test_all_softwares_works_for_tirex(self):
        actual = TestRestAPI.tira.all_softwares("ir-benchmarks")

        assert "ir-benchmarks/tira-ir-starter/ChatNoir" in actual
        assert "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)" in actual

    def test_details_of_public_software_01(self):
        actual = TestRestAPI.tira.docker_software("ir-benchmarks/tira-ir-starter/TF_IDF (tira-ir-starter-pyterrier)")

        assert actual is not None
        assert actual["ir_re_ranker"] is False

    def test_output_of_run(self):
        actual = TestRestAPI.tira.get_run_output(
            "ir-benchmarks/tira-ir-starter/BM25 Re-Rank (tira-ir-starter-pyterrier)", "antique-test-20230107-training"
        )
        actual = open(actual / "run.txt", "r").read()

        assert actual.startswith("8293 Q0 8293_1 1 33.568841093129976 pyterrier.default_pipelines.wmodel_text_scorer")

    def test_output_of_run_for_redudant_dataset_id(self):
        actual = TestRestAPI.tira.get_run_output(
            "ir-benchmarks/tira-ir-starter/BM25 Re-Rank (tira-ir-starter-pyterrier)",
            "ir-benchmarks/antique-test-20230107-training",
        )
        actual = open(actual / "run.txt", "r").read()

        assert actual.startswith("8293 Q0 8293_1 1 33.568841093129976 pyterrier.default_pipelines.wmodel_text_scorer")

    def test_load_dataset_01(self):
        actual = TestRestAPI.tira.download_dataset("workshop-on-open-web-search", "retrieval-20231027-training")
        actual = open(actual / "queries.jsonl", "r").read()

        assert actual.startswith('{"qid": "1", "query": "hubble telescope achievements"}')

    def test_load_dataset_02(self):
        actual = TestRestAPI.tira.download_dataset(
            "workshop-on-open-web-search", "workshop-on-open-web-search/retrieval-20231027-training"
        )
        actual = open(actual / "queries.jsonl", "r").read()

        assert actual.startswith('{"qid": "1", "query": "hubble telescope achievements"}')
