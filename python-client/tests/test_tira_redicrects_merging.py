import unittest

from tira.tira_redirects import STATIC_REDIRECTS, TASKS_WITH_REDIRECT_MERGING, TIRA_ZENODO_BASE_URL


class TestTiraRedirectsMerging(unittest.TestCase):
    def test_with_maually_created_entry(self):
        expected = {
            "urls": [
                "https://zenodo.org/records/10743990/files/2023-01-07-22-09-56.zip?download=1",
                f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-07-22-09-56.zip",
            ],
            "run_id": "2023-01-07-22-09-56",
        }
        actual = STATIC_REDIRECTS["ir-benchmarks"]["tira-ir-starter"]["Index (tira-ir-starter-pyterrier)"][
            "msmarco-passage-trec-dl-2019-judged-20230107-training"
        ]

        self.assertEqual(expected, actual)

    def test_with_automatically_added_reneuir_entry_with_class(self):
        expected = {
            "urls": [f"{TIRA_ZENODO_BASE_URL}/reneuir-2024/runs/bi-encoder-retriever.zip?download=1"],
            "run_id": "2024-07-06-05-43-12",
        }
        actual = STATIC_REDIRECTS["reneuir-2024"]["reneuir-baselines"]["plaid-x-retrieval"][
            "dl-top-1000-docs-20240701-training"
        ]

        self.assertEqual(expected, actual)

    def test_with_automatically_added_reneuir_entry_without_class_01(self):
        expected = {
            "urls": [f"{TIRA_ZENODO_BASE_URL}/reneuir-2024/runs/ows-pyterrier-anceindex.zip?download=1"],
            "run_id": "2024-07-07-14-05-38",
        }
        actual = STATIC_REDIRECTS["reneuir-2024"]["ows"]["pyterrier-anceindex"]["dl-top-10-docs-20240701-training"]

        self.assertEqual(expected, actual)

    def test_with_automatically_added_reneuir_entry_without_class_02(self):
        expected = {
            "urls": [
                f"{TIRA_ZENODO_BASE_URL}/reneuir-2024/runs/tira-ir-starter-index-tira-ir-starter-pyterrier.zip?"
                "download=1"
            ],
            "run_id": "2024-07-07-13-27-26",
        }
        actual = STATIC_REDIRECTS["reneuir-2024"]["tira-ir-starter"]["Index (tira-ir-starter-pyterrier)"][
            "ms-marco-100-queries-20240629-training"
        ]

        self.assertEqual(expected, actual)

    def test_tasks_with_redirect_merging(self):
        expected = ["ir-benchmarks", "ir-lab-sose-2024", "reneuir-2024"]

        actual = sorted(list(TASKS_WITH_REDIRECT_MERGING))

        self.assertEqual(expected, actual)
