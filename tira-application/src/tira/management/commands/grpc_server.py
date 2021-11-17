from django.conf import settings
from concurrent import futures
import grpc
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError

from tira.proto import tira_host_pb2_grpc
from tira.grpc_server import TiraApplicationService

grpc_port = settings.APPLICATION_GRPC_PORT
listen_addr = f'[::]:{grpc_port}'

logger = logging.getLogger("grpc_server")


@contextmanager
def serve_forever():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    tira_host_pb2_grpc.add_TiraApplicationServiceServicer_to_server(TiraApplicationService(), server)
    server.add_insecure_port(listen_addr)
    server.start()
    yield
    server.stop(0)


class Command(BaseCommand):
    help = 'api server'

    def handle(self, *args, **options):
        with serve_forever():
            logger.info(f"Starting tira-application server on {listen_addr}")
            self.stdout.write(self.style.SUCCESS(f"Starting tira-application server on {listen_addr}"))
            try:
                while True:
                    time.sleep(60*60*24)
            except KeyboardInterrupt:
                pass
