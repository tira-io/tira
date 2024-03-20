#!/usr/bin/env python
import argparse
from tira.local_client import Client
from .rest_api_client import Client as RestClient
from tira.local_execution_integration import LocalExecutionIntegration
import os
import shutil
import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .tira_client import TiraClient


def setup_upload_run_command(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('runfile', type=argparse.FileType('rb'), help="Path to the runfile to be uploaded")
    parser.add_argument('--dataset-id', required=True, type=str)
    parser.add_argument('--task-id', required=False, default=os.environ.get('TIRA_TASK_ID'), type=str)
    parser.add_argument('--vm-id', required=False, default=os.environ.get('TIRA_VM_ID'), type=str)
    parser.add_argument('--upload-group', required=True, type=str)

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
    success = tira.upload_run(task_id=args.task_id, vm_id=args.vm_id, dataset_id=args.dataset_id, upload_id=upload_id, filestream=args.runfile)
    return 0 if success else 1


def parse_args():
    parser = argparse.ArgumentParser(prog='tira-run')
    parser.add_argument('--input-directory', required=False, default=str(os.path.abspath(".")))
    parser.add_argument('--input-dataset', required=False, default=None)
    parser.add_argument('--input-run', required=False, default=None)
    # Not required if the subcommand "tira-run submit" is used. FIXME: the arguments in this group should probably be subcommands
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--image')
    group.add_argument('--approach')
    group.add_argument('--export-dataset', required=False, default=None, type=str)
    group.add_argument('--export-approach-output', nargs='*', required=False, default=None, type=str)
    group.add_argument('--export-submission-from-jupyter-notebook', required=False, default=None, type=str)
    group.add_argument('--export-submission-environment', nargs='*', required=False, default=None, type=str)
    parser.add_argument('--command', required=False)
    parser.add_argument('--verbose', required=False, default=False, type=bool)
    parser.add_argument('--evaluate', required=False, default=False, type=bool)
    parser.add_argument('--evaluation-directory', required=False, default=str(os.path.abspath("tira-evaluation")))
    parser.add_argument('--dry-run', required=False, default=False, type=bool)
    parser.add_argument('--dataset-for-export-approach-output', required=False, default=False, type=str)
    parser.add_argument('-v', action='append', default=None, help='Additional volume mounts as <host-path>:<container-path>:<read-write-mode>', required=False)
    parser.add_argument('--allow-network', required=False, default=False, type=bool, help='Is the network available during the execution? (Default = False to improve reproducibility, containers that import ir-datasets can have access to the network, they can be tested with setting allow-network to true.)')
    parser.add_argument('--output-directory', required=False, default=str(os.path.abspath("tira-output")))

    parser.add_argument('--push', required=False, default='false')
    parser.add_argument('--tira-docker-registry-token', required=False, default=os.environ.get('TIRA_DOCKER_REGISTRY_TOKEN'))
    parser.add_argument('--tira-docker-registry-user', required=False, default=os.environ.get('TIRA_DOCKER_REGISTRY_USER'))
    parser.add_argument('--tira-client-token', required=False, default=os.environ.get('TIRA_CLIENT_TOKEN'))
    parser.add_argument('--tira-client-user', required=False, default=os.environ.get('TIRA_CLIENT_USER'))
    parser.add_argument('--tira-vm-id', required=False, default=os.environ.get('TIRA_VM_ID'))
    parser.add_argument('--tira-task-id', required=False, default=os.environ.get('TIRA_TASK_ID'))
    parser.add_argument('--tira-code-repository-id', required=False, default=os.environ.get('TIRA_CODE_REPOSITORY_ID'))
    parser.add_argument('--fail-if-output-is-empty', required=False, default=False, action='store_true', help='After the execution of the software, fail if the output directory is empty.')

    subparsers = parser.add_subparsers()
    setup_upload_run_command(subparsers.add_parser('upload', help="For uploading runs"))

    args = parser.parse_args()
    if args.export_submission_from_jupyter_notebook:
        return args
    
    if args.export_submission_environment:
        return args

    if (args.image is None) == (args.approach is None) == (args.export_dataset):
        parser.error('You have to exclusively use either --approach or --image.')
    if (args.image is None) != (args.command is None):
        args.command = LocalExecutionIntegration().extract_entrypoint(args.image)

        if args.command is not None:
            print(f'Use command from Docker image "{args.command}".')
        else:
            parser.error('The options --image and --command have to be used together.')

    if args.push.lower() == 'true':
        if not args.tira_docker_registry_token:
            parser.error('The option --tira-docker-registry-token (or environment variable TIRA_DOCKER_REGISTRY_TOKEN) is required when --push is active.')

        if not args.tira_docker_registry_user:
            parser.error('The option --tira-docker-registry-user (or environment variable TIRA_DOCKER_REGISTRY_USER) is required when --push is active.')

        if not args.tira_client_token:
            parser.error('The option --tira-client-token (or environment variable TIRA_CLIENT_TOKEN) is required when --push is active.')

        if not args.tira_vm_id:
            parser.error('The option --tira-vm-id (or environment variable TIRA_VM_ID) is required when --push is active.')

        if not args.tira_task_id:
            parser.error('The option --tira-task-id (or environment variable TIRA_TASK_ID) is required when --push is active.')
        if not args.tira_client_user:
            parser.error('The option --tira-client-user (or environment variable TIRA_CLIENT_USER) is required when --push is active.')

    return args


def main():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    client: "TiraClient" = Client()

    # Subcommands store their executable into args.executable which takes the parsed arguments and returns an integer
    if hasattr(args, 'executable') and args.executable is not None:
        exit(args.executable(args))

    if args.export_submission_from_jupyter_notebook:
        ret = LocalExecutionIntegration().export_submission_from_jupyter_notebook(args.export_submission_from_jupyter_notebook)
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
            print('Please specify the dataset for which the approach outputs should be exported via --dataset-for-export-approach-output')
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

    input_dir = args.input_directory
    evaluate = False
    if args.input_dataset and 'none' != args.input_dataset.lower():
        if len(args.input_dataset.split('/')) != 2:
            print(f'Please pass arguments as: --input-dataset <task>/<tira-dataset>. Got {args.input_dataset}')
            return

        task, dataset = args.input_dataset.split('/')
        tira = RestClient()
        print(f'Ensure that the input dataset {dataset} is available.')
        input_dir = tira.download_dataset(task, dataset)
        print(f'Done: Dataset {dataset} is available locally.')

        if args.input_run and 'none' != args.input_run.lower():
            print(f'Ensure that the input run {args.input_run} is available.')
            args.input_run = tira.get_run_output(args.input_run, dataset, True)
            print('Done: input run is available locally.')

        if args.evaluate:
            print(f'Ensure that the evaluation truth for dataset {dataset} is available.')
            evaluate = tira.get_configuration_of_evaluation(task, dataset)
            evaluate['truth_directory'] = tira.download_dataset(task, dataset, truth_dataset=True)
            print(f'Done: Evaluation truth for dataset {dataset} is available.')

    print(f'''
########################################### TIRA RUN CONFIGURATION ###########################################
# image=${args.image}
# command=${args.command}
##############################################################################################################
''')
    client.local_execution.run(identifier=args.approach, image=args.image, command=args.command, input_dir=input_dir, output_dir=args.output_directory, dry_run=args.dry_run, allow_network=args.allow_network, input_run=args.input_run, additional_volumes=args.v, evaluate=evaluate, eval_dir=args.evaluation_directory)

    if args.fail_if_output_is_empty and (not os.path.exists(args.output_directory) or not os.listdir(args.output_directory)):
        raise ValueError('The software produced an empty output directory, it likely failed?')

    if args.push.lower() == 'true':
        print('Push Docker image')
        client.local_execution.push_image(args.image, args.tira_docker_registry_user, args.tira_docker_registry_token)
        print('Upload TIRA_SOFTWARE')
        tira = RestClient(api_key=args.tira_client_token, api_user_name=args.tira_client_user)
        tira.add_docker_software(args.image, args.command, args.tira_vm_id, args.tira_task_id, args.tira_code_repository_id, dict(os.environ))
