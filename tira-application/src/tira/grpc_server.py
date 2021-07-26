from django.conf import settings
from concurrent import futures
import grpc
import logging
from .proto import tira_host_pb2, tira_host_pb2_grpc
from .transitions import TransitionLog

grpc_port = settings.APPLICATION_GRPC_PORT

logger = logging.getLogger("tira")


class TiraApplicationService(tira_host_pb2_grpc.TiraApplicationService):
    def set_state(self, request, context):
        print(f" Application Server received vm-state {request.state} for {request.vmId}")
        t = TransitionLog(vm_id=request.vmId, vm_state=request.state)
        t.save()
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        t = TransitionLog.objects.get(vm_id=request.vmId)
        print(t.vm_id, t.vm_state)
        # response.transactionId = "12345"
        return response

    def complete_transaction(self, request, context):
        print(f" Application Server received complete_transaction for {request.transactionId}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = request.transactionId
        return response


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraApplicationServiceServicer_to_server(TiraApplicationService(), server)
    listen_addr = f'[::]:{port}'
    server.add_insecure_port(listen_addr)
    server.start()
    logger.info("Starting tira-application server on %s", listen_addr)
    print("Starting tira-application server on ", listen_addr)
    return server


s = serve(grpc_port)
