from django.conf import settings
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command

from tira.data.HybridDatabase import HybridDatabase

grpc_app_port = settings.APPLICATION_GRPC_PORT

logger = logging.getLogger("grpc_server")


class Command(BaseCommand):
    help = 'api server'

    def handle(self, *args, **options):
        call_command('makemigrations')
        call_command('makemigrations', 'tira')
        call_command('migrate')
        HybridDatabase().create_model()
