#!/usr/bin/env python

"""
    GrpcClient to make gRPC calls to the dockerized tira-host running a VM.
"""

from django.conf import settings
import grpc
from google.protobuf.empty_pb2 import Empty

from .proto import tira_host_pb2, tira_host_pb2_grpc

grpc_port = settings.HOST_GRPC_PORT


class GrpcClient:
    def __init__(self, hostname):
        self.hostname = hostname
        self.channel = grpc.insecure_channel(hostname + ':' + str(grpc_port))
        self.stub = tira_host_pb2_grpc.TiraHostServiceStub(self.channel)

    def __del__(self):
        self.channel.close()

    def vm_create(self, ova_file, vm_id, bulk_id=None):
        response = self.stub.vm_create(
            tira_host_pb2.VmCreate(vmId=vm_id, userId=vm_id, ovaFile=ova_file, bulkCommandId=bulk_id))
        return response

    def vm_start(self, vm_id):
        response = self.stub.vm_start(tira_host_pb2.VmId(vmId=vm_id))
        print("VM-Start response: " + str(response.status))
        return response

    def vm_stop(self, vm_id):
        response = self.stub.vm_stop(tira_host_pb2.VmId(vmId=vm_id))
        print("Client received: " + str(response))
        return response

    def vm_shutdown(self, vm_id):
        response = self.stub.vm_shutdown(tira_host_pb2.VmId(vmId=vm_id))
        print("Client received: " + str(response))
        return response

    def vm_info(self, vm_id):
        response_vm_info = self.stub.vm_info(tira_host_pb2.VmId(vmId=vm_id))
        print("got vm-info reponse")
        return response_vm_info

    def vm_list(self):
        response = self.stub.vm_list(Empty)
        print("Client received: " + str(response))
        return response

    def run_execute(self, vm_id, dataset_id, run_id, working_dir, command,
                    input_run_vm_id, input_run_dataset_id, input_run_run_id, optional_parameters):
        """ Initiates a run: the execution of a software to produce output.
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
        grpc_run_id = tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id)
        grpc_input_run_id = tira_host_pb2.RunId(vmId=input_run_vm_id, datasetId=input_run_dataset_id,
                                                runId=input_run_run_id)

        response = self.stub.run_execute(tira_host_pb2.RunDetails(runId=grpc_run_id, workingDir=working_dir,
                                                                  command=command, inputRunId=grpc_input_run_id,
                                                                  optionalParameters=optional_parameters))
        print("Client received: " + str(response))
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
        grpc_run_id = tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id)
        grpc_input_run_id = tira_host_pb2.RunId(vmId=input_run_vm_id, datasetId=input_run_dataset_id,
                                                runId=input_run_run_id)
        response = self.stub.run_eval(tira_host_pb2.RunDetails(runId=grpc_run_id, workingDir=working_dir,
                                                               command=command, inputRunId=grpc_input_run_id,
                                                               optionalParameters=optional_parameters))

        print("Client received: " + str(response))
        return response
