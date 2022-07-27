from django.conf import settings
from git import Repo
import tempfile
import logging
import gitlab
from pathlib import Path
import shutil
from datetime import datetime as dt

from tira.grpc_client import new_transaction

logger = logging.getLogger("tira")

def gitlab_client():
    return gitlab.Gitlab('https://' + settings.GIT_CI_SERVER_HOST, private_token=settings.GIT_PRIVATE_TOKEN)

def repo_url(git_repository_id):
    gl = gitlab_client()
    project = gl.projects.get(git_repository_id)
    
    return project.http_url_to_repo.replace(
        settings.GIT_CI_SERVER_HOST,
        settings.GIT_USER_NAME + ':' + settings.GIT_PRIVATE_TOKEN + '@' + settings.GIT_CI_SERVER_HOST
    )

def dict_to_gitlab_key_value_file(d):
    return '\n'.join([(k + '=' + v).strip() for (k,v) in d.items()])

def __clone_repository_and_create_new_branch(repo_url, branch_name, directory):
    repo = Repo.clone_from(, directory, branch='main')
    repo.head.reference = repo.create_head(branch_name)
        
    return repo

def __write_metadata_for_evaluation_job_to_repository(tmp_dir, task_id, transaction_id, dataset_id, vm_id, run_id, identifier):
    job_dir = Path(tmp_dir) / dataset_id / vm_id / run_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    with open(str(job_dir / 'job-to-execute.txt'), 'w') as f:
        f.write(dict_to_gitlab_key_value_file({
            # The pipeline executed first a pseudo software so the following three values are
            # only dummy values so that the software runs successful.
            'TIRA_IMAGE_TO_EXECUTE': 'ubuntu:18.04',
            'TIRA_COMMAND_TO_EXECUTE': 'echo \'No software to execute. Only evaluation\'',
            'TIRA_SOFTWARE_ID': '-1',

            # The actual important stuff for the evaluator:
            'TIRA_TASK_ID': task_id,
            'TIRA_EVALUATOR_TRANSACTION_ID': transaction_id,
            'TIRA_GIT_ID': identifier,
        }))

def __commit_and_push(repo, dataset_id, vm_id, run_id, identifier):
    repo.index.add([str(Path(dataset_id) / vm_id / run_id / 'job-to-execute.txt')])
    repo.index.commit("Evaluate software: " + identifier)
    repo.remote().push(identifier)

def run_evaluate_with_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                                   git_runner_command, git_repository_id):
    msg = f"start run_eval with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
    transaction_id = new_transaction(msg, in_grpc=False)
    logger.info(msg)

    identifier = 'eval---' + dataset_id + '---' + vm_id + '---' + run_id + '---started-' + str(dt.now().strftime('%Y-%m-%d-%H-%M-%S'))
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = __clone_repository_into_new_branch(repo_url(git_repository_id), identifier, tmp_dir)
        
        __write_metadata_for_evaluation_job_to_repository(tmp_dir, task_id, transaction_id, dataset_id, vm_id, run_id, identifier)
        
        __commit_and_push(repo, dataset_id, vm_id, run_id, identifier)

