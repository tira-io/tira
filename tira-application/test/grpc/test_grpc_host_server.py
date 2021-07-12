#!/usr/bin/env python

from concurrent import futures
import grpc
import sys
from time import sleep

sys.path.append('../../src/tira')
from proto import tira_host_pb2, tira_host_pb2_grpc

STATE = {"status": 'stopped'}


class TiraHostService(tira_host_pb2_grpc.TiraHostService):

    def test(self, request, context):
        print(f"received vm-backup for {request.Input.text}")
        return tira_host_pb2.Output(text=f"Server received: {request.Input.text}")

    def vm_backup(self, request, context):
        print(f"received vm-backup for {request.vmName}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
        return response

    def vm_create(self, request, context):
        print(f"received vm-create for {request.ovaFile} - {request.userName} - {request.bulkCommandId}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
        return response

    def vm_delete(self, request, context):
        print(f"received vm-delete for {request.vmName}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
        return response

    def vm_info(self, request, context):
        print(f"received vm-info for {request.vmName}")
        response = tira_host_pb2.ResponseVmInfo()
        response.guestOs = 'test: ubuntu'
        response.memorySize = 'test: 0'
        response.numberOfCpus = 'test: 0'
        response.sshPort = '0000'
        response.rdpPort = '0000'
        response.host = 'localhost'
        if STATE.get('status') == 'stopped':
            response.state = 'stopped'
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'running':
            response.state = 'running'
            response.sshPortStatus = True
            response.rdpPortStatus = True
        elif STATE.get('status') == 'sandboxed':
            response.state = 'sandboxed'
            response.sshPortStatus = False
            response.rdpPortStatus = False
        elif STATE.get('status') == 'sandboxing':
            response.state = 'sandboxing'
            response.sshPortStatus = False
            response.rdpPortStatus = False

        return response

    def vm_list(self, context):
        print(f"received vm-list")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
        return response

    def vm_sandbox(self, request, context):
        print(f"received vm-sandbox for {request.vmName}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
        return response

    def vm_shutdown(self, request, context):
        print(f"received vm-shutdown for {request.vmName}")
        response = tira_host_pb2.Response()
        if STATE.get('status') == "running":
            response.status = tira_host_pb2.Response.Status.SUCCESS
            STATE['status'] = 'stopped'
        else:
            response.status = tira_host_pb2.Response.Status.FAILED
        response.commandId = "12345"
        return response

    def vm_snapshot(self, request, context):
        print(f"received vm-snapshot for {request.vmName}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.FAILED
        response.commandId = "12345"
        return response

    def vm_start(self, request, context):
        print(f"received vm-start for {request.vmName}")
        response = tira_host_pb2.Response()
        if STATE.get('status') == "stopped":
            response.status = tira_host_pb2.Response.Status.SUCCESS
            STATE['status'] = 'running'
        else:
            response.status = tira_host_pb2.Response.Status.FAILED
        response.commandId = "12345"
        return response

    def vm_stop(self, request, context):
        print(f"received vm-stop for {request.vmName}")
        response = tira_host_pb2.Response()
        if STATE.get('status') in {"running", "sandboxed", "sandboxing"}:
            response.status = tira_host_pb2.Response.Status.SUCCESS
            STATE['status'] = 'stopped'
        else:
            response.status = tira_host_pb2.Response.Status.FAILED
        response.commandId = "12345"
        return response

    def vm_unsandbox(self, request, context):
        print(f"received vm-unsandbox for {request.vmName}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
        return response

    def run_execute(self, request, context):
        print(f"received run-execute for {request.submissionFile} - {request.inputDatasetName} - {request.inputRunPath} - {request.outputDirName} - {request.sandboxed} - {request.runId} - {request.snapshotName} - {request.optionalParameters}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
        return response

    def run_eval(self, request, context):
        print(f"received run-eval for {request.submissionFile} - {request.inputDatasetName} - {request.inputRunPath} - {request.outputDirName} - {request.sandboxed} - {request.runId} - {request.snapshotName} - {request.optionalParameters}")
        response = tira_host_pb2.Response()
        response.status = tira_host_pb2.Response.Status.SUCCESS
        response.commandId = "12345"
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