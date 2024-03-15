import grpc
from google.protobuf.empty_pb2 import Empty
import logging
import logging.config
import sys

sys.path.append('../../src/tira')
from proto import tira_host_pb2, tira_host_pb2_grpc

logger = logging.getLogger(__name__)


class TiraHostClient(tira_host_pb2_grpc.TiraApplicationService):
    def __init__(self, tira_application_host, tira_application_grpc_port):
        # Create stub for tira-application
        self.channel = grpc.insecure_channel(tira_application_host + ':' + tira_application_grpc_port)
        self.stub_tira_application = tira_host_pb2_grpc.TiraApplicationServiceStub(self.channel)

    def set_state(self, vm_id, vm_state, transaction_id):
        """ Wait for :param slp: seconds, then call the set_state method of the applications server,
         this means, we tell the application that the vm now changed it's state to vm_state """
        response = None
        try:
            response = self.stub_tira_application.set_state(
                tira_host_pb2.VmState(transaction=tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                                                            transactionId=transaction_id,
                                                                            message=f"Set state to {vm_state}"),
                                      state=vm_state, vmId=vm_id))
            logger.debug(f"tira-application.set_state({locals()}) response was: {response}")
        except Exception as e:
            logger.debug(f"tira-application.set_state({locals()}) request failed: {e}")

        return response

    def complete_transaction(self, transaction_id, status, message):
        """ Confirm that a Transaction has completed.
        """
        response = None
        try:
            response = self.stub_tira_application.complete_transaction(
                tira_host_pb2.Transaction(status=status, transactionId=transaction_id,
                                          message=message))
            logger.debug(f"tira-application.complete_transaction({locals()}) response was: {response}")
        except Exception as e:
            logger.debug(f"tira-application.complete_transaction({locals()}) failed: {e}")

        return response

    def confirm_vm_create(self, vm_id, user_name, user_pw, ip, host, ssh, rdp, transaction_id):
        """ Wait for :param slp: seconds, then call the set_state method of the applications server,
         this means, we tell the application that the vm now changed it's state to vm_state """
        response = None
        try:
            response = self.stub_tira_application.confirm_vm_create(
                tira_host_pb2.VmDetails(transaction=tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                                                              transactionId=transaction_id,
                                                                              message=f"Created VM"),
                                        vmId=vm_id, userName=user_name, initialUserPw=user_pw,
                                        ip=ip, host=host, sshPort=ssh, rdpPort=rdp))
            logger.debug(f"tira-application.confirm_vm_create() response was: {response}")
        except Exception as e:
            logger.debug(f"tira-application.confirm_vm_create() request failed: {e}")

        return response

    def confirm_run_execute(self, vm_id, dataset_id, run_id, transaction_id):
        """ Call the confirm_run_eval method of the applications server """
        result = tira_host_pb2.ExecutionResults(
            transaction=tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS, transactionId=transaction_id,
                                                  message="completed evaluation"),
            runId=tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id))

        response = self.stub_tira_application.confirm_run_eval(result)
        if response.status == tira_host_pb2.Status.SUCCESS:
            logger.debug(f"tira-application.confirm_run_execute({locals()}) response was: {response}")
            self.complete_transaction(transaction_id, status=tira_host_pb2.Status.SUCCESS,
                                      message='confirmation: completed evaluation')
        else:
            logger.debug(f"tira-application.confirm_run_execute() request failed: {e}")
            self.confirm_run_execute(vm_id, dataset_id, run_id, transaction_id)
        return response

    def confirm_run_eval(self, vm_id, dataset_id, run_id, transaction_id):
        """ Call the confirm_run_eval method of the applications server """
        measure = tira_host_pb2.EvaluationResults.Measure(key='demo-measure', value='1')
        result = tira_host_pb2.EvaluationResults(
            transaction=tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS, transactionId=transaction_id,
                                                  message="completed evaluation"),
            runId=tira_host_pb2.RunId(vmId=vm_id, datasetId=dataset_id, runId=run_id))
        result.measures.append(measure)

        response = self.stub_tira_application.confirm_run_eval(result)
        if response.status == tira_host_pb2.Status.SUCCESS:
            logger.debug(f"tira-application.confirm_run_eval({locals()}) response was: {response}")
            self.complete_transaction(transaction_id, status=tira_host_pb2.Status.SUCCESS,
                                      message='confirmation: completed evaluation')
        else:
            logger.debug(f"tira-application.confirm_run_eval() request failed: {e}")
            self.confirm_run_eval(vm_id, dataset_id, run_id, transaction_id)
        return response
