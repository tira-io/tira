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


def run_script(script_name, *args):
    p = subprocess.Popen("tira "+script_name+" "+" ".join([a for a in args]), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0].decode('utf-8')
    response = TiraHostMessages_pb2.Response(output=output)
    return response


class TiraHostService(TiraHostMessages_pb2_grpc.TiraHostService):
    def test(self, input, context):
        return TiraHostMessages_pb2.Output(text="Server received: " + input.text)

    def vm_backup(self, request, context):
        return run_script("vm-backup", request.vmName)

    def vm_create(self, request, context):
        return run_script("vm-create", request.ovaFile, request.userName)

    def vm_delete(self, request, context):
        return run_script("vm-delete", request.VirtualMachine)

    def vm_info(self, request, context):
        return run_script("vm-info", request.vmName)

    def vm_sandbox(self, request, context):
        return run_script("vm-sandbox", request.vmName)

    def vm_shutdown(self, request, context):
        return run_script("vm-shutdown", request.vmName)

    def vm_snapshot(self, request, context):
        return run_script("vm-snapshot", request.vmName)

    def vm_start(self, request, context):
        return run_script("vm-start", request.vmName)

    def vm_stop(self, request, context):
        return run_script("vm-stop", request.vmName)

    def vm_unsandbox(self, request, context):
        return run_script("vm-unsandbox", request.vmName)

    def run_execute(self, request, context):
        return run_script("run-execute", request.submissionFile, request.inputDatasetName, request.inputRunPath,
                          request.outputDirName, request.sandboxed, request.optionalParameters);

def serve():
    logger = logging.getLogger()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    TiraHostMessages_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("TiraHost service started.")
    server.wait_for_termination()


if __name__ == '__main__':
    fileConfig('/home/tira/tira_host/logging_config.ini')
    serve()
