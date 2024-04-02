from tira.rest_api_client import Client
from tira.third_party_integrations import ensure_pyterrier_is_loaded
import os
import unittest

def get_input_run_mounts(input_run, approach_identifier):
    os.environ['TIRA_INPUT_RUN'] = input_run
    actual_dir = Client().input_run_in_sandbox(approach_identifier)
    del os.environ['TIRA_INPUT_RUN']
    actual_files = []
    try:
        actual_files = set(os.listdir(actual_dir))
    except:
        pass

    return actual_dir, actual_files

def get_pt_index_in_sandbox(input_run, approach_identifier):
    ensure_pyterrier_is_loaded()
    os.environ['TIRA_INPUT_RUN'] = input_run

    try:
        ret = Client().pt.index(approach_identifier, 'dataset_id')
        del os.environ['TIRA_INPUT_RUN']
        return ret
    except:
        del os.environ['TIRA_INPUT_RUN']
        return None

class InputRunMountTest(unittest.TestCase):
    def test_for_single_input_run_with_four_files(self):
        expected_dir = 'tests/resources/sample-input-full-rank'
        expected_files = set(['documents.jsonl', 'metadata.json', 'queries.jsonl', 'queries.xml'])

        actual_dir, actual_files = get_input_run_mounts('tests/resources/sample-input-full-rank', 'approach-identifier')
        
        self.assertEqual(expected_dir, actual_dir)
        self.assertEqual(expected_files, actual_files)

    def test_for_single_input_run_with_single_file(self):
        expected_dir = 'tests/resources/re-ranking-outputs/'
        expected_files = set(['rerank.jsonl.gz'])

        actual_dir, actual_files = get_input_run_mounts('tests/resources/re-ranking-outputs/', 'some-identifier')
        
        self.assertEqual(expected_dir, actual_dir)
        self.assertEqual(expected_files, actual_files)

    def test_for_multi_input_runs_01(self):
        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-01/', 'some-identifier')
        self.assertEqual('tests/resources/input-run-01//1', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-01/', 'some-identifier')
        self.assertEqual('tests/resources/input-run-01//1', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-01/', 'other-approach-identifier')
        self.assertEqual('tests/resources/input-run-01//2', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-01/', 'some-identifier')
        self.assertEqual('tests/resources/input-run-01//1', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-01/', 'other-approach-identifier')
        self.assertEqual('tests/resources/input-run-01//2', actual_dir)

    def test_for_multi_input_runs_02(self):
        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-02/', 'a')
        self.assertEqual('tests/resources/input-run-02//1', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-02/', 'b')
        self.assertEqual('tests/resources/input-run-02//2', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-02/', 'c')
        self.assertEqual('tests/resources/input-run-02//3', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-02/', 'a')
        self.assertEqual('tests/resources/input-run-02//1', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-02/', 'b')
        self.assertEqual('tests/resources/input-run-02//2', actual_dir)

        actual_dir, _ = get_input_run_mounts('tests/resources/input-run-02/', 'c')
        self.assertEqual('tests/resources/input-run-02//3', actual_dir)

    def test_for_index_that_does_not_exist(self):
        index = get_pt_index_in_sandbox('tests/resources/input-run-02/', 'a')
        self.assertIsNone(index)

    def test_for_index_that_does_exist_with_multi_inputs(self):
        index = get_pt_index_in_sandbox('tests/resources/input-run-02/', 'a')
        self.assertIsNone(index)

        index = get_pt_index_in_sandbox('tests/resources/input-run-02/', 'b')
        self.assertIsNotNone(index)

    def test_for_index_that_does_exist_with_single_input(self):
        index = get_pt_index_in_sandbox('tests/resources/input-run-02/2', 'a')
        self.assertIsNotNone(index)

    def test_for_index_that_does_not_exist_with_single_input(self):
        index = get_pt_index_in_sandbox('tests/resources/input-run-02/1', 'a')
        self.assertIsNone(index)