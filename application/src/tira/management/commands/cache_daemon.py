from django.conf import settings
from django.core.cache import cache
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
import tira.tira_model as model

import time
import datetime

logger = logging.getLogger("cache_daemon")
from tira.tira_model import get_git_integration
from tira.git_runner import all_git_runners


class Command(BaseCommand):
    help = 'cache daemon'

    def keep_running_softwares_fresh(self, sleep_time):
        while True:
            time.sleep(int(sleep_time))
            print(str(datetime.datetime.now()) + ': Start loop to keep the running softwares fresh (sleeped ' + str(int(sleep_time)) + ' seconds) ...')
            for task in model.get_tasks():
                if task is None:
                    continue
                if model.git_pipeline_is_enabled_for_task(task['task_id'], cache):
                    evaluators_for_task = model.get_evaluators_for_task(task['task_id'], cache)
                    repositories = set([i['git_repository_id'] for i in evaluators_for_task if i['is_git_runner'] and i['git_repository_id']])
                
                    for git_repository_id in repositories:
                        try:
                            print(task['task_id'] + '--->' + str(git_repository_id))
                            git_integration = get_git_integration(task_id=task['task_id'])
                            running_pipelines = git_integration.all_running_pipelines_for_repository(git_repository_id, cache, force_cache_refresh=True)
                            print('Refreshed Cache: ' + task['task_id'] + ' on repo ' + str(git_repository_id) + ' has ' + str(len(running_pipelines)) + ' jobs.')
                        except Exception as e:
                            print(f'Exception during refreshing the repository {git_repository_id}: e')
                            logger.warn(f'Exception during refreshing the repository {git_repository_id}', e)
                            continue

                time.sleep(0.1)

    def refresh_user_images_in_repo(self, git_runner, sleep_time):
        print(str(datetime.datetime.now()) + ': Start loop to keep the user images fresh (sleeped ' + str(int(sleep_time)) + ' seconds) ...')
        for user in git_runner.all_user_repositories():
            user = user.split('tira-user-')[-1]
            print(user)
            try:
                images = git_runner.docker_images_in_user_repository(user, cache, force_cache_refresh=True)
                print('Refreshed Cache: ' + user + ' has ' + str(len(images)) + ' images.')
            except Exception as e:
                print('Exception during refreshing image repository {user}: {e}')
                continue
            time.sleep(0.1)

    def keep_user_images_fresh(self, sleep_time):
        while True:
            time.sleep(int(sleep_time))
            print(str(datetime.datetime.now()) + ': Start loop over all git runners to keeo user images fresh (sleeped ' + str(int(sleep_time)) + ' seconds) ...')
            for git_runner in all_git_runners():
                try:
                    self.refresh_user_images_in_repo(git_runner, sleep_time)
                except Exception as e:
                    print(f'Exception in keep_user_images_fresh: {e}')
                    continue
                
    def handle(self, *args, **options):
        call_command('createcachetable')
        
        if 'keep_running_softwares_fresh' in options and options['keep_running_softwares_fresh']:
            self.keep_running_softwares_fresh(options['keep_running_softwares_fresh'])

        if 'keep_user_images_fresh' in options and options['keep_user_images_fresh']:
            self.keep_user_images_fresh(options['keep_user_images_fresh'])

    def add_arguments(self, parser):
        parser.add_argument('--keep_running_softwares_fresh', default=None, type=str)
        parser.add_argument('--keep_user_images_fresh', default=None, type=str)

