#!/usr/bin/env python
import subprocess
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

from proto import tira_host_pb2, tira_host_pb2_grpc
from proto import TiraClientWebMessages_pb2 as modelpb
from tira_model import FileDatabase
from grpc_client import TiraHostClient
import vm_manage


config = ConfigParser()
config.read('conf/grpc_service.ini')
grpc_port = config.get('main', 'grpc_port')
tira_application_host = config.get('main', 'tira_application_host')
tira_application_grpc_port = config.get('main', 'tira_application_grpc_port')
tira_log_path = config.get('main', 'tira_log_path')

fileConfig("conf/logging_config.ini", defaults={'filename': f"{tira_log_path}{socket.gethostname()}.log"},
           disable_existing_loggers=False)
logger = logging.getLogger()

if config.get('main', 'connect_to_debug_server') == 'True':
    try:
        import pydevd_pycharm
        pydevd_pycharm.settrace('host.docker.internal', port=4200,  stdoutToServer=True, stderrToServer=True)
    except Exception as e:
        logger.debug('Debug server is not reachable.')

grpc_client = TiraHostClient(tira_application_host, tira_application_grpc_port)
transactions = {}
vms = {}


class TiraHostService(tira_host_pb2_grpc.TiraHostService):
    def __init__(self):
        def call():
            """
            Start a background thread that makes heartbeat calls to tira-application.
            """
            while True:
                time.sleep(2 * 60)
                self.heartbeat()

        self.model = FileDatabase(on_modified_callback=self.load_vms_list)
        self.load_vms_list()

        thread = threading.Thread(target=call)
        thread.start()

    def load_vms_list(self):
        logger.info("Loading existing vms from vboxmanage, this may take a while...")
        vm_id_list =  []

        shell_command = f"vboxmanage list vms"
        logger.debug(f"Execute {shell_command}")
        p = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = p.communicate()
        output = out.decode('utf-8')
        if p.returncode != 0:
            logger.error(f"load_vms_list() method finished with error: \n" + output)

        for line in output.split('\n'):
            if not line: continue
            vm_name_full = line.split(' ')[0].strip('\"')
            vm_id = vm_name_full.split("-tira-")[0][:-3]
            if vm_id not in vms:
                vm_id_list.append(vm_name_full.split("-tira-")[0][:-3])

        for vm_id in vm_id_list:
            if vm_id in vms:
                continue
            vm = self.model.get_vm_by_id(vm_id)
            if vm is None:
                logger.error(f"VM '{vm_id}' is not in users.prototext")
                continue
            vms[vm_id] = vm_manage.VirtualMachine(vm)
            logger.info(f"VM '{vm_id}' (state: {vms[vm_id].state}) was loaded")

    def heartbeat(self):
        # todo: call tira-application.set_state(state, vmId) for all vms on the current host?
        pass

    def _get_vm(self, vm_id, context) -> vm_manage.VirtualMachine:
        if vm_id not in vms:
            self.load_vms_list()

        vm = vms.get(vm_id, None)
        if vm is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            msg = f"VM {vm_id} not found."
            context.set_details(msg)
            raise Exception(msg)

        return vm

    def _create_submission_file(self, request, vm, evaluator=None):
        """

        :param request:
        :return:
        """
        if evaluator:
            submission = {'user': vm.user_name, 'os': "ubuntu", 'host': vm.host, 'sshport': vm.ssh_port,
                          'userpw': vm.user_password, 'workingDir': evaluator['working_dir'],
                          'cmd': evaluator['command']}
        else:
            software = self.model.get_software(request.taskId, vm.vm_id, request.softwareId)
            submission = {'user': vm.user_name, 'os': "ubuntu", 'host': vm.host, 'sshport': vm.ssh_port,
                          'userpw': vm.user_password, 'workingDir': software['working_directory'],
                          'cmd': software['command']}

        submission_filename = f"{vm.vm_id}-submission-{request.runId.runId}.txt"
        submission_file_path = self.model.get_submissions_dir(vm.vm_id) / submission_filename
        with open(submission_file_path, "w") as f:
            for k, v in submission.items():
                f.write(f'{k}="{v}"\n')

        return submission_filename

    def vm_backup(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)

        return vm.backup(request.vmId, request)

    def vm_create(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """
        vm = vm_manage.VirtualMachine(request)
        vms[vm.vm_id] = vm_manage.VirtualMachine(vm)

        return vm.create(request.transaction.transactionId, request)

    def vm_delete(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)
        response = vm.delete(request.transaction.transactionId, request)
        vms.pop(vm.vm_id)

        return response

    def vm_info(self, request, context, cached=False):
        """

        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)

        if not cached:
            vm.info()

        response = tira_host_pb2.VmInfo(transaction=tira_host_pb2.Transaction(
            status=tira_host_pb2.Status.SUCCESS,
            message="Host received vm-info request",
            transactionId=str(uuid.uuid4())
        ))

        response.guestOs = vm.guest_os
        response.memorySize = vm.memory_size
        response.numberOfCpus = vm.number_of_cpus
        response.state = vm.state
        response.sshPort = vm.ssh_port
        response.sshPortStatus = vm.ssh_port_status
        response.rdpPortStatus = vm.rdp_port_status
        response.rdpPort = vm.rdp_port
        response.host = vm.host
        response.vmId = vm.vm_id
        response.userName = vm.user_name
        response.initialUserPw = vm.user_password
        response.ip = vm.ip

        return response

    def vm_list(self, request, context):
        response = tira_host_pb2.VmList(transaction=request.transaction,
                                        vmsInfo=[self.vm_info({'vmId': vm.vm_id}, context, cached=True) for vm in vms])
        return response

    def vm_shutdown(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)
        return vm.shutdown(request.transaction.transactionId, request)

    def vm_snapshot(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)

        return vm.spanshot(request.transaction.transactionId, request)

    def vm_start(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)

        return vm.start(request.transaction.transactionId, request)

    def vm_stop(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)

        return vm.stop(request.transaction.transactionId, request)

    def run_execute(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.runId.vmId, context)

        self.model.create_run(request.runId.vmId, request.softwareId, request.runId.runId, request.runId.datasetId,
                         request.inputRunId.runId, request.taskId)

        submission_filename = self._create_submission_file(request, vm)

        return vm.run_execute(request.transaction.transactionId, request, submission_filename)

    def run_eval(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.runId.vmId, context)
        vm.info()

        evaluator = self.model.get_evaluator(request.runId.datasetId)

        self.model.create_run(request.inputRunId.vmId, evaluator['evaluator_id'], request.runId.runId, request.runId.datasetId,
                         request.inputRunId.runId, evaluator['task_id'])

        submission_filename = self._create_submission_file(request, vm, evaluator=evaluator)

        return vm.run_eval(request.transaction.transactionId, request,
                           self.model.get_run_dir(request.inputRunId.datasetId, request.inputRunId.vmId,
                                             request.inputRunId.runId), submission_filename, evaluator['task_id'])

    def run_abort(self, request, context):
        """

        :param request:
        :param context:
        :return:
        """
        vm = self._get_vm(request.vmId, context)

        return vm.run_abort(request.transaction.transactionId, request)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=100))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    listen_addr = '[::]:' + grpc_port
    server.add_insecure_port(listen_addr)
    server.start()
    logger.info("Starting host server on %s", listen_addr)
    server.wait_for_termination()


if __name__ == '__main__':
    fileConfig("conf/logging_config.ini", defaults={'filename': f"{tira_log_path}{socket.gethostname()}.log"},
               disable_existing_loggers=False)
    logger = logging.getLogger()
    serve()
