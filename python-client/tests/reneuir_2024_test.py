import unittest

from approvaltests import verify_as_json

from tests.test_utils import digest_of_dataset, digest_of_run_output


class ReNeuIr2024Test(unittest.TestCase):
    """Unit tests for all use cases of the reneuir shared task at SIGIR 2024."""

    def test_dl_10_corpus_is_available(self):
        actual = digest_of_dataset("dl-top-10-docs-20240701-training")
        verify_as_json(actual)

    def test_dl_100_corpus_is_available(self):
        actual = digest_of_dataset("dl-top-100-docs-20240701-training")
        verify_as_json(actual)

    def test_dl_1000_corpus_is_available(self):
        actual = digest_of_dataset("dl-top-1000-docs-20240701-training")
        verify_as_json(actual)

    def test_dev_queries_100_corpus_is_available(self):
        actual = digest_of_dataset("ms-marco-100-queries-20240629-training")
        verify_as_json(actual)

    def test_dev_queries_1000_corpus_is_available(self):
        actual = digest_of_dataset("ms-marco-1000-queries-20240629-training")
        verify_as_json(actual)

    def test_dev_queries_all_corpus_is_available(self):
        actual = digest_of_dataset("ms-marco-all-dev-queries-20240629-training")
        verify_as_json(actual)

    def test_rerank_spot_check_is_available(self):
        actual = digest_of_dataset("re-rank-spot-check-20240624-training")
        verify_as_json(actual)

    def test_tiny_sample_is_available(self):
        actual = digest_of_dataset("tiny-sample-20231030-training")
        verify_as_json(actual)

    def test_dl_10_truth_corpus_is_available(self):
        actual = digest_of_dataset("dl-top-10-docs-20240701-training", truth=True)
        verify_as_json(actual)

    def test_dl_100_truth_corpus_is_available(self):
        actual = digest_of_dataset("dl-top-100-docs-20240701-training", truth=True)
        verify_as_json(actual)

    def test_dl_1000_truth_corpus_is_available(self):
        actual = digest_of_dataset("dl-top-1000-docs-20240701-training", truth=True)
        verify_as_json(actual)

    def test_dev_queries_100_truth_corpus_is_available(self):
        actual = digest_of_dataset("ms-marco-100-queries-20240629-training", truth=True)
        verify_as_json(actual)

    def test_dev_queries_1000_truth_corpus_is_available(self):
        actual = digest_of_dataset("ms-marco-1000-queries-20240629-training", truth=True)
        verify_as_json(actual)

    def test_dev_queries_all_truth_corpus_is_available(self):
        actual = digest_of_dataset("ms-marco-all-dev-queries-20240629-training", truth=True)
        verify_as_json(actual)

    def test_run_digest_of_bi_encoder(self):
        approaches = ["reneuir-2024/reneuir-baselines/plaid-x-retrieval", "reneuir-2024/ows/pyterrier-anceretrieval"]
        dataset_id = "dl-top-1000-docs-20240701-training"

        run_ids = {
            "reneuir-2024": {
                "reneuir-baselines": {"plaid-x-retrieval": {dataset_id: "2024-07-06-05-43-12"}},
                "ows": {"pyterrier-anceretrieval": {dataset_id: "2024-07-07-15-29-55"}},
            }
        }

        actual = {}
        for approach in approaches:
            actual[approach] = digest_of_run_output(approach, dataset_id, run_ids)

        verify_as_json(actual)

    def test_run_digest_of_cross_encoder(self):
        approaches = [
            "reneuir-2024/reneuir-baselines/llm-rankers-flan-t5-xl-top-100",
            "reneuir-2024/tira-ir-starter/MonoBERT Small (tira-ir-starter-gygaggle)",
        ]
        dataset_id = "dl-top-1000-docs-20240701-training"

        run_ids = {
            "reneuir-2024": {
                "reneuir-baselines": {"llm-rankers-flan-t5-xl-top-100": {dataset_id: "2024-07-04-05-31-10"}},
                "tira-ir-starter": {"MonoBERT Small (tira-ir-starter-gygaggle)": {dataset_id: "2024-07-07-12-53-42"}},
            }
        }

        actual = {}
        for approach in approaches:
            actual[approach] = digest_of_run_output(approach, dataset_id, run_ids)

        verify_as_json(actual)

    def test_run_digest_of_sparse_retriever(self):
        approaches = ["reneuir-2024/reneuir-baselines/pyterrier-bm25", "reneuir-2024/reneuir-baselines/anserini-bm25"]
        dataset_id = "dl-top-1000-docs-20240701-training"

        run_ids = {
            "reneuir-2024": {
                "reneuir-baselines": {
                    "pyterrier-bm25": {dataset_id: "2024-07-07-15-39-10"},
                    "anserini-bm25": {dataset_id: "2024-07-07-08-37-43"},
                },
            }
        }

        actual = {}
        for approach in approaches:
            actual[approach] = digest_of_run_output(approach, dataset_id, run_ids)

        verify_as_json(actual)

    def test_run_digest_of_indexes(self):
        approaches = [
            "reneuir-2024/reneuir-baselines/plaid-x-index",
            "reneuir-2024/reneuir-baselines/anserini-index",
            "reneuir-2024/ows/pyterrier-anceindex",
            "reneuir-2024/tira-ir-starter/Index (tira-ir-starter-pyterrier)",
        ]
        dataset_id = "dl-top-1000-docs-20240701-training"

        run_ids = {
            "reneuir-2024": {
                "reneuir-baselines": {
                    "plaid-x-index": {dataset_id: "2024-07-05-14-44-15"},
                    "anserini-index": {dataset_id: "2024-07-07-08-09-13"},
                },
                "ows": {
                    "pyterrier-anceindex": {dataset_id: "2024-07-07-13-43-04"},
                },
                "tira-ir-starter": {
                    "Index (tira-ir-starter-pyterrier)": {dataset_id: "2024-07-07-12-47-53"},
                },
            }
        }

        actual = {}
        for approach in approaches:
            actual[approach] = digest_of_run_output(approach, dataset_id, run_ids)

        verify_as_json(actual)
