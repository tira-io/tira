import logging

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

grpc_app_port = settings.APPLICATION_GRPC_PORT

logger = logging.getLogger("grpc_server")


class Command(BaseCommand):
    help = "api server"

    def handle(self, *args, **options):
        call_command("makemigrations")
        call_command("makemigrations", "tira")
        call_command("migrate")
        from tira.data.HybridDatabase import HybridDatabase

        HybridDatabase().create_model()
