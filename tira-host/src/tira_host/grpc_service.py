#!/usr/bin/env python
from concurrent import futures
from configparser import ConfigParser
from datetime import datetime
from functools import wraps
from google.protobuf.json_format import MessageToDict
import grpc
from grpc import aio
import logging
from logging.config import fileConfig
import os
import re
import socket
import signal
import threading
import time
import uuid
import vm_manage

from proto import tira_host_pb2, tira_host_pb2_grpc
from proto import TiraClientWebMessages_pb2 as modelpb
from tira_model import FileDatabase
from grpc_client import TiraHostClient

logging.config.fileConfig("conf/logging_config.ini")
logger = logging.getLogger()

commands = {}
model = FileDatabase()

parser = ConfigParser()
parser.read('conf/grpc_service.ini')
grpc_port = parser.get('main', 'grpc_port')
tira_application_host = parser.get('main', 'tira_application_host')
tira_application_grpc_port = parser.get('main', 'tira_application_grpc_port')

grpc_client = TiraHostClient(tira_application_host, tira_application_grpc_port)


def async_api(wrapped_function):
    """
    Manages command queue.
    :param wrapped_function:
    :return:
    """

    @wraps(wrapped_function)
    def new_function(*args, **kwargs):
        def task_call():
            try:
                # TODO: check solution with logger
                # Set logger handler file for the command output
                # vmmanage.logger.handlers.clear()
                # vmmanage.logger.addHandler(logging.FileHandler(command.logFile))

                vmmanage = vm_manage.VMManage()
                commands[transaction_id]['return_code'] = wrapped_function(*args, vmmanage=vmmanage)
                logger.debug(f"Transaction {transaction_id} request (function {wrapped_function.__name__}) finished.")
            except Exception as e:
                logger.error(f"Transaction {transaction_id} request failed (function {wrapped_function.__name__}): {str(e)}")
                # todo: if tira script fails (return_code != 0), we need to reset the vm state in TransitionLog and/or trigger new vm_info request
                grpc_client.complete_transaction(transaction_id=transaction_id,
                                                 status=tira_host_pb2.Status.FAILED,
                                                 message=f"Transaction {transaction_id} request failed: {str(e)}")
            finally:
                commands.pop(transaction_id, None)

        request = args[1]
        transaction_id = request.transaction.transactionId
        logger.debug(f"{wrapped_function.__name__} call. Server received {str(request)}.")

        # Record the task, and then launch it
        commands[transaction_id] = {'command_thread': threading.Thread(target=task_call, args=())}
        commands[transaction_id]['command_thread'].start()

        # Respond right away with Transaction message to tira-application request
        response_transaction = tira_host_pb2.Transaction()
        response_transaction.transactionId = str(uuid.uuid4())
        response_transaction.status = tira_host_pb2.Status.SUCCESS
        response_transaction.message = f"Host accepted the transaction {transaction_id} request."

        return response_transaction

    return new_function


class TiraHostService(tira_host_pb2_grpc.TiraHostService):
    def __init__(self):
        def call():
            """
            Start a background thread that makes heartbeat calls to tira-application.
            """
            while True:
                time.sleep(2 * 60)
                self.heartbeat()

        thread = threading.Thread(target=call)
        thread.start()

    def heartbeat(self):
        # todo: call tira-application.set_state(state, vmId) for all vms on the current host?
        pass

    def _get_vm(self, vm_id, context):
        vm = model.get_vm_by_id(vm_id)
        if not vm:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("VM not found.")
            raise Exception("VM not found.")

        return vm

    @async_api
    def vm_backup(self, request, context, vmmanage):
        """

        :param vmmanage:
        :param request:
        :param context:
        :return:
        """
        return_code, output = vmmanage.vm_backup(request.vmId)
        grpc_client.set_state(request.vmId, tira_host_pb2.State.ARCHIVED, request.transaction.transactionId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"vm_backup command finished successfully.")
        return return_code

    @async_api
    def vm_create(self, request, context, vmmanage):
        """

        :param vmmanage:
        :param request:
        :param context:
        :return:
        """

        return_code, output = vmmanage.vm_create(request.ovaFile, request.userName)
        grpc_client.set_state(request.vmId, tira_host_pb2.State.RUNNING, request.transaction.transactionId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"vm_create command finished successfully.")
        return return_code

    @async_api
    def vm_delete(self, request, context, vmmanage):
        """

        :param vmmanage:
        :param request:
        :param context:
        :return:
        """
        return_code, output = vmmanage.vm_delete(request.vmId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"vm_delete command finished successfully.")
        return return_code

    def vm_info(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)

        vm_state = None
        vmmanage = vm_manage.VMManage()
        return_code, output = vmmanage.vm_info(vm.vmName)
        response = tira_host_pb2.VmInfo(transaction=tira_host_pb2.Transaction(
            status=tira_host_pb2.Status.SUCCESS,
            message="host received vm-info request",
            transactionId=str(uuid.uuid4().hex + "_vm_info")
        ))
        for line in output.split('\n'):
            if line.startswith("Guest OS:"):
                response.guestOs = line.split(": ")[1].strip()
            elif line.startswith("Memory size"):
                response.memorySize = line.split()[2].strip()
            elif line.startswith("Number of CPUs:"):
                response.numberOfCpus = line.split(": ")[1].strip()
            elif line.startswith("State:"):
                vm_state = re.sub(".\\d+\\)", ")", line.split(": ")[1].strip())

        response.sshPort = vm.portSsh
        response.rdpPort = vm.portRdp
        response.host = vm.host

        if response.sshPort and response.rdpPort:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                response.sshPortStatus = 1 if sock.connect_ex((vm.host, int(vm.portSsh))) == 0 else 0
                response.rdpPortStatus = 1 if sock.connect_ex((vm.host, int(vm.portRdp))) == 0 else 0

        # TODO we should return here fine grained information about the state before this foes live.
        # todo: check which commands are executing at the moment
        if vm_state and vm_state.startswith("running"):
            response.state = tira_host_pb2.State.RUNNING
        elif vm_state:
            response.state = tira_host_pb2.State.POWERED_OFF
        else:
            response.state = tira_host_pb2.State.UNDEFINED

        # response.transaction = tira_host_pb2.Transaction(
        #     status=tira_host_pb2.Status.SUCCESS,
        #     message="host received vm-info request",
        #     transactionId=str(uuid.uuid4().hex + "_vm_info")
        # )

        return response

    def vm_list(self, context, vmmanage):
        output = ""
        vmmanage.vm_list(output)
        return output

    def _vm_sandbox(self, vmmanage, vm_id, output_dir_name, mount_test_data):
        """
        :param vm_id:
        :param vmmanage:
        :return:
        """
        #        if [[ "$inputDataset" == *"test"* ]]; then
        #            mountTestData=true
        #        else
        #            mountTestData=false
        #        fi
        return_code, output = vmmanage.vm_sandbox(vm_id, output_dir_name, mount_test_data)
        return return_code

    @async_api
    def vm_shutdown(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return_code, output = vmmanage.vm_shutdown(request.vmId)
        grpc_client.set_state(request.vmId, tira_host_pb2.State.POWERED_OFF, request.transaction.transactionId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"vm_shutdown command finished successfully.")
        return return_code

    @async_api
    def vm_snapshot(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        return_code, output = vmmanage.vm_create(request.ovaFile, request.userName)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"vm_create command finished successfully.")
        return return_code

    @async_api
    def vm_start(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        vm = self._get_vm(request.vmId, context)
        return_code, output = vmmanage.vm_start(vm.vmName)
        grpc_client.set_state(request.vmId, tira_host_pb2.State.RUNNING, request.transaction.transactionId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"vm_start command finished successfully.")

        return return_code

    @async_api
    def vm_stop(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        vm = self._get_vm(request.vmId, context)
        return_code, output = vmmanage.vm_stop(vm.vmName)
        grpc_client.set_state(request.vmId, tira_host_pb2.State.POWERED_OFF, request.transaction.transactionId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"vm_stop command finished successfully.")

        return return_code

    def _vm_unsandbox(self, vm_id, vmmanage):
        """
        :param vm_id:
        :param vmmanage:
        :return:
        """
        return_code, output = vmmanage.vm_unsandbox(vm_id)
        return return_code

    @async_api
    def run_execute(self, request, context, vmmanage):
        """
        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        vm = self._get_vm(request.runId.vmId, context)

        model.create_run(request.runId.vmId, request.softwareId, request.runId.runId, request.runId.datasetId,
                         request.inputRunId.runId, request.taskId)

        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.POWERING_OFF, request.transaction.transactionId)
        vmmanage.vm_stop(request.runId.vmId)
        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.POWERED_OFF, request.transaction.transactionId)
        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.SANDBOXING, request.transaction.transactionId)
        self._vm_sandbox(vmmanage, vm.vmName, 'auto', "true" if "test" in request.inputRunId.datasetId else "false")
        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.EXECUTING, request.transaction.transactionId)
        return_code, output = vmmanage.run_execute(vm.userName + ".prototext", request.runId.datasetId, 'none',
                                                   datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S'),
                                                   request.taskId, request.softwareId)
        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.UNSANDBOXING, request.transaction.transactionId)
        self._vm_unsandbox(vm.vmName, vmmanage)
        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.RUNNING, request.transaction.transactionId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"run_execute command finished successfully.")

        return return_code

    @async_api
    def run_eval(self, request, context, vmmanage):
        """

        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        vm = self._get_vm(request.runId.vmId, context)

        model.create_run(request.runId.vmId, request.softwareId, request.runId.runId, request.runId.datasetId,
                         request.inputRunId.runId, request.taskId)

        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.EXECUTING, request.transaction.transactionId)
        return_code, output = vmmanage.run_eval(vm.vmName + ".prototext", request.runId.datasetId,
                                                model.get_run_dir(request.runId.datasetId, request.runId.vmId,
                                                                  request.inputRunId.runId),
                                                datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S'))
        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.RUNNING, request.transaction.transactionId)
        grpc_client.complete_transaction(transaction_id=request.transaction.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"run_eval command finished successfully.")

        return return_code

    @async_api
    def run_abort(self, request, context, vmmanage):
        """

        :param request:
        :param context:
        :param vmmanage:
        :return:
        """
        vm = self._get_vm(request.runId.vmId, context)

        transaction_id = request.vmId.transactionId
        if transaction_id not in commands:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            msg = f"Transaction {transaction_id} not found."
            context.set_details(msg)
            raise Exception(msg)

        t = commands[transaction_id]['command_thread']
        os.killpg(os.getpgid(t.pid), signal.SIGTERM)
        commands.pop(transaction_id)

        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.UNSANDBOXING, request.vmId.transactionId)
        self._vm_unsandbox(vm.vmName, vmmanage)
        grpc_client.set_state(request.runId.vmId, tira_host_pb2.State.RUNNING, request.vmId.transactionId)
        grpc_client.complete_transaction(transaction_id=request.vmId.transactionId,
                                         status=tira_host_pb2.Status.SUCCESS,
                                         message=f"run_abort command finished successfully.")


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
