import json
import os
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pandas as pd

from tira.ir_datasets_loader import IrDatasetsLoader, get_as_re_rank_input
from tira.ir_datasets_util import TirexQuery

EXAMPLE_RANKING_01 = """
1 Q0 12 1 10 tag
1 Q0 15 2 9 tag
1 Q0 16 3 6 tag
2 Q0 3 1 1 tag
4 Q0 4 1 10 tag
"""


class TestIrDatasetsLoader(unittest.TestCase):
    def test_map_query_preserves_raw_original_query(self):
        original_query = {
            "language": "en",
            "description": "A description",
            "custom": {"values": [1, 2]},
        }
        query = TirexQuery(
            query_id="1",
            text="query text",
            title="query text",
            query="query text",
            description="A description",
            narrative=None,
            original_query=original_query,
        )

        actual = json.loads(IrDatasetsLoader().map_query_as_jsonl(query))

        self.assertEqual(original_query, actual["original_query"])
        self.assertNotIn("original_query", actual["original_query"])

    def test_map_query_without_raw_original_query_uses_query_fields(self):
        query = TirexQuery(
            query_id="1",
            text="query text",
            title="query text",
            query="query text",
            description="A description",
            narrative=None,
        )

        actual = json.loads(IrDatasetsLoader().map_query_as_jsonl(query))

        self.assertEqual("1", actual["original_query"]["query_id"])
        self.assertEqual("A description", actual["original_query"]["description"])
        self.assertNotIn("original_query", actual["original_query"])

    def test_loading_of_re_rank_file_depth_10(self):
        expected_path = "-inputs/83051700dcfaf0babc8fa5724dfc5c51/10"
        with TemporaryDirectory() as cache, NamedTemporaryFile() as ranking:
            os.environ["TIRA_CACHE_DIR"] = str(cache)
            ranking = Path(str(ranking.name))
            ranking.write_text(EXAMPLE_RANKING_01)
            actual = get_as_re_rank_input(ranking, 10, "cranfield")

            self.assertIn(str(cache), str(actual))
            self.assertIn(expected_path, str(actual))
            self.assertTrue(str(actual).endswith(expected_path + "/input-data"))
            self.assertTrue((actual / "rerank.jsonl.gz").is_file())
            actual_lines = pd.read_json(actual / "rerank.jsonl.gz", lines=True)
            self.assertEqual(5, len(actual_lines))
            self.assertIn("qid", actual_lines.iloc[0].to_dict())
            self.assertIn("query", actual_lines.iloc[0].to_dict())
            self.assertIn("text", actual_lines.iloc[0].to_dict())

        del os.environ["TIRA_CACHE_DIR"]

    def test_loading_of_re_rank_file_depth_3(self):
        expected_path = "-inputs/83051700dcfaf0babc8fa5724dfc5c51/3"
        with TemporaryDirectory() as cache, NamedTemporaryFile() as ranking:
            os.environ["TIRA_CACHE_DIR"] = str(cache)
            ranking = Path(str(ranking.name))
            ranking.write_text(EXAMPLE_RANKING_01)
            actual = get_as_re_rank_input(ranking, 3, "cranfield")

            self.assertIn(str(cache), str(actual))
            self.assertIn(expected_path, str(actual))
            self.assertTrue(str(actual).endswith(expected_path + "/input-data"))
            self.assertTrue((actual / "rerank.jsonl.gz").is_file())
            actual_lines = pd.read_json(actual / "rerank.jsonl.gz", lines=True)
            self.assertEqual(5, len(actual_lines))
            self.assertIn("qid", actual_lines.iloc[0].to_dict())
            self.assertIn("query", actual_lines.iloc[0].to_dict())
            self.assertIn("text", actual_lines.iloc[0].to_dict())

        del os.environ["TIRA_CACHE_DIR"]

    def test_loading_of_re_rank_file_depth_1(self):
        expected_path = "-inputs/83051700dcfaf0babc8fa5724dfc5c51/1"
        with TemporaryDirectory() as cache, NamedTemporaryFile() as ranking:
            os.environ["TIRA_CACHE_DIR"] = str(cache)
            ranking = Path(str(ranking.name))
            ranking.write_text(EXAMPLE_RANKING_01)
            actual = get_as_re_rank_input(ranking, 1, "cranfield")

            self.assertIn(str(cache), str(actual))
            self.assertIn(expected_path, str(actual))
            self.assertTrue(str(actual).endswith(expected_path + "/input-data"))
            self.assertTrue((actual / "rerank.jsonl.gz").is_file())
            actual_lines = pd.read_json(actual / "rerank.jsonl.gz", lines=True)
            self.assertEqual(3, len(actual_lines))
            self.assertIn("qid", actual_lines.iloc[0].to_dict())
            self.assertIn("query", actual_lines.iloc[0].to_dict())
            self.assertIn("text", actual_lines.iloc[0].to_dict())

        del os.environ["TIRA_CACHE_DIR"]
