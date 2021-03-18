#!/usr/bin/env python

import asyncio
# from grpc import aio
from google.protobuf.empty_pb2 import Empty
from grpc.experimental import aio

from proto import tira_host_pb2, tira_host_pb2_grpc


async def vm_start():
    # channel = grpc.insecure_channel('betaweb112.medien.uni-weimar.de:50051')
    # channel = grpc.insecure_channel('localhost:50051')
    # channel = grpc.aio.insecure_channel('betaweb111.medien.uni-weimar.de:50051')
    # stub = tira_host_pb2_grpc.TiraHostServiceStub(channel)
    # call_future = stub.SayHello.future(tira_host_pb2.HelloRequest(name='you'))
    # call_future.add_done_callback(process_response)

    # stub = tira_host_pb2.TiraHostServiceStub(channel)

    # response = stub.test(tira_host_pb2.Input(text='Hello test'))
    # response = stub.vm_create(tira_host_pb2.Request(ovaFile="tira-ubuntu-20-04-desktop-64bit.ova", userName="nik-test-ubuntu18"))
    # response = stub.vm_delete(tira_host_pb2.Request(vmName="nik-test-ubuntu18-01-tira-ubuntu-20-04-desktop-64bit"))

    # async with aio.insecure_channel('localhost:50051') as channel:
    # async with aio.insecure_channel('betaweb111.medien.uni-weimar.de:50051') as channel:
    # channel = aio.insecure_channel('betaweb111.medien.uni-weimar.de:50051')

    channel = aio.insecure_channel('localhost:50051')
    stub = tira_host_pb2_grpc.TiraHostServiceStub(channel)
    response = await stub.vm_start(tira_host_pb2.RequestVmCommands(vmName="nik1"))
    print("Client received: " + response.output)
    await channel.close()
    return response.output


async def vm_stop():
    channel = aio.insecure_channel('localhost:50051')
    stub = tira_host_pb2_grpc.TiraHostServiceStub(channel)
    response = await stub.vm_stop(tira_host_pb2.RequestVmCommands(vmName="nik1"))
    print("Client received: " + response.output)
    await channel.close()
    return response.output


async def vm_info():
    # channel = aio.insecure_channel('betaweb112.medien.uni-weimar.de:50051')
    channel = aio.insecure_channel('localhost:50051')
    stub = tira_host_pb2_grpc.TiraHostServiceStub(channel)
    # response = await stub.vm_info(tira_host_pb2.RequestVmCommands(vmName="nik-u18-2-08-tira-ubuntu-18-04-desktop-64bit"))
    response = await stub.vm_info(tira_host_pb2.RequestVmCommands(vmName="nik1"))
    print("Client received: " + str(response))
    await channel.close()
    return response


async def vm_list():
    channel = aio.insecure_channel('localhost:50051')
    stub = tira_host_pb2_grpc.TiraHostServiceStub(channel)
    response = await stub.vm_list(Empty)
    print("Client received: " + response.output)
    await channel.close()
    return response


async def vm_create():
    channel = aio.insecure_channel('localhost:50051')
    stub = tira_host_pb2_grpc.TiraHostServiceStub(channel)
    response = await stub.vm_create(
        tira_host_pb2.RequestVmCreate(ovaFile="tira-ubuntu-18-04-desktop-64bit.ova", userName="nik1"))
    print("Client received: " + response.output)
    await channel.close()
    return response


async def main():
    await asyncio.gather(vm_start())
    await asyncio.gather(vm_stop(), vm_info())
    # await asyncio.gather(vm_create(), get_command_status())
    # await asyncio.gather(vm_info())


if __name__ == '__main__':
    asyncio.run(main())
