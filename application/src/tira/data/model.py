# from google.protobuf.text_format import Parse
# from google.protobuf.json_format import MessageToDict
# from pathlib import Path
# import logging
# from django.conf import settings
# from django.db import models
# from django.core.exceptions import ValidationError
# import socket
# from datetime import datetime
#
# from tira.proto import TiraClientWebMessages_pb2 as modelpb
# from tira.proto import tira_host_pb2 as model_host
#
# logger = logging.getLogger("tira")
#
#
# class Organizers(models.Model):
#     organizer_id = models.CharField(max_length=280, primary_key=True)
#     name = models.CharField(max_length=100)
#     years = models.CharField(max_length=30)
#     web = models.CharField(max_length=300)
#
#
# class VirtualMachines(models.Model):
#     vm_id = models.CharField(max_length=280, primary_key=True)
#     user_name = models.CharField(max_length=280)
#     user_password = models.CharField(max_length=280)
#
#
# # class EvaluationLog(models.Model):
# #     vm_id = models.CharField(max_length=280)
# #     run_id = models.CharField(max_length=280)
# #     running_on = models.CharField(max_length=280)  # the vm_id of the master vm for the dataset that is evaluated on
# #     transaction = models.ForeignKey(TransactionLog, on_delete=models.SET_NULL, null=True)
# #     last_update = models.DateTimeField(auto_now=True)
# #
# #     class Meta:
# #         unique_together = (("vm_id", "run_id"),)
#
#
#
