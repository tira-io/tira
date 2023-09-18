#!/usr/bin/env python
import argparse
from tira.local_client import Client
from tira.rest_api_client import Client as RestClient
from tira.local_execution_integration import LocalExecutionIntegration
from pathlib import Path
import os
import shutil

def parse_args():
    parser = argparse.ArgumentParser(prog='tira-run')
    parser.add_argument('--input-directory', required=False, default=str(os.path.abspath(".")))
    parser.add_argument('--input-run', required=False, default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--image')
    group.add_argument('--approach')
    group.add_argument('--export-dataset', required=False, default=None, type=str)
    group.add_argument('--export-approach-output', nargs='*', required=False, default=None, type=str)
    group.add_argument('--export-submission-from-jupyter-notebook', required=False, default=None, type=str)
    parser.add_argument('--command', required=False)
    parser.add_argument('--verbose', required=False, default=False, type=bool)
    parser.add_argument('--dry-run', required=False, default=False, type=bool)
    parser.add_argument('--dataset-for-export-approach-output', required=False, default=False, type=str)
    parser.add_argument('-v', action='append', default=None, help='Additional volume mounts as <host-path>:<container-path>:<read-write-mode>', required=False)
    parser.add_argument('--allow-network', required=False, default=False, type=bool, help='Is the network available during the execution? (Default = False to improve reproducibility, containers that import ir-datasets can have access to the network, they can be tested with setting allow-network to true.)')
    parser.add_argument('--output-directory', required=False, default=str(os.path.abspath("tira-output")))

    args = parser.parse_args()
    if args.export_submission_from_jupyter_notebook:
        return args

    if (args.image is None) == (args.approach is None) == (args.export_dataset):
        parser.error('You have to exclusively use either --approach or --image.')
    if (args.image is None) != (args.command is None):
        parser.error('The options --image and --command have to be used together.')

    return args

def main():
    args = parse_args()
    client = Client()
    
    if args.export_submission_from_jupyter_notebook:
        ret = LocalExecutionIntegration().export_submission_from_jupyter_notebook(args.export_submission_from_jupyter_notebook)
        if not ret:
            exit(1)
            return
        print(ret)
        return
    
    if args.export_dataset:
        if len(args.export_dataset.split('/')) != 2:
            print(f'Please pass arguments as: --export-dataset <task>/<tira-dataset>. Got {args.export_dataset}')
            return
        
        task, dataset = args.export_dataset.split('/')
        print(f'Export dataset "{dataset}" for task "{task}" to directory "{args.output_directory}".')

        tira = RestClient()
        data_dir = tira.download_dataset(task, dataset)
        
        if os.path.exists(args.output_directory):
            print(f'The directory {args.output_directory} specified by --output-directory already exists. I do not overwrite the directory, please remove it manually if you want to export the dataset.')
        shutil.copytree(data_dir, args.output_directory)
        
        return

    if args.export_approach_output:
        if not args.dataset_for_export_approach_output:
            print(f'Please specify the dataset for which the approach outputs should be exported via --dataset-for-export-approach-output')
            return

        if os.path.exists(args.output_directory):
            print(f'The directory {args.output_directory} specified by --output-directory already exists. I do not overwrite the directory, please remove it manually if you want to export the dataset.')
            return

        tira = RestClient()
        data_dirs = []

        for approach in args.export_approach_output:
            if len(approach.split('/')) != 3:
                print(f'Please pass arguments as: --export-approach-output <task>/<tira-dataset>/approach. Got {approach}')

        for approach in args.export_approach_output:
            data_dirs += [tira.get_run_output(approach, args.dataset_for_export_approach_output, True)]

        for num, data_dir in zip(range(len(data_dirs)), data_dirs):
            shutil.copytree(data_dir, Path(args.output_directory) / str(num+1))

        return

    client.local_execution.run(identifier=args.approach, image=args.image, command=args.command, input_dir=args.input_directory, output_dir=args.output_directory, verbose=args.verbose, dry_run=args.dry_run, allow_network=args.allow_network, input_run=args.input_run, additional_volumes=args.v)

