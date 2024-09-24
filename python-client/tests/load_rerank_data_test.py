import os
import unittest

import ir_datasets

from tira.third_party_integrations import ensure_pyterrier_is_loaded, load_rerank_data


class TestLoadRerankData(unittest.TestCase):
    def test_loading_rerank_data_from_local_file(self):
        re_rank_data = load_rerank_data(default="tests/resources/re-ranking-outputs/")

        self.assertEqual(3, len(re_rank_data))
        self.assertEqual(
            {"qid": "1", "query": "query 1", "docno": "doc-1", "text": "Text of doc-1", "rank": 1, "score": 10},
            re_rank_data.iloc[0].to_dict(),
        )
        self.assertEqual(
            {"qid": "3", "query": "query 3", "docno": "doc-3", "text": "Text of doc-3", "rank": 1, "score": 1},
            re_rank_data.iloc[2].to_dict(),
        )

    def test_loading_rerank_data_from_remote_file_01(self):
        re_rank_data = load_rerank_data(default="workshop-on-open-web-search/re-ranking-20231027-training")

        self.assertEqual(6, len(re_rank_data))
        self.assertEqual(
            {
                "qid": "2",
                "query": "how to exit vim?",
                "docno": "doc-1",
                "text": (
                    "Press ESC key, then the : (colon), and type the wq command after the colon and hit the Enter key"
                    " to save and leave Vim."
                ),
                "rank": 1,
                "score": 10,
            },
            re_rank_data.iloc[2].to_dict(),
        )

    def test_loading_rerank_data_from_remote_file_02(self):
        re_rank_data = load_rerank_data(default="workshop-on-open-web-search/re-ranking-20231027-training")

        self.assertEqual(6, len(re_rank_data))
        self.assertEqual(
            {
                "qid": "3",
                "query": "signs heart attack",
                "docno": "doc-5",
                "text": (
                    "Common heart attack symptoms include: (1) Chest pain, (2) Pain or discomfort that spreads to the"
                    " shoulder, arm, back, neck, jaw, teeth or sometimes the upper belly, etc."
                ),
                "rank": 1,
                "score": 10,
            },
            re_rank_data.iloc[4].to_dict(),
        )

    def test_loading_of_scored_docs_from_ir_datasets(self):
        from tira.third_party_integrations import ir_datasets

        dataset = ir_datasets.load("workshop-on-open-web-search/re-ranking-20231027-training")
        actual = []

        for i in dataset.scoreddocs_iter():
            actual.append(i)

        self.assertEqual(6, len(actual))
        self.assertEqual("3", actual[4].query_id)
        self.assertEqual(10, actual[4].score)
        self.assertEqual("doc-5", actual[4].doc_id)
        self.assertEqual("signs heart attack", actual[4].query.default_text())
        self.assertEqual(
            "Common heart attack symptoms include: (1) Chest pain, (2) Pain or discomfort that spreads to the shoulder,"
            " arm, back, neck, jaw, teeth or sometimes the upper belly, etc.",
            actual[4].document.default_text(),
        )

    def test_loading_of_scored_docs_from_ir_datasets_within_tira(self):
        os.environ["TIRA_INPUT_DATASET"] = "tests/resources/re-ranking-outputs"
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        dataset = ir_datasets.load("workshop-on-open-web-search/re-ranking-20231027-training")
        print(list(dataset.scoreddocs))
        del os.environ["TIRA_INPUT_DATASET"]
        self.assertEqual(len(list(dataset.scoreddocs)), 3)
        self.assertEqual("doc-1", list(dataset.scoreddocs)[0].doc_id)
        self.assertEqual("1", list(dataset.scoreddocs)[0].query_id)
        self.assertEqual(10, list(dataset.scoreddocs)[0].score)
        self.assertEqual("Text of doc-1", list(dataset.scoreddocs)[0].document.default_text())
        self.assertEqual("query 1", list(dataset.scoreddocs)[0].query.default_text())
