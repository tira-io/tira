#!/usr/bin/env python3

from datetime import datetime as dt
from pathlib import Path
from os.path import exists
import json
import os
from django.conf import settings
import shutil
from tira.git_integration.gitlab_integration import persist_tira_metadata_for_job

def fail_if_environment_variables_are_missing():
    for v in ['TIRA_DATASET_ID', 'TIRA_VM_ID', 'TIRA_RUN_ID', 'TIRA_OUTPUT_DIR', 'TIRA_TASK_ID']:
        if v not in os.environ:
            raise ValueError('I expect that the environment variable "' + v + '" is set, but it was absent.')

def run_output_dir():
    return settings.TIRA_ROOT / 'data' / 'runs' / os.environ['TIRA_DATASET_ID'] / os.environ['TIRA_VM_ID'] / os.environ['TIRA_RUN_ID'] / 'output'

def eval_dir(eval_id):
    return Path(os.environ['TIRA_OUTPUT_DIR']) / '..' / '..' / eval_id
    
def final_eval_dir(eval_id):
    return settings.TIRA_ROOT / 'data' / 'runs' / os.environ['TIRA_DATASET_ID'] / os.environ['TIRA_VM_ID'] / eval_id

def copy_resources():
    if exists(str(run_output_dir())):
        print(str(run_output_dir()) + " exists already. I do not overwrite.")
        return

    src = str(os.environ['TIRA_OUTPUT_DIR'])
    target = run_output_dir()
    target_without_output = str(os.path.abspath(target / '..'))
    
    if not exists(src):
        print(f'Make src-directory: "{src}"')
        Path(src).mkdir(parents=True, exist_ok=True)
    
    print(f'Make target directory: "{target_without_output}"')
    Path(target_without_output).mkdir(parents=True, exist_ok=True)
    
    print('The output dir exists: ' + str(exists(str(run_output_dir()))))
    
    shutil.copytree(src, str(target))
    persist_tira_metadata_for_job(target_without_output, os.environ['TIRA_RUN_ID'], 'run-user-software')

def config(job_file):
    ret = {}
    with open(job_file, 'r') as f:
        for l in f:
            l = l.split('=')
            if len(l) == 2:
                ret[l[0].strip()] = l[1].strip()
    
    return ret

def extract_evaluation_commands():
    if 'TIRA_JOB_FILE' in os.environ:
        c = config(os.environ['TIRA_JOB_FILE'])
        return {'TIRA_EVALUATION_IMAGE_TO_EXECUTE': c['TIRA_EVALUATION_IMAGE_TO_EXECUTE'], 'TIRA_EVALUATION_COMMAND_TO_EXECUTE': c['TIRA_EVALUATION_COMMAND_TO_EXECUTE'], 'TIRA_EVALUATION_SOFTWARE_ID': os.environ['TIRA_EVALUATION_SOFTWARE_ID']}
        
    if 'TIRA_EVALUATION_COMMAND_TO_EXECUTE' in os.environ and 'TIRA_EVALUATOR_TRANSACTION_ID' in os.environ and 'TIRA_EVALUATION_IMAGE_TO_EXECUTE' in os.environ:
        return {'TIRA_EVALUATION_IMAGE_TO_EXECUTE': os.environ['TIRA_EVALUATION_IMAGE_TO_EXECUTE'], 'TIRA_EVALUATION_COMMAND_TO_EXECUTE': os.environ['TIRA_EVALUATION_COMMAND_TO_EXECUTE'], 'TIRA_EVALUATION_SOFTWARE_ID': os.environ['TIRA_EVALUATION_SOFTWARE_ID']}

    return {'TIRA_EVALUATION_IMAGE_TO_EXECUTE': 'ubuntu:16.04', 'TIRA_EVALUATION_COMMAND_TO_EXECUTE': 'echo "No evaluation specified..."', 'TIRA_EVALUATION_SOFTWARE_ID': '-1'}

def copy_to_local(absolute_src, relative_target):
    if exists(absolute_src) and not exists(relative_target):
        print(f'Copy ground data from {absolute_src} to {os.path.abspath(Path(relative_target))}')
        shutil.copytree(absolute_src, os.path.abspath(Path(relative_target)))
    
    if not exists(relative_target):
        print(f'Make empty ground directory: "{relative_target}"')
        Path(relative_target).mkdir(parents=True, exist_ok=True)
    
    json.dump({'keep': True}, open(relative_target + '/.keep', 'w'))

def identify_environment_variables():
    eval_id = dt.now().strftime('%Y-%m-%d-%H-%M-%S')
    ret = set()
    for (k,v) in os.environ.items() :
        if k.lower().startswith('tira') and k.upper() not in ['TIRA_EVALUATION_INPUT_DIR', 'TIRA_EVALUATION_OUTPUT_DIR', 'TIRA_FINAL_EVALUATION_OUTPUT_DIR', 'TIRA_EVALUATION_IMAGE_TO_EXECUTE', 'TIRA_EVALUATION_COMMAND_TO_EXECUTE', 'TIRA_EVALUATION_SOFTWARE_ID']:
            ret.add((k + '=' + v).strip())

    absolute_input_dataset = os.environ['TIRA_EVALUATION_GROUND_TRUTH']
    input_dataset = absolute_input_dataset.split('/mnt/ceph/tira/data/datasets/')[1]
    copy_to_local(absolute_input_dataset, input_dataset)
    copy_to_local(str(run_output_dir()), 'local-copy-of-input-run')
    
    evaluator = extract_evaluation_commands()
    ret.add('TIRA_EVALUATION_INPUT_DIR=local-copy-of-input-run')
    ret.add('inputRun=local-copy-of-input-run')
    ret.add('TIRA_EVALUATION_OUTPUT_DIR=' + str(eval_dir(eval_id) / 'output'))
    ret.add('TIRA_FINAL_EVALUATION_OUTPUT_DIR=' + str(final_eval_dir(eval_id)))
    ret.add('inputDataset=' + input_dataset)
    ret.add('outputDir=' + str(eval_dir(eval_id) / 'output'))
    ret.add('TIRA_EVALUATION_IMAGE_TO_EXECUTE=' + evaluator['TIRA_EVALUATION_IMAGE_TO_EXECUTE'])
    ret.add('TIRA_EVALUATION_COMMAND_TO_EXECUTE=' + evaluator['TIRA_EVALUATION_COMMAND_TO_EXECUTE'])
    ret.add('TIRA_EVALUATION_SOFTWARE_ID=' + evaluator['TIRA_EVALUATION_SOFTWARE_ID'])

    return sorted(list(ret))

if __name__ == '__main__':
    fail_if_environment_variables_are_missing()
    copy_resources()

    with open('task.env', 'w') as f:
        for l in identify_environment_variables():
            f.write(l.strip() + '\n')

