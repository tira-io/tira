from google.protobuf.text_format import Parse
from google.protobuf.json_format import MessageToDict
from pathlib import Path
import logging
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
import socket
from datetime import datetime

from .proto import TiraClientWebMessages_pb2 as modelpb
from .proto import tira_host_pb2 as model_host

logger = logging.getLogger("tira")
# Transition is powering_on (3), powering_off (4), sandboxing (5), unsandboxing (6), executing (7)
transition_states = {3, 4, 5, 6, 7}
# Stable is undefined (0), running (1), powered_off (2), or archived (8)
stable_state = {0, 1, 2, 8}


def _validate_transition_state(value):
    if value not in transition_states:
        raise ValidationError('%(value)s is not a transition state', params={'value': value})


class TransactionLog(models.Model):
    transaction_id = models.CharField(max_length=280, primary_key=True)
    completed = models.BooleanField()
    last_update = models.DateTimeField(auto_now=True)
    last_status = models.CharField(max_length=50)
    last_message = models.CharField(max_length=500)


class TransitionLog(models.Model):
    vm_id = models.CharField(max_length=280, primary_key=True)
    # tracks the state of vms that are not in a stable state.
    vm_state = models.IntegerField(validators=[_validate_transition_state])
    transaction = models.ForeignKey(TransactionLog, on_delete=models.CASCADE, null=True)


class EvaluationLog(models.Model):
    vm_id = models.CharField(max_length=280)
    run_id = models.CharField(max_length=280)
    transaction = models.ForeignKey(TransactionLog, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = (("vm_id", "run_id"),)



