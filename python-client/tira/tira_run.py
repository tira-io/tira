#!/usr/bin/env python
import argparse
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from tira.check_format import _fmt, log_message
from tira.io_utils import huggingface_model_mounts
from tira.local_client import Client
from tira.local_execution_integration import LocalExecutionIntegration
from tira.rest_api_client import Client as RestClient
from tira.third_party_integrations import extract_previous_stages_from_docker_image

if TYPE_CHECKING:
    from .tira_client import TiraClient


def setup_upload_run_command(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("runfile", type=argparse.FileType("rb"), help="Path to the runfile to be uploaded")
    parser.add_argument("--dataset-id", required=True, type=str)
    parser.add_argument("--task-id", required=False, default=os.environ.get("TIRA_TASK_ID"), type=str)
    parser.add_argument("--vm-id", required=False, default=os.environ.get("TIRA_VM_ID"), type=str)
    parser.add_argument("--upload-group", required=True, type=str)

    # Register the upload_run_command method as the "main"-method
    parser.set_defaults(executable=upload_run_command)


def upload_run_command(args: argparse.Namespace) -> int:
    # TODO: allow the user to override some settings (e.g., API key and URL) via arguments
    tira = RestClient()
    if args.task_id is None:
        raise argparse.ArgumentTypeError("Please populate --task-id or set the environment variable TIRA_TASK_ID")
    if args.vm_id is None:
        raise argparse.ArgumentTypeError("Please populate --vm-id or set the environment variable TIRA_VM_ID")
    upload_id = tira.create_upload_group(args.task_id, args.vm_id, args.upload_group)
    success = tira.upload_run(
        task_id=args.task_id, vm_id=args.vm_id, dataset_id=args.dataset_id, upload_id=upload_id, filestream=args.runfile
    )
    return 0 if success else 1


def guess_vm_id_of_user(tira_task_id: str, rest_client, tira_vm_id: "Optional[str]" = None):
    if tira_vm_id:
        return tira_vm_id
    tmp = rest_client.metadata_for_task(tira_task_id)
    if tmp and "status" in tmp and 0 == tmp["status"] and "context" in tmp and "user_vms_for_task" in tmp["context"]:
        if len(tmp["context"]["user_vms_for_task"]) != 1:
            log_message(
                f'You have multiple vms ({tmp["context"]["user_vms_for_task"]}).\n\tPlease use the following command to authenticate yourself:\n\ttira-cli login --token YOUR-AUTH-TOKEN\n\ttira-cli verify-installation\n\n\n\tPlease pass --dry-run if you want to test without uploading use option --tira-vm-id to'
                " specify the vm.\n\t(if you have multiple virtual machines, please pass --tira-vm-id or set the TIRA_VM_ID ENVIRONMENT)",
                _fmt.ERROR,
            )
            return None
        else:
            return tmp["context"]["user_vms_for_task"][0]
    else:
        log_message(
            "You are not authenticated.\n\tPlease use the following command to authenticate yourself:\n\ttira-cli login --token YOUR-AUTH-TOKEN\n\ttira-cli verify-installation\n\n\n\tPlease pass --dry-run if you want to test without uploading",
            _fmt.ERROR,
        )
        return


def guess_dataset(directory: Path, include_hidden_dirs=True) -> Optional[str]:
    from tira.check_format import lines_if_valid

    ret = []
    lines = []
    try:
        lines = lines_if_valid(Path(directory), "ir_metadata")
    except ValueError:
        pass

    for line in lines:
        if (
            line
            and (include_hidden_dirs or ("name" in line and not line["name"].startswith(".")))
            and "content" in line
            and "data" in line["content"]
            and line["content"]["data"]
            and "test collection" in line["content"]["data"]
            and "name" in line["content"]["data"]["test collection"]
            and isinstance(line["content"]["data"]["test collection"]["name"], str)
        ):
            ret.append(line["content"]["data"]["test collection"]["name"])

    ret = list(set(ret))
    if len(ret) > 1:
        if include_hidden_dirs:
            tmp_ret = guess_dataset(directory, False)
            if tmp_ret is not None:
                return tmp_ret

        print(f"Dataset definitions are ambiguous, I got {ret}.")
    return None if len(ret) != 1 else ret[0]


def guess_system_details(directory, system) -> Dict:
    if system:
        return {"tag": system}

    from tira.check_format import lines_if_valid

    lines = []
    try:
        lines = lines_if_valid(Path(directory), "ir_metadata")
    except ValueError:
        pass

    for line in lines:
        if (
            line
            and "content" in line
            and "tag" in line["content"]
            and line["content"]["tag"]
            and isinstance(line["content"]["tag"], str)
        ):
            ret = {"tag": line["content"]["tag"]}
            if "research goal" in line["content"] and "description" in line["content"]["research goal"]:
                ret["description"] = line["content"]["research goal"]["description"]
            if "actor" in line["content"] and "team" in line["content"]["actor"]:
                ret["team"] = line["content"]["actor"]["team"]

            return ret

    return None


def parse_args():
    parser = argparse.ArgumentParser(prog="tira-run")
    parser.add_argument("--input-directory", required=False, default=str(os.path.abspath(".")))
    parser.add_argument("--input-dataset", required=False, default=None)
    parser.add_argument("--input-run", required=False, default=None)
    parser.add_argument("--input-run-directory", required=False, default=None)
    # Not required if the subcommand "tira-run submit" is used.
    # FIXME: the arguments in this group should probably be subcommands
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--image")
    group.add_argument("--approach")
    group.add_argument("--export-dataset", required=False, default=None, type=str)
    group.add_argument("--export-approach-output", nargs="*", required=False, default=None, type=str)
    group.add_argument("--export-submission-from-jupyter-notebook", required=False, default=None, type=str)
    group.add_argument("--export-submission-environment", nargs="*", required=False, default=None, type=str)
    parser.add_argument(
        "--command",
        required=False,
        help=(
            "Command to execute in the container. Has access to variables $inputDataset (points to the directory with"
            " the inputs), $outputDir (results should be persisted in this directory), and optionally $inputRun (points"
            " to the directory with the outputs of the previous stage)."
        ),
    )
    parser.add_argument("--verbose", required=False, default=False, action="store_true")
    parser.add_argument(
        "--gpus",
        required=False,
        default=False,
        type=str,
        help='GPU devices to add to the container ("all" or -1 to pass all GPUs, or the number of devices).',
    )
    parser.add_argument("--evaluate", required=False, default=False, type=bool)
    parser.add_argument("--evaluation-directory", required=False, default=str(os.path.abspath("tira-evaluation")))
    parser.add_argument("--dry-run", required=False, default=False, type=bool)
    parser.add_argument("--dataset-for-export-approach-output", required=False, default=False, type=str)
    parser.add_argument(
        "-v",
        action="append",
        default=None,
        help="Additional volume mounts as <host-path>:<container-path>:<read-write-mode>",
        required=False,
    )
    parser.add_argument(
        "--allow-network",
        required=False,
        default=False,
        type=bool,
        help=(
            "Is the network available during the execution? (Default = False to improve reproducibility, containers"
            " that import ir-datasets can have access to the network, they can be tested with setting allow-network to"
            " true.)"
        ),
    )
    parser.add_argument("--output-directory", required=False, default=str(os.path.abspath("tira-output")))

    parser.add_argument("--push", required=False, default="false")
    parser.add_argument(
        "--skip-local-test",
        required=False,
        default=False,
        action="store_true",
        help="Skip the execution of the local test, only upload the submission to TIRA.",
    )
    parser.add_argument(
        "--tira-docker-registry-token", required=False, default=os.environ.get("TIRA_DOCKER_REGISTRY_TOKEN")
    )
    parser.add_argument(
        "--tira-docker-registry-user", required=False, default=os.environ.get("TIRA_DOCKER_REGISTRY_USER")
    )
    parser.add_argument("--tira-client-token", required=False, default=os.environ.get("TIRA_CLIENT_TOKEN"))
    parser.add_argument("--tira-client-user", required=False, default=os.environ.get("TIRA_CLIENT_USER"))
    parser.add_argument("--tira-vm-id", required=False, default=os.environ.get("TIRA_VM_ID"))
    parser.add_argument("--tira-task-id", required=False, default=os.environ.get("TIRA_TASK_ID"))
    parser.add_argument("--tira-code-repository-id", required=False, default=os.environ.get("TIRA_CODE_REPOSITORY_ID"))
    parser.add_argument(
        "--fail-if-output-is-empty",
        required=False,
        default=False,
        action="store_true",
        help="After the execution of the software, fail if the output directory is empty.",
    )
    parser.add_argument(
        "--mount-hf-model",
        nargs="+",
        default=[],
        help=(
            "Mount models from the local huggingface hub cache (i.e., $HOME/.cache/huggingface/hub) into the container"
            " during execution. This is intended to remove redundancy so that the models must not be embedded into the"
            " Docker images."
        ),
    )

    subparsers = parser.add_subparsers()
    setup_upload_run_command(subparsers.add_parser("upload", help="For uploading runs"))

    args = parser.parse_args()
    if args.export_submission_from_jupyter_notebook:
        return args

    if args.export_submission_environment:
        return args

    if os.path.exists(args.output_directory) and len(os.listdir(args.output_directory)) > 0:
        parser.error(
            f"The output directory {os.path.abspath(args.output_directory)} is not empty. Please empty it or provide a"
            " new output directory with --ouptut-directory."
        )

    if (args.image is None) == (args.approach is None) == (args.export_dataset):
        parser.error("You have to exclusively use either --approach or --image.")
    if (args.image is None) != (args.command is None):
        args.command = LocalExecutionIntegration().extract_entrypoint(args.image)

        if args.command is not None:
            print(f'Use command from Docker image "{args.command}".')
        else:
            parser.error(
                "I could not find a command to execute, please either configure the entrypoint of the image or use"
                " --command."
            )

    args.previous_stages = [] if not args.input_run else [args.input_run]

    if args.input_run is None and args.input_run_directory is None and args.image is not None:
        args.input_run = extract_previous_stages_from_docker_image(args.image, args.command)
        args.command = LocalExecutionIntegration().make_command_absolute(args.image, args.command)
        args.previous_stages = args.input_run
        if args.input_run and len(args.input_run) == 1:
            args.input_run = args.input_run[0]

    if args.push.lower() == "true":
        print("I will check that the API key and the credentials for the image registry are valid.")
        rest_client = RestClient()
        docker_authenticated = rest_client.local_execution.docker_client_is_authenticated()

        api_key_valid = rest_client.api_key_is_valid()

        if args.tira_client_token:
            if api_key_valid:
                args.tira_client_token = rest_client.api_key
            elif "TIRA_CLIENT_TOKEN" in os.environ and os.environ.get("TIRA_CLIENT_TOKEN"):
                rest_client = RestClient(api_key=os.environ.get("TIRA_CLIENT_TOKEN"))
                api_key_valid = rest_client.api_key_is_valid()
                if api_key_valid:
                    args.tira_client_token = rest_client.api_key
                else:
                    parser.error(
                        "The option --tira-client-token (or environment variable TIRA_CLIENT_TOKEN) is required when"
                        " --push is active."
                    )
            else:
                rest_client = RestClient(api_key=args.tira_client_token)
                if not rest_client.api_key_is_valid():
                    parser.error(
                        "The option --tira-client-token (or environment variable TIRA_CLIENT_TOKEN) is required when"
                        " --push is active."
                    )

        if not args.tira_task_id and args.input_dataset:
            args.tira_task_id = args.input_dataset.split("/")[0]

        if not args.tira_task_id:
            parser.error(
                "The option --tira-task-id (or environment variable TIRA_TASK_ID) is required when --push is active."
            )

        args.tira_vm_id = guess_vm_id_of_user(args.tira_task_id, rest_client, args.tira_vm_id)
        if not args.tira_vm_id:
            parser.error("There was an error (see above).")

        if not args.tira_client_user:
            tmp = rest_client.metadata_for_task(args.tira_task_id)
            if tmp and "status" in tmp and 0 == tmp["status"] and "context" in tmp and "user_id" in tmp["context"]:
                args.tira_client_user = tmp["context"]["user_id"]
            else:
                parser.error(
                    "The option --tira-client-user (or environment variable TIRA_CLIENT_USER) is required when --push"
                    " is active."
                )

        if (
            not docker_authenticated
            and not args.tira_docker_registry_token
            and not rest_client.local_execution.login_docker_client(args.tira_task_id, args.tira_vm_id)
        ):
            parser.error(
                "The option --tira-docker-registry-token (or environment variable TIRA_DOCKER_REGISTRY_TOKEN) is"
                " required when --push is active."
            )

        if (
            not docker_authenticated
            and not args.tira_docker_registry_user
            and not rest_client.local_execution.login_docker_client(args.tira_task_id, args.tira_vm_id)
        ):
            parser.error(
                "The option --tira-docker-registry-user (or environment variable TIRA_DOCKER_REGISTRY_USER) is required"
                " when --push is active."
            )

        args.previous_stages = [
            rest_client.public_runs(
                args.tira_task_id, args.input_dataset.split("/")[1], i.split("/")[1], i.split("/")[2]
            )
            for i in args.previous_stages
        ]
        if "none" in args.previous_stages or None in args.previous_stages:
            parser.error(
                "One of the previous stages is not public. Please contact the organizer with a link to your code so"
                " that they can ensure it is public."
            )

    if not args.approach and not args.image:
        parser.error("Please specify what you want to run.")

    return args


def push_image(client, image, tira_task_id, tira_vm_id):
    registry_prefix = client.docker_registry() + "/code-research/tira/tira-user-" + tira_vm_id + "/"
    print("Push Docker image")

    return client.local_execution.push_image(image, registry_prefix, tira_task_id, tira_vm_id)


def main(args=None):
    args = args if args else parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    client: "TiraClient" = Client()

    # Subcommands store their executable into args.executable which takes the parsed arguments and returns an integer
    if hasattr(args, "executable") and args.executable is not None:
        exit(args.executable(args))

    if args.export_submission_from_jupyter_notebook:
        ret = LocalExecutionIntegration().export_submission_from_jupyter_notebook(
            args.export_submission_from_jupyter_notebook
        )
        if not ret:
            exit(1)
            return
        print(ret)
        return

    if args.export_submission_environment:
        from tira.io_utils import all_environment_variables_for_github_action_or_fail

        for i in all_environment_variables_for_github_action_or_fail(args.export_submission_environment):
            print(i)
        return

    if args.export_dataset:
        if len(args.export_dataset.split("/")) != 2:
            print(f"Please pass arguments as: --export-dataset <task>/<tira-dataset>. Got {args.export_dataset}")
            return

        task, dataset = args.export_dataset.split("/")
        print(f'Export dataset "{dataset}" for task "{task}" to directory "{args.output_directory}".')

        tira = RestClient()
        data_dir = tira.download_dataset(task, dataset)

        if os.path.exists(args.output_directory):
            print(
                f"The directory {args.output_directory} specified by --output-directory already exists. I do not"
                " overwrite the directory, please remove it manually if you want to export the dataset."
            )
        shutil.copytree(data_dir, args.output_directory)
        return

    if args.export_approach_output:
        if not args.dataset_for_export_approach_output:
            print(
                "Please specify the dataset for which the approach outputs should be exported via"
                " --dataset-for-export-approach-output"
            )
            return

        if os.path.exists(args.output_directory):
            print(
                f"The directory {args.output_directory} specified by --output-directory already exists. I do not"
                " overwrite the directory, please remove it manually if you want to export the dataset."
            )
            return

        tira = RestClient()
        data_dirs = []

        for approach in args.export_approach_output:
            if len(approach.split("/")) != 3:
                print(
                    f"Please pass arguments as: --export-approach-output <task>/<tira-dataset>/approach. Got {approach}"
                )

        for approach in args.export_approach_output:
            data_dirs += [tira.get_run_output(approach, args.dataset_for_export_approach_output, True)]

        for num, data_dir in zip(range(len(data_dirs)), data_dirs):
            shutil.copytree(data_dir, Path(args.output_directory) / str(num + 1))

        return

    input_dir = args.input_directory
    evaluate = False
    if args.input_dataset and "none" != args.input_dataset.lower():
        if len(args.input_dataset.split("/")) != 2:
            print(f"Please pass arguments as: --input-dataset <task>/<tira-dataset>. Got {args.input_dataset}")
            return

        task, dataset = args.input_dataset.split("/")
        tira = RestClient()
        print(f"Ensure that the input dataset {dataset} is available.")
        input_dir = tira.download_dataset(task, dataset)
        print(f"Done: Dataset {dataset} is available locally.")

        if args.input_run and not isinstance(args.input_run, list) and "none" != args.input_run.lower():
            print(f"Ensure that the input run {args.input_run} is available.")
            args.input_run = tira.get_run_output(args.input_run, dataset, True)
            print("Done: input run is available locally.")
        elif args.input_run and not isinstance(args.input_run, list) and len(args.input_run) > 0:
            temp_dir = "/tmp/" + tempfile.TemporaryDirectory().name
            os.makedirs(temp_dir, exist_ok=True)
            for num, input_run in zip(range(len(args.input_run)), args.input_run):
                print(f"Ensure that the input run {input_run} is available.")
                input_run = tira.get_run_output(input_run, dataset, True)
                shutil.copytree(input_run, temp_dir + "/" + str(1 + num))
            args.input_run = temp_dir
        elif args.input_run_directory and "none" != args.input_run_directory.lower():
            args.input_run = os.path.abspath(args.input_run_directory)

        if args.evaluate:
            print(f"Ensure that the evaluation truth for dataset {dataset} is available.")
            evaluate = tira.get_configuration_of_evaluation(task, dataset)
            evaluate["truth_directory"] = tira.download_dataset(task, dataset, truth_dataset=True)
            print(f"Done: Evaluation truth for dataset {dataset} is available.")

    if args.mount_hf_model:
        hf_models = huggingface_model_mounts(args.mount_hf_model)
        hf_models = [k + ":" + v["bind"] + ":" + v["mode"] for k, v in hf_models.items()]
        print(f"The following models from huggingface are mounted: {hf_models}\n\n")
        if not args.v:
            args.v = []
        args.v += hf_models

    print(
        f"""
########################################## TIRA RUN CONFIGURATION ######################################################
# image={args.image}
# command={args.command}
########################################################################################################################
"""
    )
    gpus = 0
    if args.gpus:
        gpus = -1 if args.gpus == "all" else int(args.gpus)

    if not args.skip_local_test:
        client.local_execution.run(
            identifier=args.approach,
            image=args.image,
            command=args.command,
            input_dir=input_dir,
            output_dir=args.output_directory,
            dry_run=args.dry_run,
            allow_network=args.allow_network,
            input_run=args.input_run,
            additional_volumes=args.v,
            evaluate=evaluate,
            eval_dir=args.evaluation_directory,
            gpu_count=gpus,
        )
    else:
        print("Skip the local test execution of the software.")

    if args.fail_if_output_is_empty and (
        not os.path.exists(args.output_directory) or not os.listdir(args.output_directory)
    ):
        raise ValueError("The software produced an empty output directory, it likely failed?")

    if args.push.lower() == "true":
        print(
            f"""
######################################### Review the Outputs of your Software ##########################################
# Your software produced the following outputs in {args.output_directory}.
# Please shortly review them before we push your software.
########################################################################################################################
"""
        )
        if not os.path.exists(args.output_directory) or not os.listdir(args.output_directory):
            print("Your software did not produce any output, please review the logs above.")
        else:
            for f in os.listdir(args.output_directory):
                print(f' - {f}: {os.path.getsize(args.output_directory + "/" + f)} bytes')

        if not args.fail_if_output_is_empty:
            continue_user = input("Are the outputs correct and should I push the software to TIRA? (y/N) ").lower()

            if not continue_user or continue_user.lower() not in ["y", "yes"]:
                print("You did not specify yes, I will not push the software.")
                return

        image = push_image(client, args.image, args.tira_task_id, args.tira_vm_id)

        print("Upload TIRA_SOFTWARE")
        prev_stages = []
        for i in args.previous_stages:
            prev_stages += [
                str(
                    i["job_id"]["software_id"]
                    if i["job_id"]["software_id"]
                    else ("upload-" + str(i["job_id"]["upload_id"]))
                )
            ]

        tira = RestClient(api_key=args.tira_client_token, api_user_name=args.tira_client_user)
        tira.add_docker_software(
            image,
            args.command,
            args.tira_vm_id,
            args.tira_task_id,
            args.tira_code_repository_id,
            dict(os.environ),
            prev_stages,
            args.mount_hf_model,
        )
