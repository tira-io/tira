import unittest

import pandas as pd

from tira.third_party_integrations import persist_and_normalize_run

# .. todo:: there are no assertions in this file


class TestPersistingRunFiles(unittest.TestCase):

    def test_variant_01(self):
        run = pd.DataFrame(
            [
                {"qid": "1", "score": "1", "docno": "d1"},
                {"qid": "1", "score": "0", "docno": "d2"},
                {"qid": "1", "score": "2", "docno": "d3"},
            ]
        )
        persist_and_normalize_run(run, "system_name", default_output="/tmp/variant_01.run.txt")

    def test_variant_02(self):
        run = pd.DataFrame(
            [
                {"qid": "1", "score": "1", "docno": "d1"},
                {"qid": "1", "score": "0", "docno": "d2"},
                {"qid": "1", "score": "2", "docno": "d3"},
            ]
        )
        persist_and_normalize_run(run, "system_name", output_file="/tmp/variant_02.run.txt")

    def test_variant_03(self):
        run = pd.DataFrame(
            [
                {"qid": "1", "score": "1", "docno": "d1"},
                {"qid": "1", "score": "0", "docno": "d2"},
                {"qid": "1", "score": "2", "docno": "d3"},
            ]
        )
        persist_and_normalize_run(run, "system_name")
