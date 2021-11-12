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
        response = self.stub_tira_application.set_state(
            tira_host_pb2.VmState(transaction=tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                                                        transactionId=transaction_id,
                                                                        message=f"Set state to {vm_state}"),
                                  state=vm_state, vmId=vm_id))
        logger.debug(f"tira-application.set_state() response was: {response}")
        return response

    def complete_transaction(self, transaction_id, status, message):
        """ Confirm that a Transaction has completed.
        """
        response = self.stub_tira_application.complete_transaction(
            tira_host_pb2.Transaction(status=status, transactionId=transaction_id,
                                      message=message))
        logger.debug(f"tira-application.complete_transaction() response was: {response}")
        return response

    # TODO transactionId
    def confirm_vm_create(self, vm_id, user_name, user_pw, ip, host, ssh, rdp, transaction_id):
        """ Wait for :param slp: seconds, then call the set_state method of the applications server,
         this means, we tell the application that the vm now changed it's state to vm_state """
        response = self.stub_tira_application.confirm_vm_create(
            tira_host_pb2.VmDetails(transaction=tira_host_pb2.Transaction(status=tira_host_pb2.Status.SUCCESS,
                                                                          transactionId=transaction_id,
                                                                          message=f"Created VM"),
                                    vmId=vm_id, userName=user_name, initialUserPw=user_pw,
                                    ip=ip, host=host, sshPort=ssh, rdpPort=rdp))
        logger.debug(f"tira-application.confirm_vm_create() response was: {response}")
        return response
