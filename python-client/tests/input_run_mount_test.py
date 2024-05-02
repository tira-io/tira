from tira.rest_api_client import Client
from tira.third_party_integrations import ensure_pyterrier_is_loaded
import os
import unittest

def get_input_run_mounts(input_run, approach_identifier):
    os.environ['inputRun'] = input_run
    actual_dir = Client().input_run_in_sandbox(approach_identifier)
    del os.environ['inputRun']
    actual_files = []
    try:
        actual_files = set(os.listdir(actual_dir))
    except:
        pass

    return actual_dir, actual_files

def tira_cli_download_run_output(input_run, approach_identifier):
    os.environ['inputRun'] = input_run
    actual_dir = Client().get_run_output(approach_identifier, 'dataset')
    del os.environ['inputRun']
    actual_files = []
    try:
        actual_files = set(os.listdir(actual_dir))
    except:
        pass

    return actual_dir, actual_files

def tira_cli_download_dataset(dataset_path):
    os.environ['TIRA_INPUT_DATASET'] = dataset_path
    actual_dir = Client().download_dataset(None, 'dataset')
    del os.environ['TIRA_INPUT_DATASET']
    actual_files = []
    try:
        actual_files = set(os.listdir(actual_dir))
    except:
        pass

    return actual_dir, actual_files

def get_pt_index_in_sandbox(input_run, approach_identifier):
    ensure_pyterrier_is_loaded()
    os.environ['inputRun'] = input_run

    try:
        ret = Client().pt.index(approach_identifier, 'dataset_id')
        del os.environ['inputRun']
        return ret
    except:
        del os.environ['inputRun']
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

    def test_cli_download_run_output_01(self):
        expected_dir = 'tests/resources/re-ranking-outputs/'
        expected_files = set(['rerank.jsonl.gz'])
    
        actual_dir, actual_files = tira_cli_download_run_output('tests/resources/re-ranking-outputs/', 'a')

        self.assertEqual(expected_dir, actual_dir)
        self.assertEqual(expected_files, actual_files)

    def test_cli_download_run_output_02(self):
        expected_dir = 'tests/resources/input-run-02//2'
        expected_files = set(['.gitkeep', 'index'])
    
        tira_cli_download_run_output('tests/resources/input-run-02/', 'a')
        actual_dir, actual_files = tira_cli_download_run_output('tests/resources/input-run-02/', 'b')

        self.assertEqual(expected_dir, actual_dir)
        self.assertEqual(expected_files, actual_files)

    def test_cli_download_dataset_01(self):
        expected_dir = 'tests/resources/re-ranking-outputs/'
        expected_files = set(['rerank.jsonl.gz'])
    
        actual_dir, actual_files = tira_cli_download_dataset('tests/resources/re-ranking-outputs/')

        self.assertEqual(expected_dir, actual_dir)
        self.assertEqual(expected_files, actual_files)

    def test_cli_download_dataset_02(self):
        expected_dir = 'tests/resources/input-run-02//2'
        expected_files = set(['index', '.gitkeep'])
    
        actual_dir, actual_files = tira_cli_download_dataset('tests/resources/input-run-02//2')

        self.assertEqual(expected_dir, actual_dir)
        self.assertEqual(expected_files, actual_files)
