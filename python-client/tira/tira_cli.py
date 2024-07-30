#!/usr/bin/env python
import argparse
import logging
from platform import python_version
from typing import TYPE_CHECKING, Optional

from tira import __version__
from tira.rest_api_client import Client as RestClient

if TYPE_CHECKING:
    from .tira_client import TiraClient


def download_run(client, approach, dataset):
    help()


"""
Utility functions to setup arguments that are common across multiple commands (e.g., logging).
"""


def setup_logging_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action="count",
        help="Increases the output verbosity. Default is INFO. Can be repeated for more verbose output.",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Disables logging.")


"""
Setup commands for each supported subcommand.
"""


def setup_download_command(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.add_argument(
        "--approach",
        required=False,
        default=None,
        help="Download the outputs of the specified approach. Usage: --approach <task-id>/<user-id>/<approach-name>",
    )
    parser.add_argument("--dataset", required=True, help="The dataset.")
    parser.set_defaults(executable=download_command)


def setup_login_command(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.add_argument("--token", required=True, default=None, help="The token to login to the server.")
    parser.add_argument(
        "--print-docker-auth",
        required=False,
        default=False,
        action="store_true",
        help="Print the docker credentials as TIRA_DOCKER_REGISTRY_USER and TIRA_DOCKER_REGISTRY_TOKEN to stdout.",
    )
    parser.set_defaults(executable=login_command)


def setup_upload_command(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.set_defaults(executable=upload_command)


"""
Implementations of each command. They don't all need to be here but if your command is short and sweet and you don't
don't know, where else to put it, this is a good place.
"""


def download_command(dataset: str, approach: Optional[str] = None, **kwargs) -> int:
    client: "TiraClient" = RestClient()
    if approach is not None:
        print(client.get_run_output(approach, dataset))
    else:
        print(client.download_dataset(None, dataset))
    return 0


def login_command(token: str, print_docker_auth: bool, **kwargs) -> int:
    client: "TiraClient" = RestClient()
    client.login(token)
    if print_docker_auth:
        print(client.local_execution.docker_client_is_authenticated())
    return 0


def upload_command() -> None:
    pass


"""
Finally, parsing the arguments and running the chose command.
"""


def parse_args():
    parser = argparse.ArgumentParser(prog="tira-cli")
    version_str = f"TIRA v{__version__} using Python v{python_version()}"
    parser.add_argument("-v", "--version", action="version", version=version_str)

    # Register all subcommands here:
    subparsers = parser.add_subparsers(dest="command", required=True)
    setup_download_command(subparsers.add_parser("download", help="Download runs or datasets from TIRA.io"))
    setup_upload_command(subparsers.add_parser("upload", help="Upload runs or datasets to TIRA.io"))
    setup_login_command(subparsers.add_parser("login", help="Login your TIRA client to the tira server."))

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not hasattr(args, "executable") or args.executable is None:
        logging.critical("No subcommand was found or it was not set up correctly.")
        logging.critical(
            f"Command: {vars(args).get('command', None)}; Executable: {vars(args).get('executable', None)}"
        )
        return -1

    # Potential bug: a user could supply his own "quiet" argument without using setup_logging_args and we would handle
    # it as if it was a logging argument, which it may not be. Probably the best solution right now would be to create a
    # custom argparse.Action for setup_logging_args to handle the --quiet and --verbose options... but that would be a
    # bit more effort and we can tackle that when this actually clashes (i.e., if we need --quiet or --verbose handled
    # differently in another command.
    if hasattr(args, "quiet") and args.quiet:
        logging.disable()
    else:
        if not hasattr(args, "verbose"):
            args.verbose = 0
        verbosity_levels = [logging.CRITICAL, logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
        default_verbosity = verbosity_levels.index(logging.INFO)
        verbosity = verbosity_levels[min(default_verbosity + args.verbose, len(verbosity_levels) - 1)]
        logging.basicConfig(level=verbosity)

    # Subcommands store their executable into args.executable which takes the parsed arguments and returns an integer.
    # We just dump all the arguments into the function and let it sort it out itself.
    return args.executable(**vars(args))
