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


def get_git_runner(git_integration):
    from tira.git_runner_integration import GitLabRunner, GithubRunner
    if 'github.com' in git_integration['namespace_url']:
        return GithubRunner()
    else:
        return GitLabRunner(
            git_integration['private_token'], git_integration['host'], git_integration['user_name'],
            git_integration['user_password'], git_integration['gitlab_repository_namespace_id'],
            git_integration['image_registry_prefix'], git_integration['user_repository_branch']
        )

