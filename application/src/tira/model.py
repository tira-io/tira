from google.protobuf.text_format import Parse
from google.protobuf.json_format import MessageToDict
from pathlib import Path
import logging
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
import socket
from datetime import datetime

from tira.proto import TiraClientWebMessages_pb2 as modelpb
from tira.proto import tira_host_pb2 as model_host

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
    transaction = models.ForeignKey(TransactionLog, on_delete=models.SET_NULL, null=True)
    last_update = models.DateTimeField(auto_now=True)


class EvaluationLog(models.Model):
    vm_id = models.CharField(max_length=280)
    run_id = models.CharField(max_length=280)
    running_on = models.CharField(max_length=280)  # the vm_id of the master vm for the dataset that is evaluated on
    transaction = models.ForeignKey(TransactionLog, on_delete=models.CASCADE, null=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("vm_id", "run_id"),)


class Organizer(models.Model):
    organizer_id = models.CharField(max_length=280, primary_key=True)
    name = models.CharField(max_length=100, default='tira')
    years = models.CharField(max_length=30, default='2022')
    web = models.CharField(max_length=300, default='https://www.tira.io')


class VirtualMachine(models.Model):
    vm_id = models.CharField(max_length=280, primary_key=True)
    user_password = models.CharField(max_length=280, default='tira')
    roles = models.CharField(max_length=100, default='guest')
    host = models.CharField(max_length=100, default=None, null=True)
    admin_name = models.CharField(max_length=100, default=None, null=True)
    admin_pw = models.CharField(max_length=280, default=None, null=True)
    ip = models.CharField(max_length=30, default=None, null=True)
    ssh = models.IntegerField(default=None, null=True)
    rdp = models.IntegerField(default=None, null=True)
    archived = models.BooleanField(default=False)


class Task(models.Model):
    task_id = models.CharField(max_length=150, primary_key=True)
    task_name = models.CharField(max_length=150, default="")
    task_description = models.TextField(default="")
    vm = models.ForeignKey(VirtualMachine, on_delete=models.SET_NULL, null=True)
    organizer = models.ForeignKey(Organizer, on_delete=models.SET_NULL, null=True)
    web = models.CharField(max_length=150, default='')
    max_std_out_chars_on_test_data = models.IntegerField(default=0)
    max_std_err_chars_on_test_data = models.IntegerField(default=0)
    max_file_list_chars_on_test_data = models.IntegerField(default=0)
    command_placeholder = models.TextField(default="mySoftware -c $inputDataset -r $inputRun -o $outputDir")
    command_description = models.TextField(default="Available variables: <code>$inputDataset</code>, <code>$inputRun</code>, <code>$outputDir</code>, <code>$dataServer</code>, and <code>$token</code>.")
    dataset_label = models.CharField(max_length=280, default="Input dataset")
    max_std_out_chars_on_test_data_eval = models.IntegerField(default=0)
    max_std_err_chars_on_test_data_eval = models.IntegerField(default=0)
    max_file_list_chars_on_test_data_eval = models.IntegerField(default=0)


class AllowedServer(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    server_address = models.CharField(max_length=280)

    class Meta:
        unique_together = (("task", "server_address"),)


class Evaluator(models.Model):
    evaluator_id = models.CharField(max_length=150, primary_key=True)
    command = models.CharField(max_length=280, default="")
    working_directory = models.CharField(max_length=150, default="")
    measures = models.CharField(max_length=150, default="")
    is_deprecated = models.BooleanField(default=False)
    is_git_runner = models.BooleanField(default=False)
    git_runner_image = models.CharField(max_length=100, null=True, default=None)
    git_runner_command = models.CharField(max_length=280, null=True, default=None)
    git_repository_id = models.CharField(max_length=100, null=True, default=None)


class VirtualMachineHasEvaluator(models.Model):
    evaluator = models.ForeignKey(Evaluator, on_delete=models.CASCADE)
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)


class Dataset(models.Model):
    dataset_id = models.CharField(max_length=150, primary_key=True)
    default_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, default=None)
    display_name = models.CharField(max_length=150, default="")
    evaluator = models.ForeignKey(Evaluator, on_delete=models.CASCADE, null=True, default=None)
    is_confidential = models.BooleanField(default=True)
    is_deprecated = models.BooleanField(default=False)
    data_server = models.CharField(max_length=150, null=True, default=None)
    released = models.CharField(max_length=30, default="")
    default_upload_name = models.CharField(max_length=50, default="predictions.ndjson")
    created = models.DateField(auto_now_add=True)
    last_modified = models.DateField(auto_now=True)


class TaskHasDataset(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    is_test = models.BooleanField(default=True)

    class Meta:
        unique_together = (("task_id", "dataset_id"),)


class Software(models.Model):
    software_id = models.CharField(max_length=150)
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    count = models.CharField(max_length=150)
    command = models.TextField(default="")
    working_directory = models.TextField(default="")
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True)
    creation_date = models.CharField(max_length=150)
    last_edit_date = models.CharField(max_length=150)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = (("software_id", "vm", 'task'),)


class Upload(models.Model):
    """ Because I've fallen over this several times:
    - there is exactly one 'Upload' per vm. It's the equivalent to "software',
    the uploaded instance is a 'run' ...
    - The dataset is only associated for compatibility with Software. It's probably always none.
    """
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True)
    last_edit_date = models.CharField(max_length=150)

    class Meta:
        unique_together = (("vm", 'task'),)


class Run(models.Model):
    run_id = models.CharField(max_length=150, primary_key=True)
    software = models.ForeignKey(Software, on_delete=models.SET_NULL, null=True)
    evaluator = models.ForeignKey(Evaluator, on_delete=models.SET_NULL, null=True)
    upload = models.ForeignKey(Upload, on_delete=models.SET_NULL, null=True)
    input_dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True)
    input_run = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    downloadable = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    access_token = models.CharField(max_length=150, default="")


class SoftwareHasInputRun(models.Model):
    software = models.OneToOneField(Software, on_delete=models.CASCADE)
    input_run = models.ForeignKey(Run, on_delete=models.SET_NULL, null=True)


class Evaluation(models.Model):
    measure_key = models.CharField(max_length=150)
    measure_value = models.CharField(max_length=150)
    evaluator = models.ForeignKey(Evaluator, on_delete=models.SET_NULL, null=True)
    run = models.ForeignKey(Run, on_delete=models.CASCADE)


class Review(models.Model):
    run = models.OneToOneField(Run, on_delete=models.CASCADE)
    reviewer_id = models.CharField(max_length=150)
    review_date = models.CharField(max_length=150)
    no_errors = models.BooleanField(default=True)
    missing_output = models.BooleanField(default=False)
    extraneous_output = models.BooleanField(default=False)
    invalid_output = models.BooleanField(default=False)
    has_error_output = models.BooleanField(default=False)
    other_errors = models.BooleanField(default=False)
    comment = models.TextField(default="")
    has_errors = models.BooleanField(default=False)
    has_warnings = models.BooleanField(default=False)
    has_no_errors = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    blinded = models.BooleanField(default=True)
