import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger("tira_server")


class Command(BaseCommand):
    help = "api server"

    def handle(self, *args, **options):
        call_command("makemigrations")
        call_command("makemigrations", "tira")
        call_command("migrate")
        from ...data.HybridDatabase import HybridDatabase

        HybridDatabase().create_model()
