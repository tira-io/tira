#!/usr/bin/env python
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Nikolay Kolyada
"""

import asyncio
from concurrent import futures
import grpc
from grpc import aio
import logging
from logging.config import fileConfig
import subprocess
import re

from proto import tira_host_pb2, tira_host_pb2_grpc

def run_tira_script(script_name, *args):
    p = subprocess.Popen("tira " + script_name + " " + " ".join([a for a in args]), shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output = p.communicate()[0].decode('utf-8')
    response = tira_host_pb2.Response(output=output)
    return response


def run_shell_command(command_string):
    p = subprocess.Popen(command_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0].decode('utf-8')
    response = tira_host_pb2.Response(output=output)
    return response


class TiraHostService(tira_host_pb2_grpc.TiraHostService):
    def test(self, input, context):
        return tira_host_pb2.Output(text="Server received: " + input.text)

    def shell_command(self, command):
        return run_shell_command(command)

    def vm_backup(self, request, context):
        return run_tira_script("vm-backup", request.vmName)

    def vm_create(self, request, context):
        return run_tira_script("vm-create", request.ovaFile, request.userName)

    def vm_delete(self, request, context):
        return run_tira_script("vm-delete", request.vmName)

    def vm_info(self, request, context):
        response = run_tira_script("vm-info", request.vmName)
        response_vm_info = tira_host_pb2.ResponseVmInfo()
        for line in response.output.split("\n"):
            if line.startswith("Guest OS:"):
                response_vm_info.guestOs = line.split(": ")[1].strip()
            elif line.startswith("Memory size"):
                response_vm_info.memorySize = line.split()[2].strip()
            elif line.startswith("Number of CPUs:"):
                response_vm_info.numberOfCpus = line.split(": ")[1].strip()
            elif line.startswith("State:"):
                response_vm_info.state = re.sub(".\\d+\\)", ")", line.split(": ")[1].strip())

        return response_vm_info

    def vm_list(self, request, context):
        return run_tira_script("vm-list")

    def vm_sandbox(self, request, context):
        return run_tira_script("vm-sandbox", request.vmName)

    def vm_shutdown(self, request, context):
        return run_tira_script("vm-shutdown", request.vmName)

    def vm_snapshot(self, request, context):
        return run_tira_script("vm-snapshot", request.vmName)

    def vm_start(self, request, context):
        return run_tira_script("vm-start", request.vmName)

    def vm_stop(self, request, context):
        return run_tira_script("vm-stop", request.vmName)

    def vm_unsandbox(self, request, context):
        return run_tira_script("vm-unsandbox", request.vmName)

    def run_execute(self, request, context):
        return run_tira_script("run-execute", request.submissionFile, request.inputDatasetName, request.inputRunPath,
                               request.outputDirName, request.sandboxed, request.optionalParameters);

    # async def run_execute(self, request, context):
    #     return run_tira_script("run-execute", request.submissionFile, request.inputDatasetName, request.inputRunPath,
    #                                       request.outputDirName, request.sandboxed, request.optionalParameters);


def serve():
    logger = logging.getLogger()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    server.start()
    logging.info("Starting tira-host server on %s", listen_addr)
    server.wait_for_termination()


# async def serve_async():
#     server = aio.server()
#     tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
#     listen_addr = '[::]:50051'
#     server.add_insecure_port(listen_addr)
#     logging.info("Starting server on %s", listen_addr)
#     await server.start()
#     await server.wait_for_termination()


if __name__ == '__main__':
    fileConfig('../conf/logging_config.ini')
    serve()
    # asyncio.run(serve_async())
