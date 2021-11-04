#!/usr/bin/env python
"""
    GrpcClient to make gRPC calls to the dockerized tira-host running a VM.
"""
import logging

from django.conf import settings
import grpc
from google.protobuf.empty_pb2 import Empty
from .transitions import TransactionLog
from uuid import uuid4

from .proto import tira_host_pb2, tira_host_pb2_grpc

logger = logging.getLogger("tira")
grpc_port = settings.HOST_GRPC_PORT


def new_transaction(message):
    """ A convenience method to create a new transaction with a :@param message:, save it to the database,
    and wrap it in a protobuf Transaction to be returned.
    """
    transaction_id = str(uuid4())
    _ = TransactionLog.objects.create(transaction_id=transaction_id, completed=False, last_message=message)
    return tira_host_pb2.Transaction(transactionId=transaction_id)


class GrpcClient:
    """ Main class for the Application's GRPC client. This client makes calls to a server running on a host specified
    by it's hostname """
    def __init__(self, hostname):
        """ A channel is opened at init time and closed on deletion. Try not to store these objects for long. """
        self.hostname = hostname
        self.channel = grpc.insecure_channel(hostname + ':' + str(grpc_port))
        self.stub = tira_host_pb2_grpc.TiraHostServiceStub(self.channel)

    def __del__(self):
        self.channel.close()

    def vm_create(self, ova_file, vm_id, user_id, hostname):
        """ TODO test and comment """
        grpc_transaction = new_transaction(f"initialized vm create of {vm_id}")

        response = self.stub.vm_create(
            tira_host_pb2.VmCreate(transaction=grpc_transaction,
                                   vmId=vm_id, userId=user_id, ovaFile=ova_file, host=hostname))
        logger.debug("Application received vm-create response: " + str(response.message))
        return response

    def vm_start(self, vm_id):
        grpc_transaction = new_transaction(f"initialized vm start of {vm_id}")
        response = self.stub.vm_start(tira_host_pb2.VmId(transaction=grpc_transaction, vmId=vm_id))
        logger.debug("Application received vm-start response: " + str(response.message))
        return response

    def vm_stop(self, vm_id):
        grpc_transaction = new_transaction(f"initialized vm stop of {vm_id}")
        response = self.stub.vm_stop(tira_host_pb2.VmId(transaction=grpc_transaction, vmId=vm_id))
        logger.debug("Application received vm-stop response: " + str(response.message))
        return response

    def vm_shutdown(self, vm_id):
        grpc_transaction = new_transaction(f"initialized vm shutdown of {vm_id}")
        response = self.stub.vm_shutdown(tira_host_pb2.VmId(transaction=grpc_transaction, vmId=vm_id))
        logger.debug("Application received vm-shutdown response: " + str(response.message))
        return response

    def vm_info(self, vm_id):
        response = self.stub.vm_info(tira_host_pb2.VmId(vmId=vm_id))
        logger.debug("Application received vm-info response: " + str(response.transaction.message))
        return response

    def vm_list(self):
        response = self.stub.vm_list(Empty)
        logger.debug("Application received vm-list response: " + str(response.transaction.message))
        return response

    def run_execute(self, vm_id, dataset_id, run_id, input_run_vm_id, input_run_dataset_id, input_run_run_id, task_id,
                    software_id):
        """ Initiates a run: the execution of a software to produce output.
        :param software_id:
        :param task_id:
        :param vm_id: ID of the vm to run the command below
        :param dataset_id: ID of the dataset
        :param run_id: ID of the run
        :param working_dir: WD of the command below
        :param command: command to be run on the vm
        :param input_run_vm_id: (optional) vm that produced additional input as a run
        :param input_run_dataset_id: (optional) ID of the dataset of the additional input
        :param input_run_run_id: (optional) ID of the additional input (the input run )
        :param optional_parameters: Other parameters the software might expect
        """

        grpc_transaction = new_transaction(f"initialized run execute of {vm_id} with run_id {run_id}")
        grpc_run_id = tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id)
        grpc_input_run_id = tira_host_pb2.RunId(vmId=input_run_vm_id, datasetId=input_run_dataset_id,
                                                runId=input_run_run_id)

        response = self.stub.run_execute(tira_host_pb2.RunDetails(transaction=grpc_transaction,
                                                                  runId=grpc_run_id, inputRunId=grpc_input_run_id,
                                                                  taskId=task_id, softwareId=software_id))
        logger.debug("Application received run-execute response: " + str(response.message))
        return response

    def run_eval(self, vm_id, dataset_id, run_id, working_dir, command,
                 input_run_vm_id, input_run_dataset_id, input_run_run_id, optional_parameters):
        """ Initiates the evaluation of a prior run.
        :param vm_id: ID of the vm that can run the evaluation
        :param dataset_id: ID of the dataset
        :param run_id: ID of the evaluation
        :param working_dir: WD of the evaluator
        :param command: command to run the evaluator
        :param input_run_vm_id: id of the vm that produced the run (this exists to find the run output)
        :param input_run_dataset_id: ID of the dataset
        :param input_run_run_id: ID of the run that should be evaluated
        :param optional_parameters: Other parameters the evaluator might expect
        """
        grpc_transaction = new_transaction(f"initialized eval of run_id {input_run_run_id} on {vm_id}")
        grpc_run_id = tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id)
        grpc_input_run_id = tira_host_pb2.RunId(vmId=input_run_vm_id, datasetId=input_run_dataset_id,
                                                runId=input_run_run_id)
        response = self.stub.run_eval(tira_host_pb2.RunDetails(transaction=grpc_transaction,
                                                               runId=grpc_run_id, workingDir=working_dir,
                                                               command=command, inputRunId=grpc_input_run_id,
                                                               optionalParameters=optional_parameters))
        logger.debug("Application received run-eval response: " + str(response.message))
        return response

    def run_abort(self, vm_id):
        grpc_transaction = new_transaction(f"initialized run abort on {vm_id}")
        response = self.stub.run_abort(tira_host_pb2.VmId(transaction=grpc_transaction, vmId=vm_id))
        logger.debug("Application received run-abort response: " + str(response.message))
        return response
