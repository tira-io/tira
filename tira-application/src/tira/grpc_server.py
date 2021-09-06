from django.conf import settings
from concurrent import futures
import grpc
import logging
from .proto import tira_host_pb2, tira_host_pb2_grpc
from .transitions import TransitionLog, EvaluationLog, TransactionLog
from uuid import uuid4

grpc_port = settings.APPLICATION_GRPC_PORT

logger = logging.getLogger("tira")


class TiraApplicationService(tira_host_pb2_grpc.TiraApplicationService):
    def set_state(self, request, context):
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
        TODO this should add the new VM to the model in the future.
        """
        logger.debug(f" Application Server received vm-create confirmation with \n"
                     f"{request.vmID}, {request.userName}, {request.initialUserPw}, {request.ip}, {request.sshPort}, "
                     f"{request.rdpPort}")

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


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraApplicationServiceServicer_to_server(TiraApplicationService(), server)
    listen_addr = f'[::]:{port}'
    server.add_insecure_port(listen_addr)
    server.start()
    logger.info("Starting tira-application server on %s", listen_addr)
    return server


s = serve(grpc_port)
