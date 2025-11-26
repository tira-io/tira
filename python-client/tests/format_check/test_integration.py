import unittest
from typing import List

from tira.check_format import _fmt, check_format
from tira.rest_api_client import Client

ALL_DATASETS = {}
tira = Client()
TASKS: List[str] = [
    "wows-eval",
    # "longeval-2025",
    # ToDo: Add again
    # "advertisement-in-retrieval-augmented-generation-2025",
]
for task in TASKS:
    ALL_DATASETS.update(tira.datasets(task))

import tempfile
from pathlib import Path
from typing import Dict

from parameterized import parameterized

from ..format_check.test_check_format_for_long_eval import persist_longeval_data


def datasets_with_format(dataset_type) -> Dict:
    ret = {}
    for k, v in ALL_DATASETS.items():
        if f"{dataset_type}_format" in v:
            format_config_key = (
                "{dataset_type}_format_configuration" if dataset_type == "truth" else "format_configuration"
            )

            ret[k] = {
                f"{dataset_type}_format": v[f"{dataset_type}_format"],
                f"{dataset_type}_format_configuration": v.get(format_config_key),
            }
    return ret


MINIMAL_WOWS_POINTWISE = {
    "run": """{"id": "32d23068-7440-4891-9958-42325f98a604", "probability_relevant": 0.5}
{"id": "cde83146-ac3e-4bc5-a959-f2006ac7b8de", "probability_relevant": 0.5}
{"id": "cb7b20d0-def6-46c4-ae44-a78f00b47735", "probability_relevant": 0.5}
{"id": "4a68c86f-64ea-4293-bda5-7a0130c13864", "probability_relevant": 0.5}
{"id": "3e550de5-a104-44ae-bc3f-7ab556cc1018", "probability_relevant": 0.5}""",
    "truth": """{"id": "32d23068-7440-4891-9958-42325f98a604", "query": "who sings monk theme song", "query_id": 1051399, "unknown_doc_id": "4426187", "qrel_unknown_doc": 3}
{"id": "cde83146-ac3e-4bc5-a959-f2006ac7b8de", "query": "who sings monk theme song", "query_id": 1051399, "unknown_doc_id": "4642930", "qrel_unknown_doc": 0}
{"id": "cb7b20d0-def6-46c4-ae44-a78f00b47735", "query": "who sings monk theme song", "query_id": 1051399, "unknown_doc_id": "3108511", "qrel_unknown_doc": 1}
{"id": "4a68c86f-64ea-4293-bda5-7a0130c13864", "query": "who sings monk theme song", "query_id": 1051399, "unknown_doc_id": "5040048", "qrel_unknown_doc": 1}
{"id": "3e550de5-a104-44ae-bc3f-7ab556cc1018", "query": "who sings monk theme song", "query_id": 1051399, "unknown_doc_id": "3376628", "qrel_unknown_doc": 0}""",
}

MINIMAL_WOWS_PAIRWISE = {
    "run": """{"id": "3d080873-98a1-4388-af86-fe2c8b47ebca", "probability_relevant": 0.5}
{"id": "468a9e92-467f-47c9-810b-fe6fa9dca634", "probability_relevant": 0.5}
{"id": "846a69d0-0c0e-4d86-baf2-c3e8d31fdc86", "probability_relevant": 0.5}
{"id": "83c0e22c-b00f-4570-b1cb-027199c673d4", "probability_relevant": 0.5}
{"id": "a88a0a31-4795-4c59-830b-848de52a7fd6", "probability_relevant": 0.5}""",
    "truth": """{"id": "3d080873-98a1-4388-af86-fe2c8b47ebca", "query": "who sings monk theme song", "query_id": 1051399, "unknown_doc_id": "2378828", "qrel_unknown_doc": 2, "relevant_doc_id": "69813"}
{"id": "468a9e92-467f-47c9-810b-fe6fa9dca634", "query": "who sings monk theme song", "query_id": 1051399, "relevant_doc_id": "69813", "unknown_doc_id": "3376628", "qrel_unknown_doc": 0}
{"id": "846a69d0-0c0e-4d86-baf2-c3e8d31fdc86", "query": "who sings monk theme song", "query_id": 1051399, "relevant_doc_id": "69813", "unknown_doc_id": "5040048", "qrel_unknown_doc": 1}
{"id": "83c0e22c-b00f-4570-b1cb-027199c673d4", "query": "who sings monk theme song", "query_id": 1051399,  "relevant_doc_id": "69813", "unknown_doc_id": "4642930", "qrel_unknown_doc": 0}
{"id": "a88a0a31-4795-4c59-830b-848de52a7fd6", "query": "who sings monk theme song", "query_id": 1051399, "relevant_doc_id": "69813", "unknown_doc_id": "4426187", "qrel_unknown_doc": 3, "relevant_doc_id": "69813"}""",
}

MINIMAL_AD_CLASSIFICATION = {
    "run": """{"id": "xyz1", "label": 1, "tag": 1}
{"id": "xyz2", "label": 0, "tag": 1}
{"id": "xyz3", "label": 0, "tag": 1}""",
    "truth": """{"id": "xyz1", "label": 1, "tag": 1}
{"id": "xyz2", "label": 0, "tag": 1}
{"id": "xyz3", "label": 1, "tag": 1}""",
}

MINIMAL_AD_GENERATION = {
    "run": """{"id": "xyz1", "response": "1", "tag": "a", "topic": "a", "references": [], "advertisement": []}
{"id": "xyz2", "response": "1", "tag": "a", "topic": "a", "references": [], "advertisement": []}
{"id": "xyz3", "response": "1", "tag": "a", "topic": "a", "references": [], "advertisement": []}""",
    "truth": """{"id": "xyz1", "response": "1"}
{"id": "xyz2", "response": "1"}
{"id": "xyz3", "response": "1"}""",
}

DATASET_TO_MINIMAL_EXAMPLE = {
    "pairwise-20250309-test": MINIMAL_WOWS_PAIRWISE,
    "pairwise-smoke-test-20250210-training": MINIMAL_WOWS_PAIRWISE,
    "pointwise-20250309-test": MINIMAL_WOWS_POINTWISE,
    "pointwise-smoke-test-20250128-training": MINIMAL_WOWS_POINTWISE,
    # "ads-in-rag-task-1-generation-spot-check-20250423_1-training": MINIMAL_AD_GENERATION,
    # "ads-in-rag-task-1-generation-test-20250506-test": MINIMAL_AD_GENERATION,
    # "ads-in-rag-task-1-generation-training-20250423-training": MINIMAL_AD_GENERATION,
    # "ads-in-rag-task-2-classification-spot-check-20250423-training": MINIMAL_AD_CLASSIFICATION,
    # "ads-in-rag-task-2-classification-test-20250428-test": MINIMAL_AD_CLASSIFICATION,
    # "ads-in-rag-task-2-classification-training-20250423-training": MINIMAL_AD_CLASSIFICATION,
    # "sci-spot-check-no-prior-data-20250322-training": {"run": persist_longeval_data(["2024-10"]), "truth": "skip"},
    # "sci-spot-check-with-prior-data-20250322-training": {"run": persist_longeval_data(["2024-11"]), "truth": "skip"},
    "web-20250430-test": {
        "run": persist_longeval_data(["2023-03", "2023-04", "2023-05", "2023-06", "2023-07", "2023-08"]),
        "truth": "skip",
    },
    "sci-20250430-test": {"run": persist_longeval_data(["2024-11", "2025-01"]), "truth": "skip"},
}


class TestIntegration(unittest.TestCase):
    @unittest.skip("ToDo")
    def test_datasets_with_run_format(self):
        expected = DATASET_TO_MINIMAL_EXAMPLE.keys()
        actual = datasets_with_format("run").keys()
        self.assertEqual(expected, actual)

    @unittest.skip("ToDo")
    def test_datasets_with_truth_format(self):
        expected = DATASET_TO_MINIMAL_EXAMPLE.keys()
        actual = datasets_with_format("truth").keys()
        self.assertEqual(expected, actual)

    @parameterized.expand(datasets_with_format("truth").items())
    def test_truth_datasets_are_valid(self, k, v):
        TYPE = "truth"
        if k not in DATASET_TO_MINIMAL_EXAMPLE:
            return
        val = DATASET_TO_MINIMAL_EXAMPLE[k][TYPE]
        if val == "skip":
            return

        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "labels.jsonl").write_text(val)
            actual = check_format(Path(d), v[f"{TYPE}_format"], v[f"{TYPE}_format_configuration"])
            self.assertEqual(_fmt.OK, actual[0], f"Problem in {k}: {actual[1]}")

    @parameterized.expand(datasets_with_format("run").items())
    def test_run_datasets_are_valid(self, k, v):
        TYPE = "run"
        if k not in DATASET_TO_MINIMAL_EXAMPLE:
            return
        if isinstance(DATASET_TO_MINIMAL_EXAMPLE[k][TYPE], Path):
            print(v[f"{TYPE}_format"])
            print(v[f"{TYPE}_format_configuration"])
            actual = check_format(
                Path(DATASET_TO_MINIMAL_EXAMPLE[k][TYPE]), v[f"{TYPE}_format"], v[f"{TYPE}_format_configuration"]
            )
        else:
            with tempfile.TemporaryDirectory() as d:
                (Path(d) / "labels.jsonl").write_text(DATASET_TO_MINIMAL_EXAMPLE[k][TYPE])
                actual = check_format(Path(d), v[f"{TYPE}_format"], v[f"{TYPE}_format_configuration"])
        self.assertEqual(_fmt.OK, actual[0], f"Problem in {k}: {actual[1]}")
