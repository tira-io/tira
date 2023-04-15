#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess


def parse_args():
    parser = argparse.ArgumentParser(prog='tira-run-notebook', description='')

    parser.add_argument('--input', type=str, help='The directory that contains the input data (within tira-run this should be \'$inputDataset\').', required=True)
    parser.add_argument('--notebook', type=str, help='The notebook to execute.', required=True)
    parser.add_argument('--output', type=str, help='The directory for storing output data (within tira-run this should be \'$outputDir\').', required=True)

    return parser.parse_args()


def main():
    args = parse_args()
    os.environ['TIRA_INPUT_DIRECTORY'] = args.input
    os.environ['TIRA_OUTPUT_DIRECTORY'] = args.output

    command = f'runnb --allow-not-trusted {args.notebook}'
    try:
        return_code = subprocess.check_call(command, shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return_code = 2
    sys.exit(return_code)
