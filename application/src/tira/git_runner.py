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
    from tira.tira_model import model
    ret = []
    for git_integration in model.all_git_integrations(return_dict=True):
        try:
            ret += [get_git_runner(git_integration)]
        except Exception as e:
            print(f'Could not load git integration: {git_integration}. Skip')
            logger.warn(f'Could not load git integration: {git_integration}. Skip')

    return ret


def check_that_git_integration_is_valid(namespace_url, private_token):
    import tira.model as modeldb
    from tira.tira_model import model
    git_integration = {'namespace_url': namespace_url, 'private_token': private_token}
    
    try:
        git_integration = modeldb.GitIntegration.objects.get(namespace_url=namespace_url)
        git_integration = model._git_integration_to_dict(git_integration)
        git_integration['private_token'] = private_token
    except:
        pass
    
    try:
        git_runner = get_git_runner(git_integration)
        
        if not git_runner:
            return (False, 'Invalid Parameters.')
        
        all_user_repositories = git_runner.all_user_repositories()
        if all_user_repositories is not None and len(all_user_repositories) >= 0:
            return (True, 'The git credentials are valid (tested by counting repositories).')
        else:
            return (False, 'The git credentials are not valid (tested by counting repositories).')
    except Exception as e:
        return (False, f'The Git credentials are not valid: {e}')


def get_git_runner(git_integration):
    from tira.git_runner_integration import GitLabRunner, GithubRunner

    if not git_integration or 'namespace_url' not in git_integration:
        return None

    if 'github.com' in git_integration['namespace_url']:
        return GithubRunner(git_integration['private_token'])
    else:
        return GitLabRunner(
            git_integration['private_token'], git_integration['host'], git_integration['user_name'],
            git_integration['user_password'], git_integration['gitlab_repository_namespace_id'],
            git_integration['image_registry_prefix'], git_integration['user_repository_branch']
        )

def get_git_runner_for_software_integration():
    from tira.git_runner_integration import GithubRunner
    return GithubRunner(settings.GITHUB_TOKEN)

