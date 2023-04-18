from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.apps import apps

class Command(BaseCommand):
    help = 'dump all of tira'

    def handle(self, *args, **options):
        tira_config = apps.get_app_config('tira')
        models = [f'tira.{i}' for i in tira_config.models]

        cmd = ['dumpdata'] + models + ['--indent', '2']
        call_command(*cmd)
