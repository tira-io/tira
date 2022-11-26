#!/usr/bin/env python3

from git import Repo
import argparse
from tira.git_integration import get_tira_db
from tira.git_integration.gitlab_integration import yield_all_running_pipelines
import tempfile
from pathlib import Path
import shutil
from datetime import datetime as dt

def ensure_repo_is_fresh(repo_dir):
    repo = Repo(repo_dir)
    repo.remote().pull(repo.active_branch)

def parse_args():
    parser = argparse.ArgumentParser('tira-git')
    subparsers = parser.add_subparsers(help='Subcommands either run a user software or evaluate a run.', dest='command')
    parser.add_argument('--repo_dir', help='The repository to use.', required=False, default='.')
    
    parser_eval = subparsers.add_parser('run-evaluate', help='Evaluate an existing run.')
    parser_eval.add_argument('--task_id', help='The id of the task.', required=True)
    parser_eval.add_argument('--dataset_id', help='The id of the task.', required=True)
    parser_eval.add_argument('--vm_id', help='The id of the vm/user.', required=True)
    parser_eval.add_argument('--run_id', help='The id of the run to evaluate.', required=True)
    
    return parser.parse_args()

def run_evaluate(args):
    identifier = 'eval---' + args.dataset_id + '---' + args.vm_id + '---' + args.run_id + '---started-' + str(dt.now().strftime('%Y-%m-%d-%H-%M-%S'))
    
    for pipeline_identifer in yield_all_running_pipelines():
        if pipeline_identifer == identifier.split('---started-')[0]:
            print('A pipeline for identifier "' + pipeline_identifer + '" is already scheduled/running. I do nothing.')
            return
    
    db = get_tira_db()
    ensure_repo_is_fresh(args.repo_dir)
    run = db._load_run(args.dataset_id, args.vm_id, args.run_id)
    if run == None or run.runId != args.run_id:
        raise ValueError('The specified run does not exist: ' + str(args))

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname = tmpdirname +'/repo'
        shutil.copytree(args.repo_dir, tmpdirname)
        job_dir = Path(tmpdirname) / args.dataset_id / args.vm_id / args.run_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        repo = Repo(tmpdirname)
        branch = repo.create_head(identifier)
        repo.head.reference = branch
        repo.head.reset(index=True, working_tree=True)
        
        with open(str(job_dir / 'job-to-execute.txt'), 'w') as f:
            f.write('''TIRA_IMAGE_TO_EXECUTE=ubuntu:18.04
TIRA_COMMAND_TO_EXECUTE=echo 'No software to execute. Only evaluation'
TIRA_SOFTWARE_ID=-1
TIRA_TASK_ID=''' + args.task_id + '''
TIRA_GIT_ID=''' + identifier + '''''')

        
        repo.index.add([str(Path(args.dataset_id) / args.vm_id / args.run_id / 'job-to-execute.txt')])
        repo.index.commit("Evaluate software")
        repo.remote().push(identifier)
        print('A new job with identifier "' + identifier + '" is scheduled.')
    
if __name__ == '__main__':
    args = parse_args()
    
    if args.command == 'run-evaluate':
        run_evaluate(args)
    else:
        raise ValueError('I can not handle the passed command: ' + str(args))

