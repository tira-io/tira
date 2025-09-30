import unittest
from pathlib import Path

from tira.tira_client import TiraClient

RESOURCE_DIR = Path(__file__).parent / "resources"


def submit_task(directory, dataset="train"):
    client = TiraClient()
    return client.submit_dataset(directory, "task", dataset, True, skip_baseline=True)


class TestTaskSubmissions(unittest.TestCase):
    def test_fails_for_non_existing_directory(self):
        actual = submit_task(RESOURCE_DIR / "does-not-exist")
        self.assertIsNone(actual)

    def test_works_for_valid_directory(self):
        actual = submit_task(RESOURCE_DIR / "example-datasets" / "multi-author-analysis")
        self.assertIsNotNone(actual)

    def test_fails_for_non_existing_dataset(self):
        actual = submit_task(RESOURCE_DIR / "example-datasets" / "multi-author-analysis", "does-not-exist")
        self.assertIsNone(actual)

    def test_works_for_lsr_benchmark(self):
        actual = submit_task(RESOURCE_DIR / "example-datasets" / "learned-sparse-retrieval")
        self.assertIsNotNone(actual)
