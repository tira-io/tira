from django.conf import settings
from django.template.loader import render_to_string
from git import Repo
import tempfile
import logging
import gitlab
from pathlib import Path
import shutil
from datetime import datetime as dt
import os
import stat
import json

from tira.grpc_client import new_transaction
from tira.model import TransactionLog, EvaluationLog
from .proto import tira_host_pb2, tira_host_pb2_grpc
import requests

logger = logging.getLogger('tira')


def create_task_repository(task_id):
    logger.info(f"Creating task repository for task {task_id} ...")
    repo = __existing_repository(task_id)
    if repo:
        return int(repo.id)

    gitlab_ci = render_to_string('tira/git_task_repository_gitlab_ci.yml', context={})
    readme = render_to_string('tira/git_task_repository_readme.md', context={'task_name': task_id})
    project = gitlab_client().projects.create(
        {'name': task_id, 'namespace_id': str(int(settings.GIT_USER_REPOSITORY_NAMESPACE_ID)),
         "default_branch": settings.GIT_USER_REPOSITORY_BRANCH})
    tira_cmd_script = render_to_string('tira/tira_git_cmd.sh', context={'project_id': project.id,
                                                                        'ci_server_host': settings.GIT_CI_SERVER_HOST})

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Repo.init(tmp_dir)
        __write_to_file(str(tmp_dir) + '/.gitlab-ci.yml', gitlab_ci)
        __write_to_file(str(tmp_dir) + '/README.md', readme)
        __write_to_file(str(tmp_dir) + '/tira', tira_cmd_script)
        os.chmod(str(tmp_dir) + '/tira', os.stat(str(tmp_dir) + '/tira').st_mode | stat.S_IEXEC)

        repo.create_remote('origin', repo_url(project.id))
        repo.index.add(['README.md', '.gitlab-ci.yml', 'tira'])
        repo.index.commit('Initial commit')
        repo.remote().push(settings.GIT_USER_REPOSITORY_BRANCH, o='ci.skip')

    logger.info(f"Created task repository for task {task_id} with new id {project.id}")
    return project.id


def create_user_repository(repo):
    gl = gitlab_client()
    repo = 'tira-user-' + repo
    existing_repo = __existing_repository(repo)
    if existing_repo:
        return existing_repo.id
    
    project = gl.projects.create({'name': repo, 'namespace_id': str(int(settings.GIT_USER_REPOSITORY_NAMESPACE_ID)),
                                  "default_branch": settings.GIT_USER_REPOSITORY_BRANCH})
    token = project.access_tokens.create(
        {"name": repo, "scopes": ['read_registry', 'write_registry'], "access_level": 30})
    __initialize_user_repository(project.id, repo, token.token)
    
    return project.id


def docker_images_in_user_repository(user):
    ret = []
    repo = __existing_repository('tira-user-' + user)
    if not repo:
        return ret

    for registry_repository in repo.repositories.list():
        for registry in registry_repository.manager.list():
            for image in registry.tags.list():
                ret += [image.location]
    
    return ret


def add_new_tag_to_docker_image_repository(repository_name, old_tag, new_tag):
    """
    Background for the implementation:
    https://dille.name/blog/2018/09/20/how-to-tag-docker-images-without-pulling-them/
    https://gitlab.com/gitlab-org/gitlab/-/issues/23156
    """
    repository_name = repository_name.split(settings.GIT_CONTAINER_REGISTRY_HOST + '/')[-1]
    
    token = requests.get(f'https://{settings.GIT_CI_SERVER_HOST}:{settings.GIT_PRIVATE_TOKEN}@git.webis.de/jwt/auth?client_id=docker&offline_token=true&service=container_registry&scope=repository:{repository_name}:push,pull')
    
    if not token.ok:
        raise ValueError(token.content.decode('UTF-8'))
    
    token = json.loads(token.content.decode('UTF-8'))['token']
    headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
               'Content-Type': 'application/vnd.docker.distribution.manifest.v2+json',
               'Authorization':'Bearer ' + token}
    
    manifest = requests.get(f'https://registry.webis.de/v2/{repository_name}/manifests/{old_tag}', headers=headers)

    if not manifest.ok:
        raise ValueError('-->' + manifest.content.decode('UTF-8'))
    manifest = manifest.content.decode('UTF-8')

    manifest = requests.put(f'https://registry.webis.de/v2/{repository_name}/manifests/{new_tag}', headers=headers, data=manifest)

    if not manifest.ok:
        raise ValueError(manifest.content.decode('UTF-8'))

    print(repository_name + ':' + new_tag)
    

def __existing_repository(repo):
    for potential_existing_projects in gitlab_client().projects.list(search=repo):
        if potential_existing_projects.name == repo and int(potential_existing_projects.namespace['id']) == int(settings.GIT_USER_REPOSITORY_NAMESPACE_ID):
            return potential_existing_projects

def run_evaluate_with_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                                   git_runner_command, git_repository_id, evaluator_id):
    msg = f"start run_eval with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
    transaction_id = start_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                                        git_runner_command, git_repository_id, evaluator_id,
                                        'ubuntu:18.04',
                                        'echo \'No software to execute. Only evaluation\'')

    t = TransactionLog.objects.get(transaction_id=transaction_id)
    _ = EvaluationLog.objects.update_or_create(vm_id=vm_id, run_id=run_id, running_on=vm_id,
                                               transaction=t)

    return transaction_id


def run_docker_software_with_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                                       git_runner_command, git_repository_id, evaluator_id,
                                       user_image_to_execute, user_command_to_execute):
    msg = f"start run_docker_image with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
    raise ValueError('ToDo Add ')
    transaction_id = start_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                       git_runner_command, git_repository_id, evaluator_id,
                       user_image_to_execute, user_command_to_execute)

    return transaction_id


def start_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                       git_runner_command, git_repository_id, evaluator_id,
                       user_image_to_execute, user_command_to_execute):
    msg = f"start git-workflow with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
    transaction_id = new_transaction(msg, in_grpc=False)
    logger.info(msg)

    identifier = f"eval---{dataset_id}---{vm_id}---{run_id}---started-{str(dt.now().strftime('%Y-%m-%d-%H-%M-%S'))}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = __clone_repository_and_create_new_branch(repo_url(git_repository_id), identifier, tmp_dir)

        __write_metadata_for_ci_job_to_repository(tmp_dir, task_id, transaction_id, dataset_id, vm_id, run_id,
                                                  identifier, git_runner_image, git_runner_command, evaluator_id,
                                                  user_image_to_execute, user_command_to_execute)

        __commit_and_push(repo, dataset_id, vm_id, run_id, identifier)

        t = TransactionLog.objects.get(transaction_id=transaction_id)
        _ = EvaluationLog.objects.update_or_create(vm_id=vm_id, run_id=run_id, running_on=vm_id,
                                                   transaction=t)

    return transaction_id


def gitlab_client():
    return gitlab.Gitlab('https://' + settings.GIT_CI_SERVER_HOST, private_token=settings.GIT_PRIVATE_TOKEN)


def repo_url(git_repository_id):
    gl = gitlab_client()
    project = gl.projects.get(git_repository_id)
    
    return project.http_url_to_repo.replace(
        settings.GIT_CI_SERVER_HOST,
        settings.GIT_USER_NAME + ':' + settings.GIT_PRIVATE_TOKEN + '@' + settings.GIT_CI_SERVER_HOST
    )


def _dict_to_gitlab_key_value_file(d):
    return '\n'.join([(k + '=' + v).strip() for (k,v) in d.items()])


def __clone_repository_and_create_new_branch(repo_url, branch_name, directory):
    repo = Repo.clone_from(repo_url, directory, branch='main')
    repo.head.reference = repo.create_head(branch_name)
        
    return repo


def __write_metadata_for_ci_job_to_repository(tmp_dir, task_id, transaction_id, dataset_id, vm_id, run_id, identifier,
                                                      git_runner_image, git_runner_command, evaluator_id,
                                                      user_image_to_execute, user_command_to_execute):
    job_dir = Path(tmp_dir) / dataset_id / vm_id / run_id
    job_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
            # The pipeline executed first a pseudo software so the following three values are
            # only dummy values so that the software runs successful.
            'TIRA_IMAGE_TO_EXECUTE': user_image_to_execute,
            'TIRA_VM_ID': vm_id,
            'TIRA_COMMAND_TO_EXECUTE': user_command_to_execute,
            'TIRA_SOFTWARE_ID': '-1',
            'TIRA_DATASET_ID': dataset_id,
            'TIRA_RUN_ID': run_id,

            # The actual important stuff for the evaluator:
            'TIRA_TASK_ID': task_id,
            'TIRA_EVALUATOR_TRANSACTION_ID': transaction_id,
            'TIRA_GIT_ID': identifier,
            'TIRA_EVALUATION_IMAGE_TO_EXECUTE': git_runner_image,
            'TIRA_EVALUATION_COMMAND_TO_EXECUTE': git_runner_command,
            'TIRA_EVALUATION_SOFTWARE_ID': evaluator_id,
        }
    
    open(job_dir / 'job-to-execute.txt', 'w').write(_dict_to_gitlab_key_value_file(metadata))


def __commit_and_push(repo, dataset_id, vm_id, run_id, identifier):
    repo.index.add([str(Path(dataset_id) / vm_id / run_id / 'job-to-execute.txt')])
    repo.index.commit("Evaluate software: " + identifier)
    repo.remote().push(identifier)


def __write_to_file(file_name, content):
    open(file_name, 'w').write(content)


def __initialize_user_repository(git_repository_id, repo_name, token):
    project_readme = render_to_string('tira/git_user_repository_readme.md', context={
        'user_name': repo_name.replace('tira-user-', ''),
        'repo_name': repo_name,
        'token': token,
        'image_prefix': settings.GIT_REGISTRY_PREFIX +'/' + repo_name +'/'
    })

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Repo.init(tmp_dir)
        __write_to_file(str(tmp_dir) + '/README.md', project_readme)
        
        repo.create_remote('origin', repo_url(git_repository_id))
        repo.index.add(['README.md'])
        repo.index.commit('Initial commit')
        repo.remote().push(settings.GIT_USER_REPOSITORY_BRANCH)

