#!/usr/bin/env python
"""
    GrpcClient to make gRPC calls to the dockerized tira-host running a VM.
"""
import logging

from django.conf import settings
import grpc
from google.protobuf.empty_pb2 import Empty
from .transitions import TransactionLog, EvaluationLog
from uuid import uuid4
from functools import wraps

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


def auto_transaction(msg):
    """ when we gat a Transaction message as response and it fails, automatically terminate the Transaction
    in the TransactionLog """
    def attribute_decorator(func):
        @wraps(func)
        def func_wrapper(self, *args, **kwargs):
            grpc_transaction = new_transaction(f"initialized {msg} of {kwargs['vm_id']}")
            message_suffix = '-'.join([a for a in args if isinstance(a, str)])

            response = func(self, *args, transaction=grpc_transaction, **kwargs)
            if response.status == 1:
                _ = TransactionLog.objects.filter(transaction_id=response.transactionId).update(
                    completed=True,
                    last_status=str(response.status),
                    last_message=f"{response.message}: {message_suffix}")
            return response

        return func_wrapper

    return attribute_decorator


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

    def vm_create(self, vm_id, ova_file, user_id, hostname):
        """ TODO test and comment """
        grpc_transaction = new_transaction(f"initialized vm create of {vm_id}")

        response = self.stub.vm_create(
            tira_host_pb2.VmCreate(transaction=grpc_transaction,
                                   vmId=vm_id, userId=user_id, ovaFile=ova_file, host=hostname))

        logger.debug("Application received vm-create response: " + str(response.message))
        return response

    @auto_transaction("vm-start")
    def vm_start(self, vm_id, transaction):
        response = self.stub.vm_start(tira_host_pb2.VmId(transaction=transaction, vmId=vm_id))
        logger.debug("Application received vm-start response: " + str(response.message))
        return response

    @auto_transaction("vm-stop")
    def vm_stop(self, vm_id, transaction):
        response = self.stub.vm_stop(tira_host_pb2.VmId(transaction=transaction, vmId=vm_id))
        logger.debug("Application received vm-stop response: " + str(response.message))
        return response

    @auto_transaction("vm-shutdown")
    def vm_shutdown(self, vm_id, transaction):
        response = self.stub.vm_shutdown(tira_host_pb2.VmId(transaction=transaction, vmId=vm_id))
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

    @auto_transaction("run-execute")
    def run_execute(self, vm_id, dataset_id, run_id, input_run_vm_id, input_run_dataset_id, input_run_run_id, task_id,
                    software_id, transaction):
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

        logger.info("Application starts a run-execute")
        grpc_run_id = tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id)
        grpc_input_run_id = tira_host_pb2.RunId(vmId=input_run_vm_id, datasetId=input_run_dataset_id,
                                                runId=input_run_run_id)

        response = self.stub.run_execute(tira_host_pb2.RunDetails(transaction=transaction,
                                                                  runId=grpc_run_id, inputRunId=grpc_input_run_id,
                                                                  taskId=task_id, softwareId=software_id))

        logger.debug("Application received run-execute response: " + str(response.message))
        return response

    @auto_transaction("run-eval")
    def run_eval(self, vm_id, dataset_id, run_id, working_dir, command,
                 input_run_vm_id, input_run_dataset_id, input_run_run_id, optional_parameters, transaction):
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
        grpc_run_id = tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id)
        grpc_input_run_id = tira_host_pb2.RunId(vmId=input_run_vm_id, datasetId=input_run_dataset_id,
                                                runId=input_run_run_id)
        response = self.stub.run_eval(tira_host_pb2.RunDetails(transaction=transaction,
                                                               runId=grpc_run_id, workingDir=working_dir,
                                                               command=command, inputRunId=grpc_input_run_id,
                                                               optionalParameters=optional_parameters))
        if response.status == 0:
            t = TransactionLog.objects.get(transaction_id=transaction.transactionId)
            _ = EvaluationLog.objects.update_or_create(vm_id=vm_id, run_id=run_id, running_on=vm_id,
                                                       transaction=t)
        logger.debug("Application received run-eval response: " + str(response.message))
        return response

    @auto_transaction("run-abort")
    def run_abort(self, vm_id, transaction):
        """ Abort a currently ongoing run."""
        response = self.stub.run_abort(tira_host_pb2.VmId(transaction=transaction, vmId=vm_id))
        logger.debug("Application received run-abort response: " + str(response.message))
        return response
