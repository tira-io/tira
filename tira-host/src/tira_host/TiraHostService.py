#!/usr/bin/env python
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Nikolay Kolyada
"""

from concurrent import futures
import logging
from logging.config import fileConfig
import subprocess

import grpc

import TiraHostMessages_pb2
import TiraHostMessages_pb2_grpc


def run_script(script_name, virtual_machine):
    p = subprocess.Popen("../"+script_name+" "+virtual_machine, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0].decode('utf-8')
    # return Response message  with VirtualMachineState inside
    response = TiraHostMessages_pb2.Response()
    return response


class TiraHostService(TiraHostMessages_pb2_grpc.TiraHostService):
    tira_scripts = {
        "vm_backup": "tira-vm-backup.sh",
        "vm_create": "tira-vm-create.sh",
        "vm_delete": "tira-vm-delete.sh",
        "vm_info": "tira-vm-info.sh",
        "vm_sandbox": "tira-vm-sandbox.sh",
        "vm_shutdown": "tira-vm-shutdown.sh",
        "vm_snapshot": "tira-vm-snapshot.sh",
        "vm_start": "tira-vm-start.sh",
        "vm_stop": "tira-vm-stop.sh",
        "vm_unsandbox": "tira-vm-unsandbox.sh"
    }

    def test(self, input, context):
        return TiraHostMessages_pb2.Output(text="Test message: " + input.text)

    def vm_backup(self, request, context):
        # subprocess call tira script with parameters
        return TiraHostMessages_pb2.Reply()

    def vm_create(self, request, context):
        return TiraHostMessages_pb2.Reply()

    def vm_delete(self, request, context):
        return TiraHostMessages_pb2.Reply()

    def vm_info(self, request, context):
        return run_script("tira-vm-info.sh", request.VirtualMachine)

    def vm_sandbox(self, request, context):
        return TiraHostMessages_pb2.Reply()

    def vm_shutdown(self, request, context):
        return TiraHostMessages_pb2.Reply()

    def vm_snapshot(self, request, context):
        return TiraHostMessages_pb2.Reply()

    def vm_start(self, request, context):
        return TiraHostMessages_pb2.Reply()

    def vm_stop(self, request, context):
        return TiraHostMessages_pb2.Reply()

    def vm_unsandbox(self, request, context):
        return TiraHostMessages_pb2.Reply()

def serve():
    logger = logging.getLogger()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    TiraHostMessages_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("TiraHost service started.")
    server.wait_for_termination()


if __name__ == '__main__':
    fileConfig('logging_config.ini')
    serve()
