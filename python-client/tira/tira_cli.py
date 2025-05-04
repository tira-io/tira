#!/usr/bin/env python
import argparse
import logging
from pathlib import Path
from platform import python_version
from typing import TYPE_CHECKING, Optional

from tira import __version__
from tira.check_format import fmt_message
from tira.io_utils import _fmt, log_message, verify_tira_installation
from tira.rest_api_client import Client as RestClient
from tira.tira_run import guess_system_details, guess_vm_id_of_user

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


def setup_evaluation_command(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.add_argument(
        "--predictions", required=True, default=None, help="The directory with the predictions to evaluate."
    )
    parser.add_argument(
        "--truths", required=False, default=None, help="The optional truths (use truths from the config if available)."
    )
    parser.add_argument("--config", required=True, help="The dataset for which the predictions are made.")
    parser.set_defaults(executable=evaluate_command)


def evaluate_command(predictions: Path, truths: Path, dataset: str, **kwargs) -> int:
    client: "TiraClient" = RestClient()
    eval_config = client.get_dataset(dataset)
    if not truths:
        if "task_id" in eval_config:
            task_id = eval_config["task_id"]
        elif "default_task" in eval_config:
            task_id = eval_config["default_task"]
        else:
            raise ValueError("Task configuration is invalid")

        truths = Path(client.download_dataset(task_id, eval_config["dataset_id"], truth_dataset=True))

    from tira.evaluators import evaluate, load_evaluator_config

    use_unsandboxed_evaluator = False

    try:
        load_evaluator_config(eval_config, client)
        use_unsandboxed_evaluator = True
    except:
        pass

    if use_unsandboxed_evaluator:
        print(evaluate(Path(predictions), Path(truths), eval_config))
    else:
        client.evaluate(Path(predictions), dataset)

    return 0


def setup_code_submission_command(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.add_argument(
        "--path",
        required=True,
        default=None,
        help="The path used to build the docker image, must be in a clean git repository.",
    )
    parser.add_argument(
        "--command",
        required=False,
        default=None,
        help="The command that executes your approach in the docker image (default: the Docker Entrypoint). The command should read the data from $inputDataset to write predictions to $outputDir.",
    )
    parser.add_argument(
        "--dry-run",
        required=False,
        default=False,
        action="store_true",
        help="Make a dry-run, i.e., to develop your solution, i.e., not uploading to TIRA and not requiring that the git repo is clean.",
    )
    parser.add_argument(
        "--allow-network",
        required=False,
        default=False,
        action="store_true",
        help="Allow network communication. Within TIRA itself, software is executed in a sandbox without internet access",
    )
    parser.add_argument("--task", required=True, default=None, help="The task to which the code should be submitted.")
    parser.add_argument(
        "--dataset", required=False, default=None, help="The dataset on which the code should be tested before upload."
    )

    parser.set_defaults(executable=code_submission_command)


def setup_verify_installation(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.set_defaults(executable=verify_installation_command)


def setup_upload_command(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.add_argument(
        "--directory", required=True, default=None, help="The directory with the predictions to upload."
    )
    parser.add_argument("--dataset", required=True, help="The dataset for to which the predictions should be uploaded.")
    parser.add_argument(
        "--dry-run",
        required=False,
        default=False,
        action="store_true",
        help="Make a dry-run, i.e., to verify that your output is valid without uploading to TIRA.",
    )
    parser.add_argument(
        "--system", required=False, default=None, help="The system name under which the run should be uploaded."
    )
    parser.set_defaults(executable=upload_command)


def setup_eval_command(parser: argparse.ArgumentParser) -> None:
    setup_logging_args(parser)
    parser.add_argument(
        "--predictions",
        required=True,
        default=None,
        help="The path that contains the predictions.",
    )

    parser.add_argument(
        "--truths",
        required=False,
        default=None,
        help="Optional: the path that contains the truths (use the dataset from the dataset otherwise).",
    )

    parser.add_argument("--dataset", required=False, help="The dataset for which the predictions are made.")
    parser.set_defaults(executable=evaluate_command)


"""
Implementations of each command. They don't all need to be here but if your command is short and sweet and you don't
don't know, where else to put it, this is a good place.
"""


def download_command(dataset: str, approach: "Optional[str]" = None, **kwargs) -> int:
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


def code_submission_command(
    path: Path,
    task: str,
    dry_run: bool,
    allow_network: bool,
    command: "Optional[str]",
    dataset: "Optional[str]",
    **kwargs,
) -> int:
    client: "TiraClient" = RestClient()
    client.submit_code(Path(path), task, command, dry_run=dry_run, allow_network=allow_network, dataset_id=dataset)

    return 0


def verify_installation_command(**kwards) -> int:
    status = verify_tira_installation()

    print("\nResult:")
    msg = "Your TIRA installation is valid."
    if status == _fmt.WARN:
        msg = "There are some warnings, you might not use all features."

    if status == _fmt.ERROR:
        msg = "Your installation is not valid, you might not use all features."

    log_message(msg, status)
    return 0 if status == _fmt.OK else 1


def upload_command(dataset: str, directory: Path, dry_run: bool, system: str, **kwargs) -> None:
    client: "TiraClient" = RestClient()
    vm_id = None
    default_task = None
    if client.api_key_is_valid():
        system = guess_system_details(directory, system)
        dataset_info = client.get_dataset(dataset=dataset)
        default_task = dataset_info["default_task"]
        vm_id = guess_vm_id_of_user(default_task, client)
        if not system:
            print(
                fmt_message(
                    "Please specify the name of your system. Either:"
                    + "\n\n\tIncorporate the tag into your ir-metadata (see https://ir-metadata.org),"
                    + "\n\n\tor, pass --system to tira-cli upload",
                    _fmt.ERROR,
                )
            )
            return 1

    resp = client.upload_run_anonymous(directory, dataset, dry_run, verbose=not system and not vm_id)
    if not resp or "uuid" not in resp or not resp["uuid"]:
        raise ValueError("Upload failed...")

    if not system or not vm_id:
        # only anonymous submissions
        return 0
    else:
        print("\nI upload the metadata for the submission...")
        resp = client.claim_ownership(
            resp["uuid"], vm_id, system["tag"], system.get("description", "todo: Add a description"), default_task
        )
        if "status" not in resp or "0" != resp["status"]:
            raise ValueError("There was an error with the upload, please try again...")
        print(
            "\t"
            + fmt_message(
                f"Done. Your run is available at:\n\thttps://www.tira.io/submit/{default_task}/user/{vm_id}/upload-submission",
                _fmt.OK,
            )
        )
        return 0


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
    setup_eval_command(subparsers.add_parser("evaluate", help="Evaluate runs locally."))
    setup_login_command(subparsers.add_parser("login", help="Login your TIRA client to the tira server."))
    setup_verify_installation(
        subparsers.add_parser("verify-installation", help="Verify that your local TIRA client is correctly installed.")
    )
    setup_code_submission_command(
        subparsers.add_parser("code-submission", help="Make a code submission via Docker from a git repository.")
    )

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
