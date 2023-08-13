import importlib
import os
import json
from pathlib import Path
from django.conf import settings
import shutil
import json


BASE_DIR = '/tmp/test-in-progress/'
os.makedirs(BASE_DIR)

settings.TIRA_ROOT = Path('/tmp') / 'test-in-progress' / 'tira-root'
copy_multiple_input_runs_to_local_environment = importlib.import_module("tira-specify-task-to-run").copy_multiple_input_runs_to_local_environment


def load_job_output(dataset, num):
    try:
        return json.load(open(f'{dataset}/merged-input-run/pseudo-run-id/output/{num}/data.json', 'r'))
    except:
        return None


def create_job_output(dataset_id, vm_id, run_id):
    output_dir = f'{BASE_DIR}/tira-root/data/runs/{dataset_id}/{vm_id}/{run_id}/output/'
    os.makedirs(output_dir)

    with open(f'{output_dir}/data.json', 'w') as f:
        f.write(json.dumps({'dataset_id': dataset_id, 'vm_id': vm_id, 'run_id': run_id}))


create_job_output('dataset-1', 'vm-1', 'run-1')
create_job_output('dataset-2', 'vm-1', 'run-1')
create_job_output('dataset-2', 'vm-1', 'run-3')
create_job_output('dataset-1', 'vm-2', 'run-2')
create_job_output('dataset-2', 'vm-2', 'run-2')
create_job_output('dataset-2', 'vm-2', 'run-4')


def test_empty_set_returned_for_empty_job_config():
    job_config = {}
    actual = copy_multiple_input_runs_to_local_environment(job_config)
    
    assert not actual


def test_empty_set_returned_for_none_job_config():
    job_config = None
    actual = copy_multiple_input_runs_to_local_environment(job_config)
    
    assert not actual


def test_multiple_copies_of_same_job():
    job_config = {
        'TIRA_INPUT_RUN_DATASET_IDS': '["dataset-1", "dataset-1"]',
        'TIRA_INPUT_RUN_VM_IDS': '["vm-1", "vm-1"]',
        'TIRA_INPUT_RUN_RUN_IDS': '["run-1", "run-1"]',
    }
    expected = {
        'file_skip_list': ['documents.jsonl'],
        'ret': ['inputRun=dataset-1/merged-input-run/pseudo-run-id/output'],
        'tira_cleanup_command': ';rm -Rf dataset-1/merged-input-run/pseudo-run-id/output'
    }
    actual = copy_multiple_input_runs_to_local_environment(job_config)
    
    assert actual == expected
    assert load_job_output('dataset-1', 1) == {'dataset_id': 'dataset-1', 'vm_id': 'vm-1', 'run_id': 'run-1'}
    assert load_job_output('dataset-1', 2) == {'dataset_id': 'dataset-1', 'vm_id': 'vm-1', 'run_id': 'run-1'}
    assert not load_job_output('dataset-1', 3)
    assert not load_job_output('dataset-1', 4)
    shutil.rmtree('dataset-1')

def test_multiple_copies_of_same_job_variant2():
    job_config = {
        'TIRA_INPUT_RUN_DATASET_IDS': '["dataset-2", "dataset-2", "dataset-2"]',
        'TIRA_INPUT_RUN_VM_IDS': '["vm-1", "vm-2", "vm-1"]',
        'TIRA_INPUT_RUN_RUN_IDS': '["run-3", "run-4", "run-1"]',
    }
    expected = {
        'file_skip_list': ['documents.jsonl'],
        'ret': ['inputRun=dataset-2/merged-input-run/pseudo-run-id/output'],
        'tira_cleanup_command': ';rm -Rf dataset-2/merged-input-run/pseudo-run-id/output'
    }
    actual = copy_multiple_input_runs_to_local_environment(job_config)
    
    assert actual == expected
    assert load_job_output('dataset-2', 1) == {'dataset_id': 'dataset-2', 'vm_id': 'vm-1', 'run_id': 'run-3'}
    assert load_job_output('dataset-2', 2) == {'dataset_id': 'dataset-2', 'vm_id': 'vm-2', 'run_id': 'run-4'}
    assert load_job_output('dataset-2', 3) == {'dataset_id': 'dataset-2', 'vm_id': 'vm-1', 'run_id': 'run-1'}
    assert not load_job_output('dataset-2', 4)
    assert not load_job_output('dataset-2', 5)
    shutil.rmtree('dataset-2')

