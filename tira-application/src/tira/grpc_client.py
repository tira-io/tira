#!/usr/bin/env python

"""
    GrpcClient used to make gRPC calls to the dockerized tira-host running a VM.

    1. On execution of the new command
        1.1 if the vm_id+command_name is not in the list
            - execute grpc call in the new thread
            - add vm_id+command_name:thread to the list
            - return status 202
        1.2 if the vm_id+command_name is already in the list (i.e. not finished)
            - return status 202
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
tasks = {}


def task_status_url(task_id):
    return '/command_status/'+task_id


def async_api(wrapped_function):
    @wraps(wrapped_function)
    def new_function(*args, **kwargs):
        def task_call():
            try:
                tasks[task_id]['return_value'] = wrapped_function(*args, **kwargs)
            except Exception as e:
                tasks[task_id]['return_value'] = HttpResponse(status=500)
            finally:
                # We record the time of the response, to help in garbage
                # collecting old tasks
                tasks[task_id]['completion_timestamp'] = datetime.timestamp(datetime.utcnow())

        # Assign an id to the asynchronous task
        task_id = uuid.uuid4().hex

        # Record the task, and then launch it
        tasks[task_id] = {'task_thread': threading.Thread(target=task_call, args=())}
        tasks[task_id]['task_thread'].start()

        # Return a 202 response, with a link that the client can use to obtain task status
        print(task_status_url(task_id))
        # return 'accepted', 202, {'Location': command_status_url('/command_status/'+task_id, task_id=task_id)}
        return (202, task_status_url(task_id))
    return new_function


class GrpcClient:
    def __init__(self, hostname):
        self.hostname = hostname
        self.channel = grpc.insecure_channel(hostname + ':' + str(grpc_port))
        self.stub = tira_host_pb2_grpc.TiraHostServiceStub(self.channel)

    def __del__(self):
        self.channel.close()

    @async_api
    def vm_start(self, vm_name):
        response = self.stub.vm_start(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + response.output)
        return response.output

        # t = threading.Thread(target=self.stub.vm_start, args=tira_host_pb2.RequestVmCommands(vmName=vm_name))
        # t.setDaemon(True)
        # t.start()
        #
        # return HttpResponse(status=202)

    @async_api
    def vm_stop(self, vm_name):
        response = self.stub.vm_stop(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + response.output)
        return response.output

    @async_api
    def vm_shutdown(self, vm_name):
        response = self.stub.vm_shutdown(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + response.output)
        return response.output

    @async_api
    def vm_info(self, vm_name):
        response_vm_info = self.stub.vm_info(tira_host_pb2.RequestVmCommands(vmName=vm_name))
        print("Client received: " + str(response_vm_info))
        return 202, response_vm_info

    @async_api
    def vm_list(self, vm_name):
        response = self.stub.vm_list(Empty)
        print("Client received: " + response.output)
        return response.output

    @async_api
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

    @async_api
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

    def get_command_status(self, task_id):
        # response = self.stub.get_command_status(command_id)
        # print("Client received: " + response.output)
        # return response.output
        """
            Return status of an asynchronous task. If this request returns a 202
            status code, it means that task hasn't finished yet. Else, the response
            from the task is returned.
        """
        task = tasks.get(task_id)
        if task is None:
            return 404
        if 'return_value' not in task:
            return 202, task_status_url(task_id)
        return 200, task['return_value']
