import unittest
from tests.test_utils import digest_of_dataset, digest_of_run_output
from approvaltests import verify_as_json

class ReNeuIr2024Test(unittest.TestCase):
    """Unit tests for all use cases of the reneuir shared task at SIGIR 2024.
    """
    def test_dl_10_corpus_is_available(self):
        actual = digest_of_dataset('dl-top-10-docs-20240701-training')
        verify_as_json(actual)

    def test_dl_100_corpus_is_available(self):
        actual = digest_of_dataset('dl-top-100-docs-20240701-training')
        verify_as_json(actual)

    def test_dl_1000_corpus_is_available(self):
        actual = digest_of_dataset('dl-top-1000-docs-20240701-training')
        verify_as_json(actual)

    def test_dev_queries_100_corpus_is_available(self):
        actual = digest_of_dataset('ms-marco-100-queries-20240629-training')
        verify_as_json(actual)

    def test_dev_queries_1000_corpus_is_available(self):
        actual = digest_of_dataset('ms-marco-1000-queries-20240629-training')
        verify_as_json(actual)

    def test_dev_queries_all_corpus_is_available(self):
        actual = digest_of_dataset('ms-marco-all-dev-queries-20240629-training')
        verify_as_json(actual)

    def test_rerank_spot_check_is_available(self):
        actual = digest_of_dataset('re-rank-spot-check-20240624-training')
        verify_as_json(actual)

    def test_tiny_sample_is_available(self):
        actual = digest_of_dataset('tiny-sample-20231030-training')
        verify_as_json(actual)

    def test_dl_10_truth_corpus_is_available(self):
        actual = digest_of_dataset('dl-top-10-docs-20240701-training', truth=True)
        verify_as_json(actual)

    def test_dl_100_truth_corpus_is_available(self):
        actual = digest_of_dataset('dl-top-100-docs-20240701-training', truth=True)
        verify_as_json(actual)

    def test_dl_1000_truth_corpus_is_available(self):
        actual = digest_of_dataset('dl-top-1000-docs-20240701-training', truth=True)
        verify_as_json(actual)

    def test_dev_queries_100_truth_corpus_is_available(self):
        actual = digest_of_dataset('ms-marco-100-queries-20240629-training', truth=True)
        verify_as_json(actual)

    def test_dev_queries_1000_truth_corpus_is_available(self):
        actual = digest_of_dataset('ms-marco-1000-queries-20240629-training', truth=True)
        verify_as_json(actual)

    def test_dev_queries_all_truth_corpus_is_available(self):
        actual = digest_of_dataset('ms-marco-all-dev-queries-20240629-training', truth=True)
        verify_as_json(actual)