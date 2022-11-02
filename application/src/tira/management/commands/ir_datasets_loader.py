import os
import django
    
from django.conf import settings
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.cache import cache

logger = logging.getLogger("tira")


class Command(BaseCommand):
    """Run git_runner via cli.
       ToDo: Write some documentation
    """
    

    def handle(self, *args, **options):
        print('ToDo: Implement this: Import dataset with id ' + str(options['ir_datasets_id']))

    def add_arguments(self, parser):
        parser.add_argument('--ir_datasets_id', default=None, type=str)

