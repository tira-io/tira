import logging

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

grpc_app_port = settings.APPLICATION_GRPC_PORT

logger = logging.getLogger("grpc_server")


class Command(BaseCommand):
    help = "api server"

    def handle(self, *args, **options):
        app_addr = f"[::]:{grpc_app_port}"
        logger.info(f"Starting tira-application server on {app_addr}")
        self.stdout.write(self.style.SUCCESS(f"Starting tira-application server on {app_addr}"))
        call_command("runserver", "0.0.0.0:8080")
