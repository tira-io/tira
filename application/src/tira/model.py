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


class GitIntegration(models.Model):
    namespace_url = models.CharField(max_length=280, primary_key=True)
    host = models.CharField(max_length=100, default='')
    private_token = models.CharField(max_length=100, default='')
    user_name = models.CharField(max_length=100, default='')
    user_password = models.CharField(max_length=100, default='')
    gitlab_repository_namespace_id = models.IntegerField(default=None, null=True)
    image_registry_prefix = models.CharField(max_length=150, default='')
    user_repository_branch = models.CharField(max_length=100, default='main')


class Organizer(models.Model):
    organizer_id = models.CharField(max_length=280, primary_key=True)
    name = models.CharField(max_length=100, default='tira')
    years = models.CharField(max_length=30, default='2022')
    web = models.CharField(max_length=300, default='https://www.tira.io')
    git_integrations = models.ManyToManyField(GitIntegration, default=None)


class VirtualMachine(models.Model):
    """ This is the equivalent of a 'user' object  (for legacy reasons).
    Typically, only the vm_id is set. The vm_id is the equivalent of the user name and ends
        in '-default' if there is no virtual machine assigned to this user.
    """
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
    featured = models.BooleanField(default=False)
    require_registration = models.BooleanField(default=False)
#    Set to true = users can not submit without a group
    require_groups = models.BooleanField(default=False)
#    True = users can not create their own groups, they must join the given set
    restrict_groups = models.BooleanField(default=False)
    max_std_out_chars_on_test_data = models.IntegerField(default=0)
    max_std_err_chars_on_test_data = models.IntegerField(default=0)
    max_file_list_chars_on_test_data = models.IntegerField(default=0)
    command_placeholder = models.TextField(default="mySoftware -c $inputDataset -r $inputRun -o $outputDir")
    command_description = models.TextField(default="Available variables: <code>$inputDataset</code>, <code>$inputRun</code>, <code>$outputDir</code>, <code>$dataServer</code>, and <code>$token</code>.")
    allowed_task_teams = models.TextField(default="")
    dataset_label = models.CharField(max_length=280, default="Input dataset")
    max_std_out_chars_on_test_data_eval = models.IntegerField(default=0)
    max_std_err_chars_on_test_data_eval = models.IntegerField(default=0)
    max_file_list_chars_on_test_data_eval = models.IntegerField(default=0)
    is_ir_task  = models.BooleanField(default=False)
    irds_re_ranking_image = models.CharField(max_length=150, default="")
    irds_re_ranking_command = models.CharField(max_length=150, default="")
    irds_re_ranking_resource = models.CharField(max_length=150, default="")


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
    git_runner_image = models.CharField(max_length=500, null=True, default=None)
    git_runner_command = models.CharField(max_length=500, null=True, default=None)
    git_repository_id = models.CharField(max_length=200, null=True, default=None)


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
    irds_docker_image = models.CharField(max_length=150, null=True, default=None)
    irds_import_command = models.CharField(max_length=150, null=True, default=None)
    irds_import_truth_command = models.CharField(max_length=150, null=True, default=None)
    meta_dataset_of = models.TextField(default=None, null=True)


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
    """
    - The dataset is only associated for compatibility with Software. It's probably always none.
    """
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True)
    last_edit_date = models.CharField(max_length=150)
    display_name = models.TextField(default="default upload")
    description = models.TextField(default="description missing")
    paper_link = models.TextField(default="")
    deleted = models.BooleanField(default=False)
    rename_to = models.TextField(default=None, null=True)


class DockerSoftware(models.Model):
    docker_software_id = models.AutoField(primary_key=True)
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    input_docker_software = models.ForeignKey("self", on_delete=models.RESTRICT, null=True, default=None)
    input_upload = models.ForeignKey(Upload, on_delete=models.RESTRICT, null=True)
    command = models.TextField(default="")
    display_name = models.TextField(default="")
    user_image_name = models.TextField(default="")
    tira_image_name = models.TextField(default="")
    tira_image_workdir = models.TextField(default=None, null=True)
    deleted = models.BooleanField(default=False)
    description = models.TextField(default="")
    paper_link = models.TextField(default="")
    ir_re_ranker = models.BooleanField(default=False)
    ir_re_ranking_input = models.BooleanField(default=False)
    public_image_name = models.TextField(default=None, null=True)
    public_image_size = models.BigIntegerField(default=None, null=True)


class DockerSoftwareHasAdditionalInput(models.Model):
    position = models.AutoField(primary_key=True)
    docker_software = models.ForeignKey(DockerSoftware, on_delete=models.CASCADE, related_name='+')
    input_docker_software = models.ForeignKey(DockerSoftware, on_delete=models.CASCADE, default=None, null=True, related_name='+')
    input_upload = models.ForeignKey(Upload, on_delete=models.RESTRICT, default=None, null=True)

class DiscourseTokenForUser(models.Model):
    vm_id = models.OneToOneField(VirtualMachine, on_delete=models.CASCADE, primary_key=True)
    token = models.CharField(max_length=250)

class SoftwareSubmissionGitRepository(models.Model):
    repository_url = models.CharField(max_length=500, primary_key=True)
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    reference_repository_url = models.CharField(max_length=500)
    external_owner = models.CharField(max_length=100)
    docker_registry_token = models.CharField(max_length=100)
    docker_registry_user = models.CharField(max_length=100, default=None)
    tira_client_token = models.CharField(max_length=100)
    tira_client_user = models.CharField(max_length=100, null=True, default=None)
    tira_client_description = models.CharField(max_length=100, null=True, default=None)
    confirmed = models.BooleanField(null=False, default=False)


class LinkToSoftwareSubmissionGitRepository(models.Model):
    docker_software = models.ForeignKey(DockerSoftware, on_delete=models.CASCADE)
    software_submission_git_repository = models.ForeignKey(SoftwareSubmissionGitRepository, on_delete=models.RESTRICT)
    commit_hash = models.CharField(max_length=100)
    link_to_file = models.CharField(max_length=500)
    build_environment = models.TextField(default=None, null=True)


class SoftwareClone(models.Model):
    """
    - This allows to import/export existing software to other tasks.
    """
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    docker_software = models.ForeignKey(DockerSoftware, on_delete=models.CASCADE, default=None, null=True)
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, default=None, null=True)


class HuggingFaceModelsOfSoftware(models.Model):
    """
    - The Huggingface models to mount into some software.
    """
    docker_software = models.ForeignKey(DockerSoftware, on_delete=models.CASCADE, default=None, null=True)
    hf_home = models.CharField(max_length=250, default="")
    mount_hf_model = models.TextField(default="")
    models_scan = models.TextField(default="")


class Run(models.Model):
    run_id = models.CharField(max_length=150, primary_key=True)
    software = models.ForeignKey(Software, on_delete=models.CASCADE, null=True)
    evaluator = models.ForeignKey(Evaluator, on_delete=models.SET_NULL, null=True)
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE, null=True)
    docker_software = models.ForeignKey(DockerSoftware, on_delete=models.CASCADE, null=True)
    input_dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True)
    input_run = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True)
    downloadable = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    access_token = models.CharField(max_length=150, default="")


class Registration(models.Model):
    team_name = models.CharField(primary_key=True, max_length=50, default=None)
    initial_owner = models.CharField(max_length=50, default=None)
    team_members = models.CharField(max_length=500, null=True, default=None)
    registered_on_task = models.ForeignKey(Task, on_delete=models.RESTRICT, null=True, default=None)
    name = models.CharField(max_length=150, null=True, default=None)
    email = models.CharField(max_length=150, null=True, default=None)
    affiliation = models.CharField(max_length=150, null=True, default=None)
    country = models.CharField(max_length=150, null=True, default=None)
    employment = models.CharField(max_length=150, null=True, default=None)  # student, researcher, etc.
    participates_for = models.CharField(max_length=150, null=True, default=None)  # course, thesis, research, etc.
    instructor_name = models.CharField(max_length=150, null=True, default=None)
    instructor_email = models.CharField(max_length=150, null=True, default=None)
    questions = models.CharField(max_length=500, null=True, default=None)
    created = models.DateField(auto_now_add=True)
    last_modified = models.DateField(auto_now=True)


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


class BackendProcess(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField(default="")
    cmd = models.TextField(default="")
    last_contact = models.TextField(default="")
    exit_code = models.IntegerField(default=None, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, default=None)
    vm = models.ForeignKey(VirtualMachine, on_delete=models.CASCADE, null=True, default=None)
    stdout = models.TextField(default="")
