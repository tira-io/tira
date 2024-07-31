#!/usr/bin/env python3
import logging
import os
import subprocess
import sys
from argparse import ArgumentParser, ArgumentTypeError

from tira.inference_server import run_inference_server


def limited_int_arg(lower_bound: int, upper_bound: int):
    def ret(arg: str) -> int:
        i = int(arg)
        if not (lower_bound <= i <= upper_bound):
            raise ArgumentTypeError(f"{i} is outside the permissible range from {lower_bound} to {upper_bound}")
        return i

    return ret


def parse_args():
    parser = ArgumentParser(prog="tira-run-inference-server", description="")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--script", type=str, help="The python script containing the model and the predict function.", required=False
    )
    group.add_argument(
        "--notebook", type=str, help="The notebook containing the model and the predict function.", required=False
    )

    parser.add_argument("--port", type=limited_int_arg(5000, 65536), help="Port number of local server.", required=True)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Sets the output verbosity. Default is INFO. Can be repeated for more verbose output.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.notebook is not None:
        notebook_name = args.notebook
        # convert notebook to python script
        command_convert = f"jupyter nbconvert --to script {notebook_name}"
        try:
            return_code = subprocess.check_call(
                command_convert, shell=True, stdout=sys.stdout, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError:
            return_code = 2
        if return_code != 0:
            print(f"Exception while converting notebook '{notebook_name}'. Stopping server.")
            sys.exit(return_code)
        module_name = notebook_name
    else:
        module_name = args.script

    absolute_path = os.path.splitext(os.path.abspath(module_name))[0] + ".py"
    module_name = os.path.splitext(module_name)[0].replace("/", ".")

    # flag execution for running as inference server (see third_party_integrations.is_running_as_inference_server)
    os.environ["TIRA_INFERENCE_SERVER"] = "True"

    loglevels = [logging.INFO, logging.DEBUG]
    loglevel = loglevels[min(args.verbose, len(loglevels) - 1)]
    run_inference_server(
        base_module=module_name, absolute_path=absolute_path, internal_port=args.port, loglevel=loglevel
    )
