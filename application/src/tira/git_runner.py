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
from itertools import chain

from copy import deepcopy
from tira.grpc_client import new_transaction
from tira.model import TransactionLog, EvaluationLog
from .proto import tira_host_pb2, tira_host_pb2_grpc
import requests

logger = logging.getLogger('tira')


def all_git_runners():


def get_git_runner(git_integration):
    from tira.git_runner_integration import GitLabRunner, GithubRunner
    if 'github.com' in git_integration.namespace_url:
        return GithubRunner()
    else:
        return GithubRunner(
            git_integration.private_token, git_integration.host, git_integration.user_name,
            git_integration.user_password, git_integration.gitlab_repository_namespace_id,
            git_integration.image_registry_prefix, git_integration.user_repository_branch
        )



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


def docker_images_in_user_repository(user, cache=None, force_cache_refresh=False):
    cache_key = 'docker-images-in-user-repository-tira-user-' + user
    if cache:
        ret = cache.get(cache_key)        
        if ret is not None and not force_cache_refresh:
            return ret

    ret = []
    repo = __existing_repository('tira-user-' + user)
    if not repo:
        create_user_repository(user)
        return ret
    covered_images = set()
    for registry_repository in repo.repositories.list():
        for registry in registry_repository.manager.list():
            for image in registry.tags.list(get_all=True):
                if image.location in covered_images:
                    continue
                covered_images.add(image.location)
                image_manifest = get_manifest_of_docker_image_image_repository(image.location.split(':')[0], image.location.split(':')[1], cache, force_cache_refresh)
                
                ret += [{'image': image.location,
                         'architecture': image_manifest['architecture'],
                         'created': image_manifest['created'].split('.')[0],
                         'size': image_manifest['size'],
                         'digest': image_manifest['digest']
                       }]
    
    ret = sorted(list(ret), key=lambda i: i['image'])
    
    if cache:
        logger.info(f"Cache refreshed for key {cache_key} ...")
        cache.set(cache_key, ret)

    return ret


def help_on_uploading_docker_image(user, cache=None, force_cache_refresh=False):
    cache_key = 'help-on-uploading-docker-image-tira-user-' + user
    if cache:
        ret = cache.get(cache_key)        
        if ret is not None and not force_cache_refresh:
            return ret

    repo = __existing_repository('tira-user-' + user)
    if not repo:
        create_user_repository(user)
        return help_on_uploading_docker_image(user, cache)
    
    # Hacky at the moment
    ret = repo.files.get('README.md', ref='main').decode().decode('UTF-8').split('## Create an docker image')[1]
    ret = '## Create an docker image\n\n' + ret
    
    ret = markdown.markdown(ret)
    
    if cache:
        logger.info(f"Cache refreshed for key {cache_key} ...")
        cache.set(cache_key, ret)
    
    return ret


def convert_size(size_bytes):
    import math
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
   
    return f"{s} {size_name[i]}"


def get_manifest_of_docker_image_image_repository(repository_name, tag, cache, force_cache_refresh):
    """
    Background for the implementation:
    https://dille.name/blog/2018/09/20/how-to-tag-docker-images-without-pulling-them/
    https://gitlab.com/gitlab-org/gitlab/-/issues/23156
    """
    original_repository_name = repository_name
    repository_name = repository_name.split(settings.GIT_CONTAINER_REGISTRY_HOST + '/')[-1]
    
    cache_key = f'docker-manifest-for-repo-{repository_name}-{tag}'
    if cache:
        ret = cache.get(cache_key)        
        if ret is not None:
            return ret
    
    try:
        token = requests.get(f'https://{settings.GIT_CI_SERVER_HOST}:{settings.GIT_PRIVATE_TOKEN}@git.webis.de/jwt/auth?client_id=docker&offline_token=true&service=container_registry&scope=repository:{repository_name}:push,pull,blob,upload')

        if not token.ok:
            raise ValueError(token.content.decode('UTF-8'))

        token = json.loads(token.content.decode('UTF-8'))['token']
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
                   'Content-Type': 'application/vnd.docker.distribution.manifest.v2+json',
                   'Authorization': 'Bearer ' + token}

        manifest = requests.get(f'https://registry.webis.de/v2/{repository_name}/manifests/{tag}', headers=headers)

        if not manifest.ok:
            raise ValueError('-->' + manifest.content.decode('UTF-8'))
    
        image_metadata = json.loads(manifest.content.decode('UTF-8'))
        size = convert_size(image_metadata['config']['size'] + sum([i['size'] for i in image_metadata['layers']]))
    
        image_config = requests.get(f'https://registry.webis.de/v2/{repository_name}/blobs/{image_metadata["config"]["digest"]}', headers=headers)

        if not image_config.ok:
            raise ValueError('-->' + image_config.content.decode('UTF-8'))
    
        image_config = json.loads(image_config.content.decode('UTF-8'))

        ret = {
            'architecture': image_config['architecture'],
            'created': image_config['created'],
            'size': size,
            'digest': image_metadata["config"]["digest"].split(':')[-1][:12]
        }
    except Exception as e:
        logger.warn('Exception during loading of metadata for docker image', e)
        ret = {
            'architecture': 'Loading...',
            'created': 'Loading...',
            'size': 'Loading...',
            'digest': 'Loading...'
        }
    
    if cache:
        logger.info(f"Cache refreshed for key {cache_key} ...")
        cache.set(cache_key, ret)
    
    return ret


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


def archive_repository(repo_name, persist_all_images=True):
    from tira.tira_model import get_docker_software, get_docker_softwares_with_runs, get_dataset
    from django.template.loader import render_to_string
    repo = __existing_repository(repo_name)
    if not repo:
        print(f'Repository not found "{repo_name}".')
        return

    softwares = set()
    evaluations = set()
    datasets = {}

    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f'Clone repository {repo.name}. Working in {tmp_dir}')
        repo = Repo.clone_from(repo_url(repo.id), tmp_dir, branch='main')
        Path(tmp_dir + '/docker-softwares').mkdir(parents=True, exist_ok=True)
        
        print("Export docker images:")
        downloaded_images = set()
        for job_file in tqdm(sorted(list(glob(tmp_dir + '/*/*/*/job-executed-on*.txt')))):
            job = [i.split('=') for i in open(job_file, 'r')]
            job = {k.strip():v.strip() for k,v in job}
            image = job['TIRA_IMAGE_TO_EXECUTE'].strip()
            if settings.GIT_REGISTRY_PREFIX.lower() not in image.lower():
                continue
            
            datasets[job['TIRA_DATASET_ID']] = get_dataset(job['TIRA_DATASET_ID'])
            
            try:
                software_metadata = get_docker_software(int(job["TIRA_SOFTWARE_ID"].replace('docker-software-', '')))
                runs = get_docker_softwares_with_runs(job["TIRA_TASK_ID"], job["TIRA_VM_ID"])
            except:
                continue
            runs = [i for i in runs if int(i['docker_software_id']) == (int(job["TIRA_SOFTWARE_ID"].replace('docker-software-', '')))]
            runs = list(chain(*[i['runs'] for i in runs]))
            runs = [i for i in runs if (i['input_run_id'] == job['TIRA_RUN_ID'] or i['run_id'] == job['TIRA_RUN_ID'])]
            
            for run in runs:
                result_out_dir = (Path(job_file.split('/job-executed-on')[0]) / ('evaluation' if run['is_evaluation'] else 'run'))
                result_out_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(Path(settings.TIRA_ROOT)/ 'data' / 'runs' / job['TIRA_DATASET_ID'] / job['TIRA_VM_ID'] / run['run_id'], result_out_dir / run['run_id'])

            image_name = (slugify(image) + '.tar').replace('/', '-')

            cmd = ['skopeo', 'copy', '--src-creds', 
                   f'{settings.GIT_CI_SERVER_HOST}:{settings.GIT_PRIVATE_TOKEN}',
                   f'docker://{image}', f'docker-archive:{tmp_dir}/docker-softwares/{image_name}']

            if persist_all_images and image not in downloaded_images:
                subprocess.check_output(cmd)

            dockerhub_image = f'docker.io/webis/{job["TIRA_TASK_ID"]}-submissions:' + (image_name.split('-tira-user-')[1]).replace('.tar', '').strip()
            
            cmd = ['skopeo', 'copy', f'docker-archive:{tmp_dir}/docker-softwares/{image_name}', f'docker://{dockerhub_image}']
            if persist_all_images and image not in downloaded_images:
                subprocess.check_output(cmd)

            downloaded_images.add(image)
            softwares.add(json.dumps({
                "TIRA_IMAGE_TO_EXECUTE": dockerhub_image,
                "TIRA_VM_ID": job["TIRA_VM_ID"],
                "TIRA_COMMAND_TO_EXECUTE": job["TIRA_COMMAND_TO_EXECUTE"],
                "TIRA_TASK_ID": job["TIRA_TASK_ID"],
                "TIRA_SOFTWARE_ID": job["TIRA_SOFTWARE_ID"],
                "TIRA_SOFTWARE_NAME": software_metadata['display_name']
            }))
            
            evaluations.add(json.dumps({
                "TIRA_DATASET_ID": job['TIRA_DATASET_ID'].strip(),
                "TIRA_EVALUATION_IMAGE_TO_EXECUTE": job["TIRA_EVALUATION_IMAGE_TO_EXECUTE"].strip(),
                "TIRA_EVALUATION_COMMAND_TO_EXECUTE": job["TIRA_EVALUATION_COMMAND_TO_EXECUTE"].strip()
            }))
        
        (Path(tmp_dir) / '.tira').mkdir(parents=True, exist_ok=True)
        open((Path(tmp_dir) / '.tira' / 'submitted-software.jsonl').absolute(), 'w').write('\n'.join(softwares))
        open((Path(tmp_dir) / '.tira' / 'evaluators.jsonl').absolute(), 'w').write('\n'.join(evaluations))
        open((Path(tmp_dir) / 'tira.py').absolute(), 'w').write(render_to_string('tira/tira_git_cmd.py', context={}))
        open((Path(tmp_dir) / 'requirements.txt').absolute(), 'w').write('docker==5.0.3\npandas\njupyterlab')
        open((Path(tmp_dir) / 'Makefile').absolute(), 'w').write(render_to_string('tira/tira_git_makefile', context={}))
        open((Path(tmp_dir) / 'Tutorial.ipynb').absolute(), 'w').write(render_to_string('tira/tira_git_tutorial.ipynb', context={}))
        #open((Path(tmp_dir) / 'README.md').absolute(), 'a+').write(render_to_string('tira/tira_git_cmd.py', context={}))

        logger.info(f'Archive datasets')
        for dataset_name, dataset_definition in datasets.items():
            if 'is_confidential' in dataset_definition and not dataset_definition['is_confidential']:
                for i in ['training-datasets', 'training-datasets-truth']:
                    shutil.copytree(Path(settings.TIRA_ROOT)/ 'data' / 'datasets' / i / job['TIRA_TASK_ID'] / dataset_name, Path(tmp_dir) / dataset_name / i)    
        
        logger.info(f'Archive repository into {repo_name}.zip')
        shutil.make_archive(repo_name, 'zip', tmp_dir)
        logger.info(f'The repository is archived into {repo_name}.zip')


def all_user_repositories():
    ret = []
    for potential_existing_projects in gitlab_client().projects.list(search='tira-user-'):
        if 'tira-user-' in potential_existing_projects.name and int(potential_existing_projects.namespace['id']) == int(settings.GIT_USER_REPOSITORY_NAMESPACE_ID):
            ret += [potential_existing_projects.name]
    return set(ret)


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

        __commit_and_push(repo, dataset_id, vm_id, run_id, identifier, git_repository_id, resources)

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
            'TIRA_GPU': str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]['gpu']),
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


def __commit_and_push(repo, dataset_id, vm_id, run_id, identifier, git_repository_id, resources):
    repo.index.add([str(Path(dataset_id) / vm_id / run_id / 'job-to-execute.txt')])
    repo.index.commit("Evaluate software: " + identifier)
    gpu_resources = str(settings.GIT_CI_AVAILABLE_RESOURCES[resources]['gpu']).strip()

    if gpu_resources == '0':
        repo.remote().push(identifier)
    else:
        repo.remote().push(identifier, **{'o': 'ci.skip'})

        gl = gitlab_client()
        gl_project = gl.projects.get(int(git_repository_id))
        gl_project.pipelines.create({'ref': identifier, 'variables': [{'key': 'TIRA_GPU', 'value': gpu_resources}]})


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


def stop_job_and_clean_up(git_repository_id, user_id, run_id, cache=None):
    gl = gitlab_client()
    gl_project = gl.projects.get(int(git_repository_id))
    
    for pipeline in yield_all_running_pipelines(git_repository_id, user_id, cache, True):
        if run_id == pipeline['run_id']:
            branch = pipeline['branch'] if 'branch' in pipeline else pipeline['pipeline'].ref
            if ('---' + user_id + '---') not in branch:
                continue
            if ('---' + run_id + '---') not in branch:
                continue

            if 'pipeline' in pipeline:
                pipeline['pipeline'].cancel()
            gl_project.branches.delete(branch)


def yield_all_running_pipelines(git_repository_id, user_id, cache=None, force_cache_refresh=False):
    for pipeline in all_running_pipelines_for_repository(git_repository_id, cache, force_cache_refresh):
        pipeline = deepcopy(pipeline)

        if ('---' + user_id + '---') not in pipeline['pipeline_name']:
            continue

        if ('-training---' + user_id + '---') not in pipeline['pipeline_name']:
            pipeline['stdOutput'] = 'Output for runs on the test-data is hidden.'

        yield pipeline


def all_running_pipelines_for_repository(git_repository_id, cache=None, force_cache_refresh=False):
    cache_key = 'all-running-pipelines-repo-' + str(git_repository_id)
    if cache:
        try:
            ret = cache.get(cache_key)
            if ret is not None and not force_cache_refresh:
                logger.debug('get ret from cache', ret)
                return ret
        except ModuleNotFoundError as e:
            logger.exception(f"Could not find cache module {cache_key}.")

    ret = []
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
            
            execution = {'scheduling': 'running', 'execution': 'pending', 'evaluation': 'pending'}
            if user_software_job.status == 'running':
                execution = {'scheduling': 'done', 'execution': 'running', 'evaluation': 'pending'}
            elif user_software_job.status != 'created':
                execution = {'scheduling': 'done', 'execution': 'done', 'evaluation': 'running'}

            stdout = 'Output for runs on the test-data is hidden.'
            if '-training---' in p:
                try:
                    stdout = ''
                    user_software_job = gl_project.jobs.get(user_software_job.id)
                    stdout = clean_job_output(user_software_job.trace().decode('UTF-8'))
                except:
                    # Job is not started or similar
                    pass

            run_id = p.split('---')[-1]
            
            already_covered_run_ids.add(run_id)
            ret += [{
                'run_id': run_id,
                'execution': execution,
                'stdOutput': stdout,
                'started_at': p.split('---')[-1],
                'pipeline_name': p,
                'job_config': extract_job_configuration(gl_project, pipeline.ref),
                'pipeline': pipeline
            }]
            
    ret += __all_failed_pipelines_for_repository(gl_project, already_covered_run_ids)
    
    if cache:
        logger.info(f"Cache refreshed for key {cache_key} ...")
        cache.set(cache_key, ret)
    
    return ret


def extract_job_configuration(gl_project, branch):
    ret = {}
    
    try:
        for commit in gl_project.commits.list(ref_name=branch, page=0, per_page=3):
            if len(ret) > 0:
                break

            if branch in commit.title and 'Merge' not in commit.title:
                for diff_entry in commit.diff():
                    if len(ret) > 0:
                        break

                    if diff_entry['old_path'] == diff_entry['new_path'] and diff_entry['new_path'].endswith('/job-to-execute.txt'):
                        diff_entry = diff_entry['diff'].replace('\n+', '\n').split('\n')
                        ret = {i.split('=')[0].strip():i.split('=')[1].strip() for i in diff_entry if len(i.split('=')) == 2}
    except:
        pass

    try:
        from tira.tira_model import model
        software_from_db = model.get_docker_software(int(ret['TIRA_SOFTWARE_ID'].split('docker-software-')[-1]))
    except:
        software_from_db = {}

    return {
        'software_name': software_from_db.get('display_name', 'Loading...'),
        'image': software_from_db.get('user_image_name', 'Loading...'),
        'command': software_from_db.get('command', 'Loading...'),
        'cores': str(ret.get('TIRA_CPU_COUNT', 'Loading...')) + ' CPU Cores',
        'ram': str(ret.get('TIRA_MEMORY_IN_GIBIBYTE', 'Loading...')) + 'GB of RAM',
        'gpu': str(ret.get('TIRA_GPU', 'Loading...')) + ' GPUs',
        'dataset_type': ret.get('TIRA_DATASET_TYPE', 'Loading...'),
        'dataset': ret.get('TIRA_DATASET_ID', 'Loading...'),
        'software_id': ret.get('TIRA_SOFTWARE_ID', 'Loading...'),
        'task_id': ret.get('TIRA_TASK_ID', 'Loading...'),
    }


def __all_failed_pipelines_for_repository(gl_project, already_covered_run_ids):
    ret = []

    for branch in gl_project.branches.list():
        branch = branch.name
        p = (branch + '---started-').split('---started-')[0]
        run_id = p.split('---')[-1]
        
        if run_id in already_covered_run_ids:
            continue
        
        ret += [{'run_id': run_id, 'execution': {'scheduling': 'failed', 'execution': 'failed', 'evaluation': 'failed'}, 'pipeline_name': p, 'stdOutput': 'Job did not run. (Maybe it is still submitted to the cluster or failed to start. It might take up to 5 minutes to submit a Job to the cluster.)', 'started_at': p.split('---')[-1], 'branch': branch, 'job_config': extract_job_configuration(gl_project, branch)}]

    return ret

