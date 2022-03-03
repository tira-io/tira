from django.conf import settings
from concurrent import futures
import grpc
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from tira.proto import tira_host_pb2_grpc
from tira.grpc.grpc_server import TiraApplicationService

grpc_app_port = settings.APPLICATION_GRPC_PORT

logger = logging.getLogger("grpc_server")


@contextmanager
def serve_forever(app_addr):
    app_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraApplicationServiceServicer_to_server(TiraApplicationService(), app_server)
    app_server.add_insecure_port(app_addr)

    app_server.start()
    yield
    app_server.stop(0)


class Command(BaseCommand):
    help = 'api server'

    def handle(self, *args, **options):
        call_command('makemigrations')
        call_command('migrate')
        app_addr = f'[::]:{grpc_app_port}'
        with serve_forever(app_addr):
            logger.info(f"Starting tira-application server on {app_addr}")
            self.stdout.write(self.style.SUCCESS(f"Starting tira-application server on {app_addr}"))
            call_command('runserver', "8080")
