#!/usr/bin/env python3

from glob import glob
from os.path import exists
import os
import shutil
from pathlib import Path
from django.conf import settings
import json
import sys

def find_job_to_execute():
     ret = list(glob('*/*/*/job-to-execute.txt'))
     return None if len(ret) == 0 else ret[0]

def config(job_file):
    ret = {}
    with open(job_file, 'r') as f:
        for l in f:
            l = l.split('=')
            if len(l) == 2:
                ret[l[0].strip()] = l[1].strip()
    
    return ret


def copy_from_to(source_directory, target_directory)
    if exists(source_directory) and not exists(target_directory):
        print(f'Copy input data from {source_directory} to {target_directory}', file=sys.stderr)
        shutil.copytree(source_directory, os.path.abspath(Path(target_directory)))
    else:
        print(f'Absolute input dataset {source_directory} exists: {exists(source_directory)}', file=sys.stderr)
        print(f'Relative input dataset {target_directory} exists: {exists(target_directory)}', file=sys.stderr)
    
    if not exists(target_directory):
        print(f'Make target-directory: "{target_directory}"', file=sys.stderr)
        Path(target_directory).mkdir(parents=True, exist_ok=True)


def identify_environment_variables(job_file):
    if job_file is None or not exists(job_file) or not Path(job_file).is_file():
        return ['TIRA_IMAGE_TO_EXECUTE=ubuntu:16.04']
    
    job_dir = job_file.split('/job-to-execute')[0]
    
    tira_dataset_id = job_dir.split('/')[-3]
    tira_vm_id = job_dir.split('/')[-2]
    tira_run_id = job_dir.split('/')[-1]
    job_configuration = config(job_file)

    input_dataset = job_configuration['TIRA_DATASET_TYPE'] + '-datasets/' + job_configuration['TIRA_TASK_ID'] + '/' + tira_dataset_id + '/'
    absolute_input_dataset = '/mnt/ceph/tira/data/datasets/' + input_dataset
    input_dataset_truth = '/mnt/ceph/tira/data/datasets/' + job_configuration['TIRA_DATASET_TYPE'] + '-datasets-truth/' + job_configuration['TIRA_TASK_ID'] + '/' + tira_dataset_id + '/'
    
    ret = [
        'TIRA_INPUT_RUN=' + absolute_input_dataset,
        'TIRA_DATASET_ID=' + tira_dataset_id,
        'TIRA_INPUT_DATASET=' + input_dataset,
        'inputDataset=' + input_dataset,
        'outputDir=' + job_dir + '/output',
        'TIRA_EVALUATION_GROUND_TRUTH=' + input_dataset_truth,
        'TIRA_VM_ID=' + tira_vm_id,
        'TIRA_RUN_ID=' + tira_run_id,
        'TIRA_OUTPUT_DIR=' + job_dir + '/output',
        'TIRA_JOB_FILE=' + job_file,
    ]
    
    if 'TIRA_INPUT_RUN_DATASET_ID' in job_configuration and 'TIRA_INPUT_RUN_VM_ID' in job_configuration and 'TIRA_INPUT_RUN_RUN_ID' in job_configuration:
        local_input_run_directory = os.environ['TIRA_INPUT_RUN_DATASET_ID'] / os.environ['TIRA_INPUT_RUN_VM_ID'] / os.environ['TIRA_INPUT_RUN_RUN_ID'] / 'output'
        absolute_input_run_directory = settings.TIRA_ROOT / 'data' / 'runs' / local_input_run_directory
        absolute_input_run_directory = os.path.abspath(absolute_input_run_directory)
        local_input_run_directory = os.path.abspath(local_input_run_directory)
        
        print(f'The software uses an input run. I will copy data from {absolute_input_run_directory} to {local_input_run_directory}', file=sys.stderr)
        copy_from_to(absolute_input_run_directory, local_input_run_directory)
        
        ret += [
            'inputRun=' + local_input_run_directory,
        ]
    
    with open(job_file, 'r') as f:
        for l in f:
            if '=' in l:
                ret += [l.strip()]
    
    for i in ['TIRA_TASK_ID', 'TIRA_IMAGE_TO_EXECUTE', 'TIRA_COMMAND_TO_EXECUTE']:
        if len([j for j in ret if i in j]) != 1:
            raise ValueError('I expected the variable "' + i + '" to be defined by the job, but it is missing.')

    copy_from_to(absolute_input_dataset, input_dataset)
    
    json.dump({'keep': True}, open(input_dataset + '/.keep', 'w'))
    
    return ret

if __name__ == '__main__':
    job_to_execute = find_job_to_execute()
    for i in identify_environment_variables(job_to_execute):
        print(i.strip())

