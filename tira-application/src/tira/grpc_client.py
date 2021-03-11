#!/usr/bin/env python

"""
    GrpcClient to make gRPC calls to the dockerized tira-host running a VM.
"""

from django.conf import settings
import grpc
from grpc import aio
from google.protobuf.empty_pb2 import Empty
from django.http import HttpResponse, Http404, JsonResponse
import socket
from functools import wraps
import uuid
from datetime import datetime
import threading

from .proto import tira_host_pb2, tira_host_pb2_grpc

grpc_port = settings.GRPC_PORT


class GrpcClient:
    def __init__(self, hostname):
        self.hostname = hostname
        self.channel = grpc.insecure_channel(hostname + ':' + str(grpc_port))
        self.stub = tira_host_pb2_grpc.TiraHostServiceStub(self.channel)

    def __del__(self):
        self.channel.close()

    def vm_create(self, ova_file, user_name):
        response = self.stub.vm_create(tira_host_pb2.RequestVmCommands(ovaFile=ova_file, userName=user_name))
        return response.commandId

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

    def vm_list(self):
        response = self.stub.vm_list(Empty)
        print("Client received: " + response.output)
        return response.output

    def run_execute(self, submission_file, input_dataset_name, input_run_path, output_dir_name, sandboxed,
                    optional_parameters):
        response = self.stub.run_execute(tira_host_pb2.RequestRunExecuteEval(submissionFile=submission_file,
                                                                             inputDatasetName=input_dataset_name,
                                                                             inputRunPath=input_run_path,
                                                                             outputDirName=output_dir_name,
                                                                             sandboxed=sandboxed,
                                                                             optionalParameters=optional_parameters
                                                                             ))
        print("Client received: " + response.output)
        return response.output

    def run_eval(self, submission_file, input_dataset_name, input_run_path, output_dir_name, sandboxed,
                 optional_parameters):
        response = self.stub.run_execute(tira_host_pb2.RequestRunExecuteEval(submissionFile=submission_file,
                                                                             inputDatasetName=input_dataset_name,
                                                                             inputRunPath=input_run_path,
                                                                             outputDirName=output_dir_name,
                                                                             sandboxed=sandboxed,
                                                                             optionalParameters=optional_parameters
                                                                             ))

        print("Client received: " + response.output)
        return response.output
