import grpc

from ..proto import tira_host_pb2, tira_host_pb2_grpc


class TestGrpcHostClient:
    def __init__(self, transaction_id):
        self.channel = grpc.insecure_channel("localhost:50052")
        self.stub = tira_host_pb2_grpc.TiraApplicationServiceStub(self.channel)
        self.transaction_id = transaction_id

    def __del__(self):
        self.channel.close()

    def set_state(self, vm_id, vm_state, transaction_id):
        """Wait for :param slp: seconds, then call the set_state method of the applications server,
        this means, we tell the application that the vm now changed it's state to vm_state"""
        if self.transaction_id == transaction_id:
            response = self.stub.set_state(
                tira_host_pb2.VmState(
                    transaction=tira_host_pb2.Transaction(
                        status=tira_host_pb2.Status.SUCCESS,
                        transactionId=transaction_id,
                        message=f"Set state to {vm_state}",
                    ),
                    state=vm_state,
                    vmId=vm_id,
                )
            )
            print(f"host-client: set_state response was: {response}")
            return response
        print("'set_state' rejected due to transaction id mismatch")

    # TODO transactionId -- implement create feature
    def confirm_vm_create(self, vm_id, user_name, user_pw, ip, host, ssh, rdp, transaction_id):
        """Call the set_state method of the applications server,
        this means, we tell the application that the vm now changed it's state to vm_state"""
        if self.transaction_id == transaction_id:
            response = self.stub.confirm_vm_create(
                tira_host_pb2.VmDetails(
                    transaction=tira_host_pb2.Transaction(
                        status=tira_host_pb2.Status.SUCCESS, transactionId=transaction_id, message="Created VM"
                    ),
                    vmId=vm_id,
                    userName=user_name,
                    initialUserPw=user_pw,
                    ip=ip,
                    host=host,
                    sshPort=ssh,
                    rdpPort=rdp,
                )
            )
            print(f"host-client: confirm_vm_create response was: {response}")
            return response
        print("'confirm_vm_create' rejected due to transaction id mismatch")

    # TODO transactionId -- implement delete feature
    def confirm_vm_delete(self, vm_id, user_name, user_pw, ip, ssh, rdp, transaction_id):
        """Call the set_state method of the applications server,
        this means, we tell the application that the vm now changed it's state to vm_state"""
        if self.transaction_id == transaction_id:
            response = self.stub.confirm_vm_delete(tira_host_pb2.VmId(vmId=vm_id))
            print(f"host-client: confirm_vm_delete response was: {response}")
            return response
        print("'confirm_vm_delete' rejected due to transaction id mismatch")

    def confirm_run_eval(self, vm_id, dataset_id, run_id, transaction_id):
        """Call the confirm_run_eval method of the applications server"""
        if self.transaction_id == transaction_id:
            measure = tira_host_pb2.EvaluationResults.Measure(key="demo-measure", value="1")
            result = tira_host_pb2.EvaluationResults(
                transaction=tira_host_pb2.Transaction(
                    status=tira_host_pb2.Status.SUCCESS, transactionId=transaction_id, message="completed evaluation"
                ),
                runId=tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id),
            )
            result.measures.append(measure)

            response = self.stub.confirm_run_eval(result)
            print(f"host-client: confirm_run_eval response was: {response}")
            if response.status == tira_host_pb2.Status.SUCCESS:
                self.complete_transaction(transaction_id, message="confirmation: completed evaluation")
            else:
                self.confirm_run_eval(vm_id, dataset_id, run_id, transaction_id)
            return response
        print("'confirm_run_eval' rejected due to transaction id mismatch")

    def complete_transaction(self, transaction_id, message):
        """Confirm that a Transaction has completed."""
        if self.transaction_id == transaction_id:
            response = self.stub.complete_transaction(
                tira_host_pb2.Transaction(
                    status=tira_host_pb2.Status.SUCCESS, transactionId=transaction_id, message=message
                )
            )
            print(f"host-client: complete_transaction response was: {response}")
            return response
        print("'complete_transaction' rejected due to transaction id mismatch")
