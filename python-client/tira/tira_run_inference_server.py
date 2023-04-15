#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess

from tira.inference_server import run_inference_server


def parse_args():
    parser = argparse.ArgumentParser(prog='tira-run-inference-server', description='')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--script', type=str, help='The python script containing the model and the predict function.', required=False)
    group.add_argument('--notebook', type=str, help='The notebook containing the model and the predict function.', required=False)

    parser.add_argument('--port', type=int, help='Port number of local server.', required=True)
    parser.add_argument('--log', type=str, help='Server log level. One of [INFO, WARNING, DEBUG]. Default is INFO', default='INFO', required=False)

    return parser.parse_args()


def main():
    args = parse_args()

    if not (5000 <= args.port <= 65536):
        print(f"Invalid port number {args.port}. Must be in range 5000 - 65536.")
        sys.exit(-1)

    if args.notebook is not None:
        notebook_name = args.notebook
        # convert notebook to python script
        command_convert = f"jupyter nbconvert --to script {notebook_name}"
        try:
            return_code = subprocess.check_call(command_convert, shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            return_code = 2
        if return_code != 0:
            print(f"Exception while converting notebook '{notebook_name}'. Stopping server.")
            sys.exit(return_code)
        module_name = notebook_name
    else:
        module_name = args.script

    absolute_path = os.path.splitext(os.path.abspath(module_name))[0] + '.py'
    module_name = os.path.splitext(module_name)[0].replace('/', '.')

    # flag execution for running as inference server (see third_party_integrations.is_running_as_inference_server)
    os.environ['TIRA_INFERENCE_SERVER'] = 'True'

    run_inference_server(base_module=module_name, absolute_path=absolute_path, internal_port=args.port, loglevel=args.log)
