#!/usr/bin/env python
import argparse
from tira.local_execution_integration import LocalExecutionIntegration
import os

def parse_args():
    parser = argparse.ArgumentParser(prog = 'tira-run')
    parser.add_argument('--input-directory', required=False, default=str(os.path.abspath(".")))
    parser.add_argument('--image', required=True)
    parser.add_argument('--command', required=True)
    parser.add_argument('--output-directory', required=False, default=str(os.path.abspath("tira-output")))

    return parser.parse_args()

def main():
    args = parse_args()
    tira_execution = LocalExecutionIntegration(None)
    tira_execution.run(identifier=None, image=args.image, command=args.command, input_dir=args.input_directory, output_dir=args.output_directory)

