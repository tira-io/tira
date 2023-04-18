#!/usr/bin/env python
import argparse
from tira.local_client import Client
from tira.local_execution_integration import LocalExecutionIntegration
import os

def parse_args():
    parser = argparse.ArgumentParser(prog='tira-run')
    parser.add_argument('--input-directory', required=False, default=str(os.path.abspath(".")))
    parser.add_argument('--input-run', required=False, default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--image')
    group.add_argument('--approach')
    parser.add_argument('--command', required=False)
    parser.add_argument('--verbose', required=False, default=False, type=bool)
    parser.add_argument('--dry-run', required=False, default=False, type=bool)
    parser.add_argument('--allow-network', required=False, default=False, type=bool, help='Is the network available during the execution? (Default = False to improve reproducibility, containers that import ir-datasets can have access to the network, they can be tested with setting allow-network to true.)')
    parser.add_argument('--output-directory', required=False, default=str(os.path.abspath("tira-output")))

    args = parser.parse_args()
    if (args.image is None) == (args.approach is None):
        parser.error('You have to exclusively use either --approach or --image.')
    if (args.image is None) != (args.command is None):
        parser.error('The options --image and --command have to be used together.')

    return args

def main():
    args = parse_args()
    client = Client()
    client.local_execution.run(identifier=args.approach, image=args.image, command=args.command, input_dir=args.input_directory, output_dir=args.output_directory, verbose=args.verbose, dry_run=args.dry_run, allow_network=args.allow_network, input_run=args.input_run)

