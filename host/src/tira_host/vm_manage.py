#!/usr/bin/env python
import os
import signal
import threading
import uuid
from configparser import ConfigParser
from datetime import datetime
from functools import wraps
import logging
import re
import socket
import subprocess

from grpc_client import TiraHostClient
from proto import tira_host_pb2, tira_host_pb2_grpc
from proto import TiraClientWebMessages_pb2 as modelpb


config = ConfigParser()
config.read('conf/grpc_service.ini')
tira_application_host = config.get('main', 'tira_application_host')
tira_application_grpc_port = config.get('main', 'tira_application_grpc_port')

logger = logging.getLogger(__name__)

# Transition is powering_on (3), powering_off (4), sandboxing (5), unsandboxing (6), executing (7)
transition_states = {3, 4, 5, 6, 7}
# Stable is undefined (0), running (1), powered_off (2), or archived (8)
stable_state = {0, 1, 2, 8}

grpc_client = TiraHostClient(tira_application_host, tira_application_grpc_port)


def async_api(wrapped_function):
    """
    Manage transactions, make callbacks to tira-application on complete.
    :param wrapped_function:
    :return:
    """

    @wraps(wrapped_function)
    def new_function(vm, transaction_id, request, *args, **kwargs):
        def task_call():
            try:
                wrapped_function(vm, transaction_id, request, *args, **kwargs)
                logger.debug(
                    f"Transaction {transaction_id} request ({wrapped_function.__name__}) finished successfully")
                grpc_client.complete_transaction(transaction_id=transaction_id,
                                                 status=tira_host_pb2.Status.SUCCESS,
                                                 message=f"{wrapped_function.__name__} command finished successfully")
            except Exception as e:
                logger.error(
                    f"Transaction {transaction_id} request failed (function {wrapped_function.__name__}): {str(e)}")
                grpc_client.complete_transaction(transaction_id=transaction_id,
                                                 status=tira_host_pb2.Status.FAILED,
                                                 message=f"Transaction {transaction_id} request ({wrapped_function.__name__}) failed: {str(e)}")

        logger.debug(f"Transaction ({transaction_id}) received. (function: {wrapped_function.__name__}, request: {str(request)})")

        t = threading.Thread(target=task_call, args=())
        t.start()

    return new_function


class VirtualMachine(object):
    def check_state(allowed_states):
        def decorator(func):
            @wraps(func)
            def wrapper(self, transaction_id, request, *args, **kwargs):
                if self.state not in allowed_states:
                    return tira_host_pb2.Transaction(
                        status=tira_host_pb2.Status.FAILED,
                        transactionId=transaction_id,
                        message=f"Not allowed for current vm state ({self.state})"
                    )

                elif self.transaction_id is not None:
                    return tira_host_pb2.Transaction(
                        status=tira_host_pb2.Status.FAILED,
                        transactionId=transaction_id,
                        message=f"Another transaction ({self.transaction_id}) is already running"
                    )
                else:
                    func(self, transaction_id, request, *args, **kwargs)

                # Respond right away with Transaction message to tira-application request
                response_transaction = tira_host_pb2.Transaction()
                response_transaction.transactionId = str(uuid.uuid4())
                response_transaction.status = tira_host_pb2.Status.SUCCESS
                response_transaction.message = f"Host accepted the transaction {transaction_id} request"
                logger.debug(
                    f"Confirmation for transactionId {str(request.transaction.transactionId)} ({func.__name__}) sent")

                return response_transaction

            return wrapper
        return decorator

    def run_script(self, *args, script_name="tira", command=""):
        """
        :param script_name: name of the script to execute
        :param command: name of the command (e.g. tira command vm-start)
        :param args: list of arguments for tira command
        :return:
        """
        shell_command = f"{script_name} {command} " + " ".join([f"'{a}'" for a in args])
        logger.debug(f"Execute {shell_command}")
        p = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.pid = p.pid
        out, err = p.communicate()
        output = out.decode('utf-8')
        self.pid = None

        if p.returncode != 0:
            logger.error(f"{command} command finished with error: \n" + output)

        return p.returncode, output

    def __init__(self, vm: modelpb.User):
        self.state = 0
        self.vm_id = vm.virtualMachineId
        self.user_name = vm.userName
        self.user_password = vm.userPw
        self.vm_name = vm.vmName
        self.guest_os = None
        self.memory_size = None
        self.number_of_cpus = None
        self.ssh_port = vm.portSsh
        self.ssh_port_status = False
        self.rdp_port = vm.portRdp
        self.rdp_port_status = False
        self.host = vm.host
        self.transaction_id = None
        self.pid = None

        self.state = self._update_info()

    def _set_state(self, state):
        self.state = state
        grpc_client.set_state(self.vm_id, self.state, self.transaction_id)

    def _update_info(self):
        vm_state = None
        return_code, output = self.run_script(self.vm_name, command="vm-info")
        for line in output.split('\n'):
            if line.startswith("Guest OS:"):
                self.guest_os = line.split(": ")[1].strip()
            elif line.startswith("Memory size"):
                self.memory_size = line.split()[2].strip()
            elif line.startswith("Number of CPUs:"):
                self.number_of_cpus = line.split(": ")[1].strip()
            elif line.startswith("State:"):
                vm_state = re.sub(".\\d+\\)", ")", line.split(": ")[1].strip())

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            self.ssh_port_status = 1 if sock.connect_ex((self.host, int(self.ssh_port))) == 0 else 0
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            self.rdp_port_status = 1 if sock.connect_ex((self.host, int(self.rdp_port))) == 0 else 0

        state = self.state
        if vm_state and vm_state.startswith("running"):
            state = tira_host_pb2.State.RUNNING
        elif vm_state and vm_state.startswith("powered off"):
            state = tira_host_pb2.State.POWERED_OFF
        elif vm_state is None:
            state = tira_host_pb2.State.UNDEFINED

        return state

    @check_state({0})
    @async_api
    def create(self, transaction_id, request):
        """

        :param transaction_id:
        :param request:
        :return:
        """
        self.transaction_id = transaction_id
        retcode, output = self.run_script(request.ovaFile, self.user_name, command="vm-create")
        grpc_client.set_state(self.vm_id, self.state, self.transaction_id)
        self._update_info()
        self.transaction_id = None

        return retcode, output

    @check_state({1,2})
    @async_api
    def delete(self, transaction_id, request):
        """

        :param transaction_id:
        :param request:
        :return:
        """
        self.transaction_id = transaction_id
        retcode, output = self.run_script(self.vm_name, command="vm-delete")
        grpc_client.set_state(self.vm_id, self.state, self.transaction_id)
        self.transaction_id = None

        return retcode, output

    @check_state({2})
    @async_api
    def backup(self, transaction_id, request):
        """

        :param transaction_id:
        :param request:
        :return:
        """
        self.transaction_id = transaction_id
        retcode, output = self.run_script(self.vm_name, command="vm-backup")
        grpc_client.set_state(self.vm_id, self.state, self.transaction_id)
        self.transaction_id = None

        return retcode, output

    def info(self):
        self.state = self._update_info()

    def _sandbox(self, transaction_id, output_dir_name, mount_test_data):
        """
        :param output_dir_name: timestamp format '2021-09-29-12-50-02'
        :param mount_test_data:
        :return:
        """
        self.transaction_id = transaction_id
        self._set_state(5)
        retcode, output = self.run_script(self.vm_name, output_dir_name, mount_test_data, command="vm-sandbox")
        self.transaction_id = None

        return retcode, output

    @check_state({1})
    @async_api
    def shutdown(self, transaction_id, request):
        """

        :param transaction_id:
        :return:
        """
        self.transaction_id = transaction_id
        self._set_state(4)
        retcode, output = self.run_script(self.vm_name, command="vm-shutdown")
        self._set_state(self._update_info())
        self.transaction_id = None

        return retcode, output

    # def _snapshot(self, transaction_id):
    #     """
    #
    #     :param transaction_id:
    #     :return:
    #     """
    #     self.transaction_id = transaction_id
    #     timestamp = f"{self.vm_name}-{datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ')}"
    #     retcode, output = self.run_script(self.vm_name, timestamp, command="vm-snapshot")
    #     grpc_client.set_state(self.vm_id, self.state, self.transaction_id)
    #     self.transaction_id = None
    #
    #     return retcode, output

    @check_state({2})
    @async_api
    def start(self, transaction_id, request):
        """

        :param transaction_id:
        :return:
        """
        self.transaction_id = transaction_id
        self._set_state(3)
        retcode, output = self.run_script(self.vm_name, command="vm-start")
        self._set_state(1)
        self.transaction_id = None

        return retcode, output

    @check_state({1,3,4})
    @async_api
    def stop(self, transaction_id, request):
        """

        :param transaction_id:
        :param request:
        :return:
        """
        self.transaction_id = transaction_id
        self._set_state(4)
        retcode, output = self.run_script(self.vm_name, command="vm-stop")
        self._set_state(2)
        self.transaction_id = None

        return retcode, output

    def _unsandbox(self, transaction_id):
        self.transaction_id = transaction_id
        self._set_state(6)
        retcode, output = self.run_script(self.vm_name, command="vm-unsandbox")
        self._set_state(1)
        self.transaction_id = None

        return retcode, output

    @check_state({1})
    @async_api
    def run_execute(self, transaction_id, request, submission_filename):
        """

        :param submission_filename:
        :param transaction_id:
        :param request:
        :return:
        """
        self.transaction_id = transaction_id

        self._set_state(4)
        self.run_script(self.vm_name, command="vm-stop")
        self._set_state(2)
        self._sandbox(transaction_id, 'auto', "true" if "test" in request.inputRunId.datasetId else "false")

        self._set_state(7)
        retcode, output = self.run_script(submission_filename, request.runId.datasetId, 'none',
                                          request.runId.runId, command="run-execute-new")

        self._unsandbox(transaction_id)
        self.transaction_id = None

        return retcode, output

    @check_state({1})
    @async_api
    def run_eval(self, transaction_id, request, input_run_path, submission_filename):
        """

        :param submission_filename:
        :param transaction_id:
        :param request:
        :param input_run_path:
        :return:
        """
        self.transaction_id = transaction_id
        self._set_state(7)
        retcode, output = self.run_script(submission_filename, request.runId.datasetId,
                                          input_run_path, request.runId.runId,
                                          command="run-eval-new")

        self.transaction_id = None

        return retcode, output

    @check_state({7})
    @async_api
    def run_abort(self, transaction_id, request):
        if self.pid is not None:
            os.killpg(os.getpgid(self.pid), signal.SIGTERM)
            self._unsandbox(transaction_id)
        else:
            raise Exception(f"No active runs to abort")
