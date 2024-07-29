#!/usr/bin/env python

from concurrent import futures
from functools import wraps
from threading import Thread
from time import sleep
from uuid import uuid4

import grpc

from tira.grpc.test_grpc_host_client import TestGrpcHostClient
from tira.proto import tira_host_pb2, tira_host_pb2_grpc

VIRTUAL_MACHINES = {}


class DummyVirtualMachine(object):
    def __init__(self, vm_id, user_name, os, mem, cpu, ssh, rdp, host):
        self.state = 0
        self.vm_id = vm_id
        self.user_name = user_name
        self.guest_os = os
        self.memory_size = mem
        self.number_of_cpus = cpu
        self.ssh_port = ssh
        self.ssh_port_status = False
        self.rdp_port = rdp
        self.rdp_port_status = False
        self.host = host
        self.transaction_id = None

    def _sleep_ok(self, time, transaction_id):
        sleep(time)
        if self.transaction_id == transaction_id:
            return True
        print(f"{self.vm_id}: Active transaction changed during sleep from {transaction_id} to {self.transaction_id}")
        return False

    def get_info(self):
        response = tira_host_pb2.VmInfo()
        response.guestOs = self.guest_os
        response.memorySize = self.memory_size
        response.numberOfCpus = self.number_of_cpus
        response.sshPort = self.ssh_port
        response.rdpPort = self.rdp_port
        response.host = self.host
        response.sshPortStatus = self.ssh_port_status
        response.rdpPortStatus = self.rdp_port_status
        response.state = tira_host_pb2.State.UNDEFINED
        if self.state == 1:
            response.state = tira_host_pb2.State.RUNNING
        elif self.state == 2:
            response.state = tira_host_pb2.State.POWERED_OFF
        elif self.state == 3:
            response.state = tira_host_pb2.State.POWERING_ON
        elif self.state == 4:
            response.state = tira_host_pb2.State.POWERING_OFF
        elif self.state == 7:
            response.state = tira_host_pb2.State.EXECUTING
        elif self.state == 5:
            response.state = tira_host_pb2.State.SANDBOXING
        elif self.state == 6:
            response.state = tira_host_pb2.State.UNSANDBOXING
        elif self.state == 8:
            response.state = tira_host_pb2.State.ARCHIVED

        return response

    def auto_transaction(msg):
        """automatically terminate transactions if a method completes"""

        def attribute_decorator(func):
            @wraps(func)
            def func_wrapper(self, transaction_id, *args, complete_transaction=False):
                # safely reset the transaction_ids
                if self.transaction_id is not None or self.transaction_id == transaction_id:
                    TestGrpcHostClient(self.transaction_id).complete_transaction(
                        self.transaction_id, f"transaction superseded by {transaction_id}"
                    )
                    self.transaction_id = None
                self.transaction_id = transaction_id

                func(self, transaction_id, *args)  # Do the actual function

                if complete_transaction:
                    if self.transaction_id == transaction_id:
                        TestGrpcHostClient(transaction_id).complete_transaction(transaction_id, msg)
                        self.transaction_id = None
                    else:
                        TestGrpcHostClient(transaction_id).complete_transaction(
                            transaction_id, f"transaction superseded by {self.transaction_id}"
                        )

            return func_wrapper

        return attribute_decorator

    def create(self, transaction_id):
        test_host_client = TestGrpcHostClient(transaction_id)
        self.state = 2
        test_host_client.confirm_vm_create(
            self.vm_id,
            self.user_name,
            "dummy_pw",
            "127.0.0.1",
            self.host,
            self.ssh_port,
            self.rdp_port,
            self.transaction_id,
        )
        self.start(transaction_id)
        self.transaction_id = None
        # TODO check if we need to complete transaction here

    def delete_self(self, transaction_id):
        test_host_client = TestGrpcHostClient(transaction_id)
        sleep(7)
        test_host_client.complete_transaction(self.transaction_id, "vm deleted")

    @auto_transaction("Transaction completed by vm-start.")
    def start(self, transaction_id):
        test_host_client = TestGrpcHostClient(transaction_id)

        self.state = 3
        test_host_client.set_state(self.vm_id, 3, self.transaction_id)

        if not self._sleep_ok(7, transaction_id):
            return

        self.state = 1
        test_host_client.set_state(self.vm_id, 1, self.transaction_id)

        sleep(5)
        self.ssh_port_status = True
        self.rdp_port_status = True

    @auto_transaction("Transaction completed by vm-stop.")
    def stop(self, transaction_id):
        test_host_client = TestGrpcHostClient(transaction_id)

        self.state = 4
        self.ssh_port_status = False
        self.rdp_port_status = False
        test_host_client.set_state(self.vm_id, 4, self.transaction_id)

        if not self._sleep_ok(7, transaction_id):
            return

        self.state = 2
        test_host_client.set_state(self.vm_id, 2, self.transaction_id)

    @auto_transaction("Transaction completed by vm-shutdown.")
    def shutdown(self, transaction_id):
        self.stop(transaction_id, complete_transaction=False)

    @auto_transaction("Transaction completed by vm-sandbox.")
    def sandbox(self, transaction_id):
        test_host_client = TestGrpcHostClient(transaction_id)

        self.state = 5
        test_host_client.set_state(self.vm_id, 5, self.transaction_id)

        if not self._sleep_ok(7, transaction_id):
            return

        self.state = 7
        test_host_client.set_state(self.vm_id, 7, self.transaction_id)

    @auto_transaction("Transaction completed by vm-unsandbox.")
    def unsandbox(self, transaction_id):
        test_host_client = TestGrpcHostClient(transaction_id)

        self.state = 6
        test_host_client.set_state(self.vm_id, 6, self.transaction_id)

        # wait for unsandboxing to complete
        if not self._sleep_ok(7, transaction_id):
            return

        self.state = 2
        test_host_client.set_state(self.vm_id, 2, self.transaction_id)

    @auto_transaction("Transaction completed by run-execute.")
    def run_execute(self, transaction_id):
        if self.state == 1:
            self.shutdown(transaction_id, complete_transaction=False)

        self.sandbox(transaction_id, complete_transaction=False)

        # sleep and wait for execution
        if not self._sleep_ok(7, transaction_id):
            return

        self.sandbox(transaction_id, complete_transaction=False)
        self.start(transaction_id, complete_transaction=False)

    @auto_transaction("Transaction completed by run-eval.")
    def run_eval(self, transaction_id, input_vm_id, input_dataset_id, input_run_id):
        test_host_client = TestGrpcHostClient(transaction_id)

        # sleep and wait for evaluation
        if not self._sleep_ok(7, transaction_id):
            return

        test_host_client.confirm_run_eval(input_vm_id, input_dataset_id, input_run_id, self.transaction_id)

    @auto_transaction("Transaction completed by run-abort.")
    def run_abort(self, transaction_id):
        self.transaction_id = transaction_id
        if self.state == 4:
            # wait for the shutdown to finish, then start again
            sleep(7)
            self.start(transaction_id)
        elif self.state == 5:
            # wait for sandboxing to finish, then unsandbox
            sleep(7)
            self.unsandbox(transaction_id)
            self.start(transaction_id)
        elif self.state == 6:
            # wait for unsandboxing to finish, then start
            sleep(7)
            self.start(transaction_id)
        elif self.state == 7:
            # cancel execution, clean up files, unsandbox, and start
            self.unsandbox(transaction_id)
            self.start(transaction_id)


def get_or_create_vm(vm_id):
    """this is a hack for the dummy server. In reality, the vm need to be created first ;)"""
    vm = VIRTUAL_MACHINES.get(vm_id, None)

    if vm is None:  # here we cheat
        vm = DummyVirtualMachine(vm_id, "tira", "ubuntu", "16000", "2", "1234", "5678", "localhost")
        vm.state = 2
        VIRTUAL_MACHINES[vm_id] = vm

    return vm


class TiraHostService(tira_host_pb2_grpc.TiraHostService):

    def check_state(state, ignore_ongoing=False):
        """A decorator that checks the STATE precondition for all calls to TiraHostService that thae a VmId message
        We check:
          - is the vm in the correct state for the requested transistion
          - is there already a transaction ongoing
        The decorator then calls the callback (or not) and sends the appropriate reply
        """

        def state_check_decorator(func):
            @wraps(func)
            def func_wrapper(self, request, *args, **kwargs):
                try:
                    vm_id = request.vmId
                except AttributeError:
                    vm_id = request.runId.vmId

                vm = get_or_create_vm(vm_id)

                if vm.state not in state:
                    return tira_host_pb2.Transaction(
                        status=tira_host_pb2.Status.FAILED,
                        transactionId=request.transaction.transactionId,
                        message=f"{request.vmId}: required state {state} but was in state {vm.state}",
                    )

                if (
                    vm.transaction_id is not None
                    and vm.transaction_id != request.transaction.transactionId
                    and not ignore_ongoing
                ):
                    return tira_host_pb2.Transaction(
                        status=tira_host_pb2.Status.FAILED,
                        transactionId=request.transaction.transactionId,
                        message=f"Rejected. {vm_id} already accepted a different transaction",
                    )
                else:
                    func(self, request, *args, **kwargs)
                    return tira_host_pb2.Transaction(
                        status=tira_host_pb2.Status.SUCCESS,
                        transactionId=request.transaction.transactionId,
                        message=f"Accepted transaction.",
                    )

            return func_wrapper

        return state_check_decorator

    def vm_info(self, request, context):
        print(f"received vm-info for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        return vm.get_info()

    def vm_create(self, request, context):
        # TODO transactions
        print(
            f"received vm-create for {request.ovaFile} - {request.vmId} - {request.userName} "
            f"- {request.ip} - {request.host}"
        )

        if request.vmId in VIRTUAL_MACHINES.keys():
            return tira_host_pb2.Transaction(
                status=tira_host_pb2.Status.FAILED,
                transactionId=request.transaction.transactionId,
                message="ID already exists",
            )

        new_vm = DummyVirtualMachine(
            request.vmId, request.userName, "ubuntu", "16000", "2", "1234", "5678", request.host
        )

        VIRTUAL_MACHINES[request.vmId] = new_vm

        t = Thread(target=new_vm.create, args=(request.transaction.transactionId))
        t.start()

        return tira_host_pb2.Transaction(
            status=tira_host_pb2.Status.SUCCESS,
            transactionId=request.transaction.transactionId,
            message="received vm_create request",
        )

    @check_state({2})
    def vm_delete(self, request, context):
        print(f"received vm-delete for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        t = Thread(target=vm.delete_self, args=(request.transaction.transactionId))
        t.start()

        VIRTUAL_MACHINES.pop(request.vmId)

    @check_state({1})
    def vm_shutdown(self, request, context):
        print(f"received vm-shutdown for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        t = Thread(target=vm.shutdown, args=(request.transaction.transactionId,), kwargs={"complete_transaction": True})
        t.start()

    @check_state({2})
    def vm_start(self, request, context):
        print(f"received vm-start for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        t = Thread(target=vm.start, args=(request.transaction.transactionId,), kwargs={"complete_transaction": True})
        t.start()

    @check_state({3, 4}, ignore_ongoing=True)
    def vm_stop(self, request, context):
        print(f"received vm-stop for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        t = Thread(target=vm.stop, args=(request.transaction.transactionId,), kwargs={"complete_transaction": True})
        t.start()

    @check_state({2})
    def vm_sandbox(self, request, context):
        print(f"received vm-sandbox for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        t = Thread(target=vm.sandbox, args=(request.transaction.transactionId,), kwargs={"complete_transaction": True})
        t.start()

    @check_state({7})
    def vm_unsandbox(self, request, context):
        print(f"received vm-unsandbox for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        t = Thread(
            target=vm.unsandbox, args=(request.transaction.transactionId,), kwargs={"complete_transaction": True}
        )
        t.start()

    @check_state({1, 2})
    def run_execute(self, request, context):
        """Here we pretend to do all actions involved in running and executing the software:
        - shutdown, sandbox, execute, unsandbox, power_on
        But we sleep instead. Afterwards, we notify the application that the transaction was complete.
        """
        print(
            f"received run-execute for {request.runId.runId} - {request.runId.datasetId} - {request.runId.vmId} - "
            f"{request.inputRunId.runId} - {request.inputRunId.datasetId} - {request.inputRunId.vmId}"
        )
        vm = get_or_create_vm(request.runId.vmId)

        t = Thread(
            target=vm.run_execute, args=(request.transaction.transactionId,), kwargs={"complete_transaction": True}
        )
        t.start()

    # @check_state({1})  # Uncommented for the dummy code. Here we cheat and pretend the master is running already
    def run_eval(self, request, context):
        print(
            f"received run-eval for {request.runId.runId} - {request.runId.datasetId} - {request.runId.vmId} - "
            f"{request.inputRunId.runId} - {request.inputRunId.datasetId} - {request.inputRunId.vmId}"
        )

        vm = get_or_create_vm(request.runId.vmId)  # eval is executed on the master vm
        vm.state = 1

        try:
            t = Thread(
                target=vm.run_eval,
                args=(
                    request.transaction.transactionId,
                    request.inputRunId.vmId,
                    request.inputRunId.datasetId,
                    request.inputRunId.runId,
                ),
                kwargs={"complete_transaction": True},
            )
            t.start()
            return tira_host_pb2.Transaction(
                status=tira_host_pb2.Status.SUCCESS,
                transactionId=request.transaction.transactionId,
                message=f"TiraHostService:run_eval:{request.inputRunId.runId} on {request.runId.vmId}:ACCEPTED",
            )
        except Exception as e:
            return tira_host_pb2.Transaction(
                status=tira_host_pb2.Status.FAILED,
                transactionId=request.transaction.transactionId,
                message=f"TiraHostService:run_eval:{request.vmId}:FAILED:{e}",
            )

    @check_state({4, 5, 6, 7}, ignore_ongoing=True)
    def run_abort(self, request, context):
        print(f"received run-abort for {request.vmId}")
        vm = get_or_create_vm(request.vmId)

        t = Thread(
            target=vm.run_abort, args=(request.transaction.transactionId,), kwargs={"complete_transaction": True}
        )
        t.start()

    # TODO implement
    def vm_list(self, context):
        print(f"received vm-list")
        return tira_host_pb2.VmList(
            transaction=tira_host_pb2.Transaction(
                status=tira_host_pb2.Status.FAILED, message="vm-list: not implemented", transactionId=str(uuid4())
            )
        )

    def vm_backup(self, request, context):
        print(f"received vm-backup for {request.vmId}")
        return tira_host_pb2.VmList(
            transaction=tira_host_pb2.Transaction(
                status=tira_host_pb2.Status.FAILED,
                message="vm-backup: not implemented",
                transactionId=request.transaction.transactionId,
            )
        )

    def vm_snapshot(self, request, context):
        print(f"received vm-snapshot for {request.vmId}")
        return tira_host_pb2.VmList(
            transaction=tira_host_pb2.Transaction(
                status=tira_host_pb2.Status.FAILED,
                message="vm-snapshot: not implemented",
                transactionId=request.transaction.transactionId,
            )
        )


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    listen_addr = f"[::]:{port}"
    server.add_insecure_port(listen_addr)
    server.start()
    print("Starting host server on %s", listen_addr)
    server.wait_for_termination()


if __name__ == "__main__":
    serve("50051")
