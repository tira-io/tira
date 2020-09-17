#!/usr/bin/env python
import grpc

import TiraHostMessages_pb2
import TiraHostMessages_pb2_grpc

def run():
  channel = grpc.insecure_channel('betaweb112.medien.uni-weimar.de:50051')
  stub = TiraHostMessages_pb2_grpc.TiraHostServiceStub(channel)

  # response = stub.test(TiraHostMessages_pb2.Input(text='Hello test'))
  response = stub.vm_info(TiraHostMessages_pb2.Request(vmName="nik-docker-test-ubuntu1804desktop2-01-tira-ubuntu-18-04-desktop-64bit"))

  print("Client received: " + response.output)


if __name__ == '__main__':
    run()
