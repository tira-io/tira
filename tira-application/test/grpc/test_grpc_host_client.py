import grpc
from google.protobuf.empty_pb2 import Empty
from time import sleep
import sys

sys.path.append('../../src/tira')
from proto import tira_host_pb2, tira_host_pb2_grpc


class TestGrpcHostClient:
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50052')
        self.stub = tira_host_pb2_grpc.TiraApplicationServiceStub(self.channel)

    def __del__(self):
        self.channel.close()

    def set_state(self, vm_id, vm_state, transaction_id, slp=7):
        """ Wait for :param slp: seconds, then call the set_state method of the applications server,
         this means, we tell the application that the vm now changed it's state to vm_state """
        sleep(slp)
        response = self.stub.set_state(
            tira_host_pb2.VmState(status=tira_host_pb2.Status.SUCCESS, state=vm_state, vmId=vm_id))
        print(f"host-client: set_state response was: {response}")
        return response

    # TODO transactionId
    def confirm_vm_create(self, vm_id, user_name, user_pw, ip, ssh, rdp, slp=7):
        """ Wait for :param slp: seconds, then call the set_state method of the applications server,
         this means, we tell the application that the vm now changed it's state to vm_state """
        sleep(slp)

        response = self.stub.confirm_vm_create(
            tira_host_pb2.VmDetails(vmId=vm_id, userId=vm_id, userName=user_name, initialUserPw=user_pw,
                                    ip=ip, sshPort=ssh, rdpPort=rdp))
        print(f"host-client: confirm_vm_create response was: {response}")
        return response

    # TODO transactionId
    def confirm_vm_delete(self, vm_id, user_name, user_pw, ip, ssh, rdp, slp=7):
        """ Wait for :param slp: seconds, then call the set_state method of the applications server,
         this means, we tell the application that the vm now changed it's state to vm_state """
        sleep(slp)
        response = self.stub.confirm_vm_delete(
            tira_host_pb2.VmId(vmId=vm_id))
        print(f"host-client: confirm_vm_delete response was: {response}")
        return response

    def confirm_run_eval(self, vm_id, dataset_id, run_id, transaction_id, slp=7):
        """ Wait for :param slp: seconds, then call the confirm_run_eval method of the applications server """
        sleep(slp)
        measure = tira_host_pb2.EvaluationResults.Measure(key='demo-measure', value='1')
        result = tira_host_pb2.EvaluationResults(
            transaction=tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS, transactionId=transaction_id,
                                                  message="completed evaluation"),
            runId=tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id))
        result.measures.append(measure)

        response = self.stub.confirm_run_eval(result)
        print(f"host-client: confirm_run_eval response was: {response}")
        if response.status == tira_host_pb2.Status.SUCCESS:
            self.complete_transaction(transaction_id, message='confirmation: completed evaluation')
        else:
            self.confirm_run_eval(self, vm_id, dataset_id, run_id, transaction_id)
        return response

    def complete_transaction(self, transaction_id, message, slp=7):
        """ Confirm that a Transaction has completed.
        """
        response = self.stub.complete_transaction(
            tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS, transactionId=transaction_id,
                                      message=message))
        print(f"host-client: complete_transaction response was: {response}")
        return response

    def do_run_execute(self, vm_id, dataset_id, run_id, transaction_id):
        """ Here we pretend to do all actions involved in running and executing the software:
         - shutdown, sandbox, execute, unsandbox, power_on
         But we sleep instead. Afterwards, we notify the application that the transaction was complete.
         """
        self.set_state(vm_id, 4, transaction_id)  # set state to powering_off
        sleep(7)
        self.set_state(vm_id, 5, transaction_id)  # set state to sandboxing
        sleep(7)
        self.set_state(vm_id, 7, transaction_id)  # set state to executing
        sleep(7)
        self.set_state(vm_id, 6, transaction_id)  # set state to unsandboxing
        sleep(7)
        self.set_state(vm_id, 3, transaction_id)  # set state to powering_on
        sleep(7)
        self.set_state(vm_id, 1, transaction_id)  # set state to running
        sleep(7)
        self.complete_transaction(transaction_id, message="run execute completed successful")
