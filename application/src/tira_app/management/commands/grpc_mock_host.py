import logging
import time
from concurrent import futures
from contextlib import contextmanager

import grpc
from django.conf import settings
from django.core.management.base import BaseCommand

from ...grpc.test_grpc_host_server import TiraHostService
from ...proto import tira_host_pb2_grpc

grpc_host_port = settings.HOST_GRPC_PORT

logger = logging.getLogger("grpc_server")


@contextmanager
def serve_forever(host_addr):
    host_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), host_server)
    host_server.add_insecure_port(host_addr)

    host_server.start()
    yield
    host_server.stop(0)


class Command(BaseCommand):
    help = "api server"

    def handle(self, *args, **options):
        host_addr = f"[::]:{grpc_host_port}"
        with serve_forever(host_addr):
            logger.info(f"Starting mock host server on {host_addr}")
            self.stdout.write(self.style.SUCCESS(f"Starting tira mock host server on {host_addr}"))
            try:
                while True:
                    time.sleep(60 * 60 * 24)
            except KeyboardInterrupt:
                pass
