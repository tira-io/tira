import os
import django
    
from django.conf import settings
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from tira.git_runner import create_user_repository, create_task_repository

grpc_port = settings.APPLICATION_GRPC_PORT
listen_addr = f'[::]:{grpc_port}'

logger = logging.getLogger("tira")


class Command(BaseCommand):
    """Run git_runner via cli.
       Later this will become a fully fledged cli tool that we use as wrapper in the repository.
       At the moment, we just execute some predefined commands
    """

    def handle(self, *args, **options):
        if 'create_task_repository' in options and options['create_task_repository']:
            print(f'Create a repository for {options["create_task_repository"]}.')
            repo_id = create_task_repository(options['create_task_repository'])
            print(f'The new repository has the id ${repo_id}')

    def add_arguments(self, parser):
        parser.add_argument('--create_task_repository', default=None, type=str)

