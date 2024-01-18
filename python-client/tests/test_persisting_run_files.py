from tira.third_party_integrations import persist_and_normalize_run
import pandas as pd
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from math import nan

# .. todo:: there are no assertions in this file

class TestPersistingRunFiles(unittest.TestCase):

    def test_variant_01(self):
        run = pd.DataFrame([{"qid": "1", "score": "1", "docno": "d1"},  {"qid": "1", "score": "0", "docno": "d2"},  {"qid": "1", "score": "2", "docno": "d3"}])
        persist_and_normalize_run(run, 'system_name', default_output='/tmp/variant_01.run.txt')
        
    def test_variant_02(self):
        run = pd.DataFrame([{"qid": "1", "score": "1", "docno": "d1"},  {"qid": "1", "score": "0", "docno": "d2"},  {"qid": "1", "score": "2", "docno": "d3"}])
        persist_and_normalize_run(run, 'system_name', output_file='/tmp/variant_02.run.txt')

    def test_variant_03(self):
        run = pd.DataFrame([{"qid": "1", "score": "1", "docno": "d1"},  {"qid": "1", "score": "0", "docno": "d2"},  {"qid": "1", "score": "2", "docno": "d3"}])
        persist_and_normalize_run(run, 'system_name')

    def test_none_score(self):
        run = pd.DataFrame([
            {"qid": "1", "score": "1", "docno": "d1"},
            {"qid": "1", "score": "0", "docno": "d2"},
            {"qid": "1", "score": None, "docno": "d3"},
        ])
        with TemporaryDirectory() as tmp_dir:
            run_file_path = Path(tmp_dir) / "run.txt"

            persist_and_normalize_run(
                run, 'system_name', output_file=str(run_file_path))
            
            with run_file_path.open("rt") as run_file:
                for i, line in enumerate(run_file):
                    assert len(line.split()) == 6, f"Line {i} does not have exactly 6 columns."

    def test_nan_score(self):
        run = pd.DataFrame([
            {"qid": "1", "score": "1", "docno": "d1"},
            {"qid": "1", "score": "0", "docno": "d2"},
            {"qid": "1", "score": nan, "docno": "d3"},
        ])
        with TemporaryDirectory() as tmp_dir:
            run_file_path = Path(tmp_dir) / "run.txt"

            persist_and_normalize_run(
                run, 'system_name', output_file=str(run_file_path))
            
            with run_file_path.open("rt") as run_file:
                for i, line in enumerate(run_file):
                    assert len(line.split()) == 6, f"Line {i} does not have exactly 6 columns."
