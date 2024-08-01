import logging
from concurrent import futures
from contextlib import contextmanager

import grpc
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from tira.grpc.grpc_server import TiraApplicationService
from tira.grpc.test_grpc_host_server import TiraHostService
from tira.proto import tira_host_pb2_grpc

grpc_app_port = settings.APPLICATION_GRPC_PORT
grpc_host_port = settings.HOST_GRPC_PORT

logger = logging.getLogger("grpc_server")


@contextmanager
def serve_forever(app_addr, host_addr):
    app_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraApplicationServiceServicer_to_server(TiraApplicationService(), app_server)
    app_server.add_insecure_port(app_addr)

    host_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), host_server)
    host_server.add_insecure_port(host_addr)

    app_server.start()
    host_server.start()
    yield
    app_server.stop(0)
    host_server.stop(0)


class Command(BaseCommand):
    help = "api server"

    def handle(self, *args, **options):
        call_command("makemigrations")
        call_command("migrate")
        app_addr = f"[::]:{grpc_app_port}"
        host_addr = f"[::]:{grpc_host_port}"
        with serve_forever(app_addr, host_addr):
            logger.info(f"Starting tira-application server on {app_addr} and mock host server on {host_addr}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Starting tira-application server on {app_addr} and mock host server on {host_addr}"
                )
            )
        call_command("runserver", "0.0.0.0:8080")
