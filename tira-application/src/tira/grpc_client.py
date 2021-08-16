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

    def vm_create(self, ova_file, user_name, bulk_id=None):
        response = self.stub.vm_create(
            tira_host_pb2.VmDetails(vmId=user_name, userId=user_name, ovaFile=ova_file, bulkCommandId=bulk_id))
        return response.commandId

    def vm_start(self, vm_name):
        response = self.stub.vm_start(tira_host_pb2.VmDetails(vmId=vm_name))
        print("VM-Start response: " + str(response.status))
        return response

    def vm_stop(self, vm_name):
        response = self.stub.vm_stop(tira_host_pb2.VmDetails(vmId=vm_name))
        print("Client received: " + str(response))
        return response

    def vm_shutdown(self, vm_name):
        response = self.stub.vm_shutdown(tira_host_pb2.VmDetails(vmId=vm_name))
        print("Client received: " + str(response))
        return response

    def vm_info(self, vm_name):
        response_vm_info = self.stub.vm_info(tira_host_pb2.VmDetails(vmId=vm_name))
        print("got vm-info reponse")
        return response_vm_info

    def vm_list(self):
        response = self.stub.vm_list(Empty)
        print("Client received: " + str(response))
        return response

    def run_execute(self, submission_file, input_dataset_name, input_run_path, output_dir_name, sandboxed,
                    optional_parameters):
        # user, os, host, sshport, userpw, workingDir, cmd
        response = self.stub.run_execute(tira_host_pb2.RunDetails(submissionFile=submission_file,
                                                           inputDatasetId=input_dataset_name,
                                                           inputRunPath=input_run_path,
                                                           outputDirName=output_dir_name,
                                                           sandboxed=sandboxed,
                                                           optionalParameters=optional_parameters
                                                           ))
        print("Client received: " + str(response))
        return response

    def run_eval(self, submission_file, input_dataset_name, input_run_path, output_dir_name, sandboxed,
                 optional_parameters):
        response = self.stub.run_execute(tira_host_pb2.RunDetails(submissionFile=submission_file,
                                                           inputDatasetId=input_dataset_name,
                                                           inputRunPath=input_run_path,
                                                           outputDirName=output_dir_name,
                                                           sandboxed=sandboxed,
                                                           optionalParameters=optional_parameters
                                                           ))

        print("Client received: " + str(response))
        return response
