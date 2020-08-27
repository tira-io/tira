#!/usr/bin/env python
import grpc

import TiraHostMessages_pb2
import TiraHostMessages_pb2_grpc


def run():
  channel = grpc.insecure_channel('localhost:50051')
  stub = TiraHostMessages_pb2_grpc.TiraHostServiceStub(channel)
  response = stub.test(TiraHostMessages_pb2.Input(text='Hello test'))
  response = stub.vm_info(TiraHostMessages_pb2.Request(TiraHostMessages_pb2.VirtualMachine()))
  print("Client received: " + response.text)


if __name__ == '__main__':
    run()
