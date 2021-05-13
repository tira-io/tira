#!/usr/bin/env python

import os
from concurrent import futures
from configparser import ConfigParser
from datetime import datetime
from functools import wraps
from google.protobuf.json_format import MessageToDict
import grpc
from grpc import aio
import logging
from logging.config import fileConfig
import re
import socket
import threading
import time
import uuid
import vm_manage

from proto import tira_host_pb2, tira_host_pb2_grpc
from tira_model import FileDatabase

logger = logging.getLogger()

commands = {}
model = FileDatabase()

parser = ConfigParser()
parser.read('conf/grpc_service.ini')
grpc_port = parser.get('main', 'grpc_port')


def async_api(wrapped_function):
    """
    Manage command queue and update command state in the model.
    :param wrapped_function:
    :return:
    """

    @wraps(wrapped_function)
    def new_function(*args, **kwargs):
        def task_call():
            try:
                # Add new Message to command state file for the current host.
                command = model.create_command(args[1], command_id,
                                               (wrapped_function.__name__ + ' ' + str(args[1])).strip())

                # TODO: check solution with logger
                # Set logger handler file for the command output
                # vmmanage.logger.handlers.clear()
                # vmmanage.logger.addHandler(logging.FileHandler(command.logFile))

                vmmanage = vm_manage.VMManage(command.logFile)
                returncode = wrapped_function(*args, vmmanage=vmmanage)
                model.update_command(command_id, status=tira_host_pb2.Response.Status.SUCCESS,
                                     returnCode=returncode)
            except Exception as e:
                logger.error(str(e))
                model.update_command(command_id, status=tira_host_pb2.Response.Status.FAILED,
                                     returnCode=e.returncode)
            finally:
                # Set endTime to help later remove finished commands from the state file.
                command.endTime = datetime.strftime(datetime.utcnow(), "%Y-%m-%dT%H:%M:%SZ")
                commands.pop(command_id)

        # Assign an id to the asynchronous task
        command_id = uuid.uuid4().hex + "_" + wrapped_function.__name__
        # command_id = datetime.strftime(datetime.now(), "%Y%m%dT%H:%M:%S.%fZ") + "_" + wrapped_function.__name__

        # Record the task, and then launch it
        commands[command_id] = {'command_thread': threading.Thread(target=task_call, args=())}
        commands[command_id]['command_thread'].start()

        response = tira_host_pb2.Response()
        response.commandId = command_id
        return response

    return new_function


class TiraHostService(tira_host_pb2_grpc.TiraHostService):
    def __init__(self):
        def clean_old_tasks():
            """
            Start a background thread that cleans up old tasks. Only keep tasks that are running or that finished
            less than 5 days ago.

            TODO: keep last 50 commands instead of period
            """
            while True:
                time_ago = datetime.timestamp(datetime.utcnow()) - 5 * 86400
                time.sleep(5 * 60)
                model.clean_command_state(time_ago)

        thread = threading.Thread(target=clean_old_tasks)
        thread.start()

    def test(self, request, context):
        return tira_host_pb2.Output(text="Server received: " + input.text)

    @async_api
    def vm_backup(self, request, context, vmmanage):
        """

        :param vmmanage:
        :param request:
        :param context:
        :return:
        """
        return vmmanage.vm_backup(request.vmName)

    @async_api
    def vm_create(self, request, context, vmmanage):
        """

        :param vmmanage:
        :param request:
        :param context:
        :return:
        """

        return vmmanage.vm_create(request.ovaFile, request.userName)

    @async_api
    def vm_delete(self, request, context, vmmanage):
        """

        :param vmmanage:
        :param request:
        :param context:
        :return:
        """
        return vmmanage.vm_delete(request.vmName)

    def vm_info(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """
        vm = model.get_vm_by_id(request.vmName)
        if not vm:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("VM not found.")
            # return tira_host_pb2.Response()
            raise Exception("VM not found.")

        output = ""
        vmmanage = vm_manage.VMManage()
        return_code = vmmanage.vm_info(vm.vmName, output=output)
        response_vm_info = tira_host_pb2.ResponseVmInfo()
        for line in output.split('\n'):
            if line.startswith("Guest OS:"):
                response_vm_info.guestOs = line.split(": ")[1].strip()
            elif line.startswith("Memory size"):
                response_vm_info.memorySize = line.split()[2].strip()
            elif line.startswith("Number of CPUs:"):
                response_vm_info.numberOfCpus = line.split(": ")[1].strip()
            elif line.startswith("State:"):
                response_vm_info.state = re.sub(".\\d+\\)", ")", line.split(": ")[1].strip())

        response_vm_info.sshPort = vm.portSsh
        response_vm_info.rdpPort = vm.portRdp
        response_vm_info.host = vm.host

        if response_vm_info.sshPort and response_vm_info.rdpPort:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                response_vm_info.sshPortStatus = 1 if sock.connect_ex((vm.host, int(vm.portSsh))) == 0 else 0
                response_vm_info.rdpPortStatus = 1 if sock.connect_ex((vm.host, int(vm.portRdp))) == 0 else 0

        # response_vm_info.is_running = response_vm_info.state.startswith("running")

        return response_vm_info

    def vm_list(self, context, vmmanage):
        output = ""
        vmmanage.vm_list(output)
        return output

    @async_api
    def vm_sandbox(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.vmsandbox(request.vmName)

    @async_api
    def vm_shutdown(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.vm_shutdown(request.vmName)

    @async_api
    def vm_snapshot(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.vm_snapshot(request.vmName)

    @async_api
    def vm_start(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.vm_start(request.vmName)

    @async_api
    def vm_stop(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.vm_stop(request.vmName)

    @async_api
    def vm_unsandbox(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.vm_unsandbox(request.vmName)

    @async_api
    def run_execute(self, request, context, vmmanage):
        """

        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.run_execute(request.submissionFile, request.inputDatasetName,
                                    request.inputRunPath, request.outputDirName, request.sandboxed,
                                    request.optionalParameters)

    @async_api
    def run_eval(self, request, context, vmmanage):
        """

        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return vmmanage.run_eval(request.submissionFile, request.inputDatasetName, request.inputRunPath,
                                 request.outputDirName, request.sandboxed, request.optionalParameters)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    listen_addr = '[::]:' + grpc_port
    server.add_insecure_port(listen_addr)
    server.start()
    logger.info("Starting tira-host server on %s", listen_addr)
    server.wait_for_termination()


if __name__ == '__main__':
    fileConfig('conf/logging_config.ini')
    serve()
