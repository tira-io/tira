import os
import django
    
from django.conf import settings
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.cache import cache

from tira.git_runner import get_git_runner, docker_images_in_user_repository
from tira.tira_model import load_refresh_timestamp_for_cache_key, get_git_integration

from tira.util import get_tira_id
logger = logging.getLogger("tira")


class Command(BaseCommand):
    """Run git_runner via cli.
       Later this will become a fully fledged cli tool that we use as wrapper in the repository.
       At the moment, we just execute some predefined commands
    """
    
    def run_command_create_user_repository(self, options, git_runner):
        print(f'Create a user repository for {options["create_user_repository"]}.')
        repo_id = create_user_repository(options['create_user_repository'])
        print(f'The new repository has the id ${repo_id}')
        print(add_new_tag_to_docker_image_repository('registry.webis.de/code-research/tira/tira-user-del-maik-user-repo/my-software', '0.0.3', '0.0.1-tira-docker-software-id-name-x'))
        print('Images: ' + str(git_runner.docker_images_in_user_repository(options['create_user_repository'])))

    def run_command_create_task_repository(self, options):
        print(f'Create a task-repository for {options["create_task_repository"]}.')
        repo_id = create_task_repository(options['create_task_repository'])
        print(f'The new task-repository has the id ${repo_id}')

    def run_command_running_jobs(self, options):
        if 'user_id' not in options or not options['user_id']:
            raise ValueError('Please pass --user_id as argument.')

        print(list(yield_all_running_pipelines(options['running_jobs'], options['user_id'], cache, True)))

        print(load_refresh_timestamp_for_cache_key(cache, 'all-running-pipelines-repo-' +options['running_jobs']))

    def run_command_stop_job_and_clean_up(self, options):
        if 'user_id' not in options or not options['user_id']:
            raise ValueError('Please pass --user_id as argument.')

        if 'run_id' not in options or not options['run_id']:
            raise ValueError('Please pass --user_id as argument.')

        stop_job_and_clean_up(options['stop_job_and_clean_up'], options['user_id'], options['run_id'])

    def handle(self, *args, **options):
        if 'organization' not in options or not options['organization']:
            raise ValueError('Please pass --organization')
        
        git_runner = get_git_runner(get_git_integration(options['organization'], None))
        print(f'Use {git_runner}.')
    
        if 'archive_repository' in options and options['archive_repository']:
            archive_repository(options['archive_repository'], git_runner)

        if 'create_task_repository' in options and options['create_task_repository']:
            self.run_command_create_task_repository(options, git_runner)

        if 'create_user_repository' in options and options['create_user_repository']:
            self.run_command_create_user_repository(options, git_runner)

        if 'running_jobs' in options and options['running_jobs']:
            self.run_command_running_jobs(options, git_runner)

        if 'stop_job_and_clean_up' in options and options['stop_job_and_clean_up']:
            self.run_command_stop_job_and_clean_up(options, git_runner)

        if 'run_image' in options and options['run_image']:
            git_runner.start_git_workflow(task_id='clickbait-spoiling',
                               dataset_id='task-1-type-classification-validation-20220924-training',
                               vm_id='princess-knight',
                               run_id=get_tira_id(),
                               git_runner_image='webis/pan-clickbait-spoiling-evaluator:0.0.10',
                               git_runner_command="""bash -c '/clickbait-spoiling-eval.py --task 2 --ground_truth_spoiler $inputDataset --input_run $inputRun --output_prototext ${outputDir}/evaluation.prototext'""",
                               git_repository_id=2761,
                               evaluator_id='task-2-spoiler-generation-validation-20220924-training-evaluator',
                               user_image_to_execute='registry.webis.de/code-research/tira/tira-user-princess-knight/naive-baseline-task2:0.0.1-tira-docker-software-id-genteel-upstream',
                               user_command_to_execute='/naive-baseline-task-2.py --input $inputDataset/input.jsonl --output $outputDir/run.jsonl',
                               tira_software_id='17',
                               resources='small-resources-gpu',
                               
            )
        if 'docker_images_in_user_repository' in options and options['docker_images_in_user_repository']:
            print(git_runner.docker_images_in_user_repository(options['docker_images_in_user_repository']))
            #print(docker_images_in_user_repository(options['docker_images_in_user_repository']))

    def add_arguments(self, parser):
        parser.add_argument('--create_task_repository', default=None, type=str)
        parser.add_argument('--create_user_repository', default=None, type=str)
        parser.add_argument('--run_image', default=None, type=str)
        parser.add_argument('--archive_repository', default=None, type=str)
        parser.add_argument('--running_jobs', default=None, type=str)
        parser.add_argument('--stop_job_and_clean_up', default=None, type=str)
        parser.add_argument('--user_id', default=None, type=str)
        parser.add_argument('--run_id', default=None, type=str)
        parser.add_argument('--docker_images_in_user_repository', default=None, type=str)
        parser.add_argument('--organization', default=None, type=str)

