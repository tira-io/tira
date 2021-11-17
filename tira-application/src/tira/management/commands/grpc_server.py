from django.conf import settings
from concurrent import futures
import grpc
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError

from tira.proto import tira_host_pb2, tira_host_pb2_grpc
from tira.transitions import TransitionLog, EvaluationLog, TransactionLog
from tira.tira_model import model

grpc_port = settings.APPLICATION_GRPC_PORT
listen_addr = f'[::]:{grpc_port}'

logger = logging.getLogger("tira")


class TiraApplicationService(tira_host_pb2_grpc.TiraApplicationService):
    def set_state(self, request, context):
        """ TODO error handling """
        logger.debug(f" Application Server received vm-state {request.state} for {request.vmId}")

        _ = TransitionLog.objects.create(vm_id=request.vmId, vm_state=request.state)
        return tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                         message=f"Set VM state to {request.state}",
                                         transactionId=request.transactionId)

    def complete_transaction(self, request, context):
        """ Marks a transaction as completed if the
        This is basically the final stage of a a TIRA message exchange.
        """
        logger.debug(f" Application Server received complete_transaction for {request.transactionId}")
        _ = TransactionLog.objects.filter(transaction_id=request.transactionId).update(
            completed=True,
            last_status=str(request.status),
            last_message=request.message)

        return tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                         message="Application accepted the transaction",
                                         transactionId=request.transaction.transactionId)

    def confirm_vm_create(self, request, context):
        """ This gets called if a vm was successfully created. Right now it just says 'yes' when called.
        See tira_host.proto for request specification.
        """
        logger.debug(f" Application Server received vm-create confirmation with \n"
                     f"{request.vmID}, {request.userName}, {request.initialUserPw}, {request.ip}, {request.sshPort}, "
                     f"{request.rdpPort}")

        _ = TransactionLog.objects.filter(transaction_id=request.transaction.transactionId).update(
            completed=False,
            last_status=str(request.transaction.status),
            last_message=request.transaction.message)

        if request.transaction.status == tira_host_pb2.Status.SUCCESS:
            model.add_vm(request.vmId, request.userName, request.initialUserPw,
                         request.ip, request.host, request.sshPort, request.rdpPort)

        else:
            logger.error("Application received confirm_vm_create with status Failed:\n"
                         f"{request.vmID}, {request.userName}, {request.initialUserPw}, {request.ip}, "
                         f"{request.sshPort}, {request.rdpPort}")

        return tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                         message="Application accepted vm create confirmation",
                                         transactionId=request.transaction.transactionId)

    def confirm_vm_delete(self, request, context):
        """ This gets called if a run_eval finishes and receives the EvaluationResults.
        Right now it just says 'yes' when called. See tira_host.proto for request specification.
        TODO this should remove the deleted vm from the model.
        """
        print(f" Application Server received vm_delete confirmation with: \n"
              f"{request.vmId.vmId} measures.")

        return tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                         message="Application accepted vm delete confirmation",
                                         transactionId=request.transaction.transactionId)

    def confirm_run_eval(self, request, context):
        """ This gets called if a run_eval finishes and receives the EvaluationResults.
        Right now it just says 'yes' when called. See tira_host.proto for request specification.
        """
        logger.debug(f" Application Server received run-eval confirmation with: \n"
                     f"{request.runId.runId} and {len(request.measures)} measures.")
        EvaluationLog.objects.filter(vm_id=request.runId.vmId, run_id=request.runId.runId).delete()

        _ = TransactionLog.objects.filter(transaction_id=request.transaction.transactionId).update(
            completed=False,
            last_status=str(request.transaction.status),
            last_message=request.transaction.message)

        return tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                         message="Application accepted evaluation confirmation",
                                         transactionId=request.transaction.transactionId)


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
