#!/usr/bin/env python
from django.conf import settings
import grpc
from grpc import aio
from google.protobuf.empty_pb2 import Empty
import socket

from .proto import tira_host_pb2, tira_host_pb2_grpc


grpc_port = settings.GRPC_PORT


class GrpcClient:
    def __init__(self, hostname):
        self.hostname = hostname
        self.channel = grpc.insecure_channel(hostname + ':' + str(grpc_port))
        self.stub = tira_host_pb2_grpc.TiraHostServiceStub(self.channel)

    def __del__(self):
        self.channel.close()

    def vm_start(self, vm_name):
        response = self.stub.vm_start(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + response.output)
        return response.output

    def vm_stop(self, vm_name):
        response = self.stub.vm_stop(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + response.output)
        return response.output

    def vm_shutdown(self, vm_name):
        response = self.stub.vm_shutdown(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + response.output)
        return response.output

    def vm_info(self, vm_name):
        response_vm_info = self.stub.vm_info(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + str(response_vm_info))
        return response_vm_info

    def vm_list(self, vm_name):
        response = self.stub.vm_list(Empty)
        print("Client received: " + response.output)
        return response.output

    def run_execute(self, vm_name):
        response = self.stub.run_execute(tira_host_pb2.RequestRunExecuteEval(submissionFile="",
                                                                             inputDatasetName="",
                                                                             inputRunPath="",
                                                                             outputDirName="",
                                                                             sandboxed="",
                                                                             optionalParameters=""
                                                                             ))
        print("Client received: " + response.output)
        return response.output

    def run_eval(self, vm_name):
        response = self.stub.run_eval(tira_host_pb2.RequestRunExecuteEval(submissionFile="",
                                                                          inputDatasetName="",
                                                                          inputRunPath="",
                                                                          outputDirName="",
                                                                          sandboxed="",
                                                                          optionalParameters=""
                                                                          ))
        print("Client received: " + response.output)
        return response.output

    def get_command_status(self, command_id):
        response = self.stub.get_command_status(command_id)
        print("Client received: " + response.output)
        return response.output
