import os
import django
    
from django.conf import settings
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from tira.git_runner import create_user_repository, create_task_repository, docker_images_in_user_repository,  add_new_tag_to_docker_image_repository, archive_repository, help_on_uploading_docker_image, yield_all_running_pipelines, stop_job_and_clean_up

logger = logging.getLogger("tira")


class Command(BaseCommand):
    """Run git_runner via cli.
       Later this will become a fully fledged cli tool that we use as wrapper in the repository.
       At the moment, we just execute some predefined commands
    """
    
    def run_command_create_user_repository(self, options):
        print(f'Create a user repository for {options["create_user_repository"]}.')
        repo_id = create_user_repository(options['create_user_repository'])
        print(f'The new repository has the id ${repo_id}')
        print(add_new_tag_to_docker_image_repository('registry.webis.de/code-research/tira/tira-user-del-maik-user-repo/my-software', '0.0.3', '0.0.1-tira-docker-software-id-name-x'))
        print('Images: ' + str(docker_images_in_user_repository(options['create_user_repository'])))

    def run_command_create_task_repository(self, options):
        print(f'Create a task-repository for {options["create_task_repository"]}.')
        repo_id = create_task_repository(options['create_task_repository'])
        print(f'The new task-repository has the id ${repo_id}')

    def run_command_running_jobs(self, options):
        if 'user_id' not in options or not options['user_id']:
            raise ValueError('Please pass --user_id as argument.')

        print(list(yield_all_running_pipelines(options['running_jobs'], options['user_id'])))

    def run_command_stop_job_and_clean_up(self, options):
        if 'user_id' not in options or not options['user_id']:
            raise ValueError('Please pass --user_id as argument.')

        if 'run_id' not in options or not options['run_id']:
            raise ValueError('Please pass --user_id as argument.')

        stop_job_and_clean_up(options['stop_job_and_clean_up'], options['user_id'], options['run_id'])

    def handle(self, *args, **options):
        if 'archive_repository' in options and options['archive_repository']:
            archive_repository(options['archive_repository'])

        if 'create_task_repository' in options and options['create_task_repository']:
            self.run_command_create_task_repository(options)

        if 'create_user_repository' in options and options['create_user_repository']:
            self.run_command_create_user_repository(options)

        if 'running_jobs' in options and options['running_jobs']:
            self.run_command_running_jobs(options)

        if 'stop_job_and_clean_up' in options and options['stop_job_and_clean_up']:
            self.run_command_stop_job_and_clean_up(options)

    def add_arguments(self, parser):
        parser.add_argument('--create_task_repository', default=None, type=str)
        parser.add_argument('--create_user_repository', default=None, type=str)
        parser.add_argument('--archive_repository', default=None, type=str)
        parser.add_argument('--running_jobs', default=None, type=str)
        parser.add_argument('--stop_job_and_clean_up', default=None, type=str)
        parser.add_argument('--user_id', default=None, type=str)
        parser.add_argument('--run_id', default=None, type=str)

