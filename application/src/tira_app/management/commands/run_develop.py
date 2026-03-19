import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger("tira_server")


class Command(BaseCommand):
    help = "api server"

    def handle(self, *args, **options):
        app_addr = "0.0.0.0:8080"
        logger.info(f"Starting tira-application server on {app_addr}")
        self.stdout.write(self.style.SUCCESS(f"Starting tira-application server on {app_addr}"))
        call_command("runserver", app_addr)
