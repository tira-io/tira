#!/usr/bin/env python

from concurrent import futures
import grpc
import sys
from time import sleep
from threading import Thread

sys.path.append('../../src/tira')
from proto import tira_host_pb2, tira_host_pb2_grpc
from test_grpc_host_client import TestGrpcHostClient

STATE = {"status": 'stopped'}


class TiraHostService(tira_host_pb2_grpc.TiraHostService):

    def vm_backup(self, request, context):
        print(f"received vm-backup for {request.vmId}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response

    def vm_create(self, request, context):
        print(f"received vm-create for {request.ovaFile} - {request.vmId} - {request.bulkCommandId}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response

    def vm_delete(self, request, context):
        print(f"received vm-delete for {request.vmId}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response

    def vm_info(self, request, context):
        print(f"received vm-info for {request.vmId}")
        response = tira_host_pb2.VmInfo()
        response.guestOs = 'test: ubuntu'
        response.memorySize = 'test: 0'
        response.numberOfCpus = 'test: 0'
        response.sshPort = '0000'
        response.rdpPort = '0000'
        response.host = 'localhost'
        if STATE.get('status') == 'running':
            response.state = tira_host_pb2.State.RUNNING
            response.sshPortStatus = True
            response.rdpPortStatus = True
        elif STATE.get('status') == 'stopped':
            response.state = tira_host_pb2.State.POWERED_OFF
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'powering_on':
            response.state = tira_host_pb2.State.POWERING_ON
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'powering_off':
            response.state = tira_host_pb2.State.POWERING_OFF
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'sandboxed':
            response.state = tira_host_pb2.State.EXECUTING
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'sandboxing':
            response.state = tira_host_pb2.State.SANDBOXING
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'unsandboxing':
            response.state = tira_host_pb2.State.UNSANDBOXING
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'archived':
            response.state = tira_host_pb2.State.ARCHIVED
            response.sshPortStatus = False
            response.rdpPortStatus = False
        else:
            response.state = tira_host_pb2.State.UNDEFINED
            response.sshPortStatus = False
            response.rdpPortStatus = False

        return response

    def vm_list(self, context):
        print(f"received vm-list")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response

    def vm_sandbox(self, request, context):
        print(f"received vm-sandbox for {request.vmId}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response

    def vm_shutdown(self, request, context):
        print(f"received vm-shutdown for {request.vmId}")
        response = tira_host_pb2.Transaction()
        if STATE.get('status') == "running":
            test_host_client = TestGrpcHostClient()
            t = Thread(target=test_host_client.set_state, args=(request.vmId, tira_host_pb2.State.POWERED_OFF))
            t.start()
            response.status = tira_host_pb2.Status.SUCCESS
            STATE['status'] = 'stopped'
        else:
            response.status = tira_host_pb2.Status.FAILED
        response.transactionId = "12345"
        return response

    def vm_snapshot(self, request, context):
        print(f"received vm-snapshot for {request.vmId}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.FAILED
        response.transactionId = "12345"
        return response

    def vm_start(self, request, context):
        print(f"received vm-start for {request.vmId}")
        response = tira_host_pb2.Transaction()
        if STATE.get('status') == "stopped":
            test_host_client = TestGrpcHostClient()
            t = Thread(target=test_host_client.set_state, args=(request.vmId, tira_host_pb2.State.RUNNING))
            t.start()
            STATE['status'] = 'running'  # Only works in the mockup server. Should be 'powering_on' in live.
            response.status = tira_host_pb2.Status.SUCCESS
        else:
            response.status = tira_host_pb2.Status.FAILED

        return response

    def vm_stop(self, request, context):
        print(f"received vm-stop for {request.vmId}")
        response = tira_host_pb2.Transaction()
        if STATE.get('status') in {"running", "sandboxed", "sandboxing"}:
            response.status = tira_host_pb2.Status.SUCCESS
            STATE['status'] = 'stopped'
        else:
            response.status = tira_host_pb2.Status.FAILED
        response.transactionId = "12345"
        return response

    def vm_unsandbox(self, request, context):
        print(f"received vm-unsandbox for {request.vmId}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response

    def run_execute(self, request, context):
        print(f"received run-execute for {request.submissionFile} - {request.inputDatasetName} - {request.inputRunPath} - {request.outputDirName} - {request.sandboxed} - {request.runId} - {request.snapshotName} - {request.optionalParameters}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response

    def run_eval(self, request, context):
        print(f"received run-eval for {request.submissionFile} - {request.inputDatasetName} - {request.inputRunPath} - {request.outputDirName} - {request.sandboxed} - {request.runId} - {request.snapshotName} - {request.optionalParameters}")
        response = tira_host_pb2.Transaction()
        response.status = tira_host_pb2.Status.SUCCESS
        response.transactionId = "12345"
        return response


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    listen_addr = f'[::]:{port}'
    server.add_insecure_port(listen_addr)
    server.start()
    print("Starting tira-host server on %s", listen_addr)
    server.wait_for_termination()


if __name__ == '__main__':
    serve("50051")