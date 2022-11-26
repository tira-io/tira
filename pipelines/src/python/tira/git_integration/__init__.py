#!/usr/bin/env python3

import django
from datetime import datetime as dt
from pathlib import Path
django.setup()

from tira.data.FileDatabase import FileDatabase

# I use this for the moment to ensure that the cache is not filled for multiple minutes.
class TiraGitFileDatabase(FileDatabase):
    def __init__(self):
        self.datasets = None  # dict of dataset_id: modelpb.Dataset
        self.tasks = None  # dict of task_id: modelpb.Tasks.Task
        self.updates = {
            "organizers": dt.now(),
            "vms": dt.now(),
            "tasks": dt.now(),
            "datasets": dt.now(),
            "software": dt.now(),
            "default_tasks": dt.now(),
            "software_by_vm": dt.now(),
            "software_count_by_dataset": dt.now()
        }
        self._parse_dataset_list()
        self._parse_task_list()

def get_tira_db():
    return TiraGitFileDatabase()

if __name__ == '__main__':
    db = TiraGitFileDatabase()

    dataset_id = 'clickbait-spoiling-task-01-validation-dataset-2022-08-01'
    vm_id = 'princess-knight'
    run_id = '2022-07-20-12-54-28'
    
    input_run = db.RUNS_DIR_PATH / dataset_id / vm_id / run_id / 'output'
    output_run = Path(dt.now().strftime('%Y-%m-%d-%H-%M-%S')) / 'output'
    print(db._load_run(dataset_id, vm_id, run_id))
    
    task_id = 'clickbait-spoiling'

    print(db.get_evaluator(dataset_id, task_id))

