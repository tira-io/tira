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
import string
import json
from slugify import slugify
from tqdm import tqdm
from glob import glob
import subprocess
import markdown

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
        __ensure_branch_is_main(repo)
        repo.index.add(['README.md', '.gitlab-ci.yml', 'tira'])
        repo.index.commit('Initial commit')
        repo.remote().push(settings.GIT_USER_REPOSITORY_BRANCH, o='ci.skip')

    logger.info(f"Created task repository for task {task_id} with new id {project.id}")
    return project.id


def __ensure_branch_is_main(repo):
    try:
        # for some git versions we need to manually switch, may fail if the branch is already correct
        repo.git.checkout('-b', settings.GIT_USER_REPOSITORY_BRANCH)
    except:
        pass

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
        create_user_repository(user)
        return ret

    for registry_repository in repo.repositories.list():
        for registry in registry_repository.manager.list():
            for image in registry.tags.list(get_all=True):
                ret += [image.location]
    
    return sorted(list(set(ret)))


def help_on_uploading_docker_image(user):
    repo = __existing_repository('tira-user-' + user)
    if not repo:
        create_user_repository(user)
        return help_on_uploading_docker_image(user)
    
    # Hacky at the moment
    ret = repo.files.get('README.md', ref='main').decode().decode('UTF-8').split('## Create an docker image')[1]
    ret = '## Create an docker image\n\n' + ret
    
    return markdown.markdown(ret)


def add_new_tag_to_docker_image_repository(repository_name, old_tag, new_tag):
    """
    Background for the implementation:
    https://dille.name/blog/2018/09/20/how-to-tag-docker-images-without-pulling-them/
    https://gitlab.com/gitlab-org/gitlab/-/issues/23156
    """
    original_repository_name = repository_name
    repository_name = repository_name.split(settings.GIT_CONTAINER_REGISTRY_HOST + '/')[-1]
    
    token = requests.get(f'https://{settings.GIT_CI_SERVER_HOST}:{settings.GIT_PRIVATE_TOKEN}@git.webis.de/jwt/auth?client_id=docker&offline_token=true&service=container_registry&scope=repository:{repository_name}:push,pull')
    
    if not token.ok:
        raise ValueError(token.content.decode('UTF-8'))
    
    token = json.loads(token.content.decode('UTF-8'))['token']
    headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
               'Content-Type': 'application/vnd.docker.distribution.manifest.v2+json',
               'Authorization': 'Bearer ' + token}
    
    manifest = requests.get(f'https://registry.webis.de/v2/{repository_name}/manifests/{old_tag}', headers=headers)

    if not manifest.ok:
        raise ValueError('-->' + manifest.content.decode('UTF-8'))
    manifest = manifest.content.decode('UTF-8')

    manifest = requests.put(f'https://registry.webis.de/v2/{repository_name}/manifests/{new_tag}', headers=headers, data=manifest)

    if not manifest.ok:
        raise ValueError(manifest.content.decode('UTF-8'))

    return original_repository_name + ':' + new_tag


def archive_repository(repo_name):
    repo = __existing_repository(repo_name)
    if not repo:
        print(f'Repository not found "{repo_name}".')
        return

    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f'Clone repository {repo.name}')
        repo = Repo.clone_from(repo_url(repo.id), tmp_dir, branch='main')
        Path(tmp_dir + '/docker-softwares').mkdir(parents=True, exist_ok=True)
        
        print("Export docker images:")
        downloaded_images = set()
        for job_file in tqdm(sorted(list(glob(tmp_dir + '/*/*/*/job-executed-on*.txt')))):
            job = [i.split('=') for i in open(job_file, 'r')]
            job = {k:v for k,v in job}
            image = job['TIRA_IMAGE_TO_EXECUTE'].strip()

            if image in downloaded_images:
                continue

            downloaded_images.add(image)
            image_name = (slugify(image) + '.tar').replace('/', '-')

            cmd = ['skopeo', 'copy', '--src-creds', 
                   f'{settings.GIT_CI_SERVER_HOST}:{settings.GIT_PRIVATE_TOKEN}',
                   f'docker://{image}', f'docker-archive:{tmp_dir}/docker-softwares/{image_name}']

            subprocess.check_output(cmd)

        shutil.make_archive(repo_name, 'zip', tmp_dir)
        print(f'The repository is archived into {repo_name}.zip')


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
                                        'echo \'No software to execute. Only evaluation\'',
                                        '-1', list(settings.GIT_CI_AVAILABLE_RESOURCES.keys())[0])

    t = TransactionLog.objects.get(transaction_id=transaction_id)
    _ = EvaluationLog.objects.update_or_create(vm_id=vm_id, run_id=run_id, running_on=vm_id,
                                               transaction=t)

    return transaction_id


def run_docker_software_with_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                                       git_runner_command, git_repository_id, evaluator_id,
                                       user_image_to_execute, user_command_to_execute, tira_software_id, resources):
    msg = f"start run_docker_image with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
    transaction_id = start_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                       git_runner_command, git_repository_id, evaluator_id,
                       user_image_to_execute, user_command_to_execute, tira_software_id, resources)

    # TODO: add transaction to log

    return transaction_id


def start_git_workflow(task_id, dataset_id, vm_id, run_id, git_runner_image,
                       git_runner_command, git_repository_id, evaluator_id,
                       user_image_to_execute, user_command_to_execute, tira_software_id, resources):
    msg = f"start git-workflow with git: {task_id} - {dataset_id} - {vm_id} - {run_id}"
    transaction_id = new_transaction(msg, in_grpc=False)
    logger.info(msg)

    identifier = f"eval---{dataset_id}---{vm_id}---{run_id}---started-{str(dt.now().strftime('%Y-%m-%d-%H-%M-%S'))}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = __clone_repository_and_create_new_branch(repo_url(git_repository_id), identifier, tmp_dir)

        __write_metadata_for_ci_job_to_repository(tmp_dir, task_id, transaction_id, dataset_id, vm_id, run_id,
                                                  identifier, git_runner_image, git_runner_command, evaluator_id,
                                                  user_image_to_execute, user_command_to_execute, tira_software_id, resources)

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
                                                      user_image_to_execute, user_command_to_execute, tira_software_id,
                                                      resources):
    job_dir = Path(tmp_dir) / dataset_id / vm_id / run_id
    job_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
            # The pipeline executed first a pseudo software so the following three values are
            # only dummy values so that the software runs successful.
            'TIRA_IMAGE_TO_EXECUTE': user_image_to_execute,
            'TIRA_VM_ID': vm_id,
            'TIRA_COMMAND_TO_EXECUTE': user_command_to_execute,
            'TIRA_SOFTWARE_ID': tira_software_id,
            'TIRA_DATASET_ID': dataset_id,
            'TIRA_RUN_ID': run_id,
            'TIRA_CPU_COUNT': str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]['cores']),
            'TIRA_MEMORY_IN_GIBIBYTE': str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]['ram']),
            'TIRA_DATASET_TYPE': 'training' if 'training' in dataset_id else 'test',

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
        __ensure_branch_is_main(repo)
        repo.index.add(['README.md'])
        repo.index.commit('Initial commit')
        repo.remote().push(settings.GIT_USER_REPOSITORY_BRANCH)


def clean_job_suffix(ret):
    if "[32;1m$ env|grep 'TIRA' > task.env" in ret:
        ret = ret.split("[32;1m$ env|grep 'TIRA' > task.env")[0]
    if "section_end:" in ret:
        ret = ret.split("section_end:")[0]

    return ret.strip()


def clean_job_output(ret):
    ret = ''.join(filter(lambda x: x in string.printable, ret.strip()))
    if '$ eval "${TIRA_COMMAND_TO_EXECUTE}"[0;m' in ret:
        return clean_job_suffix(ret.split('$ eval "${TIRA_COMMAND_TO_EXECUTE}"[0;m')[1])
    elif '$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m' in ret:
        return clean_job_suffix(ret.split('$ eval "${TIRA_EVALUATION_COMMAND_TO_EXECUTE}"[0;m')[1])
    else:
        # Job not jet started.
        return ''


def stop_job_and_clean_up(git_repository_id, user_id, run_id):
    gl = gitlab_client()
    gl_project = gl.projects.get(int(git_repository_id))
    
    for pipeline in yield_all_running_pipelines(git_repository_id, user_id):
        if run_id == pipeline['run_id']:
            branch = pipeline['branch'] if 'branch' in pipeline else pipeline['pipeline'].ref
            if ('---' + user_id + '---') not in branch:
                continue
            if ('---' + run_id + '---') not in branch:
                continue

            if 'pipeline' in pipeline:
                pipeline['pipeline'].cancel()
            gl_project.branches.delete(branch)


def yield_all_running_pipelines(git_repository_id, user_id):
    gl = gitlab_client()
    gl_project = gl.projects.get(int(git_repository_id))
    already_covered_run_ids = set()
    for status in ['scheduled', 'running', 'pending', 'created', 'waiting_for_resource', 'preparing']:
        for pipeline in gl_project.pipelines.list(status=status):
            user_software_job = None
            evaluation_job = None
            for job in pipeline.jobs.list():
                if 'run-user-software' == job.name:
                    user_software_job = job
                if 'evaluate-software-result' == job.name:
                    evaluation_job = job

            p = (pipeline.ref + '---started-').split('---started-')[0]
            if ('---' + user_id + '---') not in p:
                continue
            
            execution = {'scheduling': 'running', 'execution': 'pending', 'evaluation': 'pending'}
            if user_software_job.status == 'running':
                execution = {'scheduling': 'done', 'execution': 'running', 'evaluation': 'pending'}
            elif user_software_job.status != 'created':
                execution = {'scheduling': 'done', 'execution': 'done', 'evaluation': 'running'}

            stdout = 'Output for runs on the test-data is hidden.'
            if ('-training---' + user_id + '---') in p:
                try:
                    stdout = ''
                    user_software_job = gl_project.jobs.get(user_software_job.id)
                    stdout = clean_job_output(user_software_job.trace().decode('UTF-8'))
                except:
                    # Job is not started or similar
                    pass
            run_id = p.split('---')[-1]
            
            already_covered_run_ids.add(run_id)
            yield {'run_id': run_id, 'execution': execution, 'stdOutput': stdout, 'started_at': p.split('---')[-1], 'pipeline': pipeline}
    yield from yield_all_failed_pipelines(gl_project, user_id, already_covered_run_ids)


def yield_all_failed_pipelines(gl_project, user_id, already_covered_run_ids):
    for branch in gl_project.branches.list():
        branch = branch.name
        p = (branch + '---started-').split('---started-')[0]
        if ('---' + user_id + '---') not in p:
            continue
        run_id = p.split('---')[-1]
        
        if run_id in already_covered_run_ids:
            continue
        
        yield {'run_id': run_id, 'execution': {'scheduling': 'failed', 'execution': 'failed', 'evaluation': 'failed'}, 'stdOutput': 'Job did not run.', 'started_at': p.split('---')[-1], 'branch': branch}

