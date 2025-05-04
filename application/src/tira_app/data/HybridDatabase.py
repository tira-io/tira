import gzip
import json
import logging
import os
import zipfile
from datetime import datetime as dt
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, overload

import randomname
from django.conf import settings
from django.db import IntegrityError
from google.protobuf.text_format import Parse
from tira.check_format import SUPPORTED_FORMATS

from .. import model as modeldb
from ..proto import TiraClientWebMessages_pb2 as modelpb
from ..util import (
    TiraModelIntegrityError,
    TiraModelWriteError,
    auto_reviewer,
    get_tira_id,
    get_today_timestamp,
    link_to_discourse_team,
    now,
)
from . import data as dbops

if TYPE_CHECKING:
    from typing import _T, Any, Iterable, Literal, Mapping, Optional, Sequence, Union

    from django.core.files.uploadedfile import UploadedFile
    from django.db.models import BaseManager
    from google.protobuf.message import Message

logger = logging.getLogger("tira_db")


class HybridDatabase(object):
    """
    This is the class to interface a the Tira Model from a Database.
    All objects are loaded from the FileDB and cached in a Database. Changes are maintained in both sources.
    When this class is constructed, it updates all entries.
    All public methods return dicts.

    _parse methods are for loading and cashing (i.e. store in memory)
    _load methods are for loading and returning (non persistent)
    _get methods are for conversion from proto to dict
    _save is to store objects in the file structure
    add is the public IF to add to the model
    get is the public IF to get data from the model
    """

    tira_root: Path = settings.TIRA_ROOT
    tasks_dir_path = tira_root / "model" / "tasks"
    users_file_path = tira_root / "model" / "users" / "users.prototext"
    organizers_file_path = tira_root / "model" / "organizers" / "organizers.prototext"
    vm_list_file = tira_root / "model" / "virtual-machines" / "virtual-machines.txt"
    vm_dir_path = tira_root / "model" / "virtual-machines"
    host_list_file = tira_root / "model" / "virtual-machine-hosts" / "virtual-machine-hosts.txt"
    ova_dir = tira_root / "data" / "virtual-machine-templates"
    datasets_dir_path = tira_root / "model" / "datasets"
    softwares_dir_path = tira_root / "model" / "softwares"
    data_path = tira_root / "data" / "datasets"
    runs_dir_path = tira_root / "data" / "runs"
    custom_irds_datasets_path = tira_root / "state" / "custom-ir-datasets"

    def __init__(self) -> None:
        pass

    def create_model(self, admin_user_name: str = "admin", admin_password: str = "admin") -> None:
        self.users_file_path.parent.mkdir(exist_ok=True, parents=True)
        self.tasks_dir_path.mkdir(exist_ok=True, parents=True)
        self.organizers_file_path.parent.mkdir(exist_ok=True, parents=True)
        self.vm_dir_path.mkdir(exist_ok=True, parents=True)
        self.host_list_file.parent.mkdir(exist_ok=True, parents=True)
        self.ova_dir.mkdir(exist_ok=True, parents=True)
        self.datasets_dir_path.mkdir(exist_ok=True, parents=True)
        self.softwares_dir_path.mkdir(exist_ok=True, parents=True)
        self.data_path.mkdir(exist_ok=True, parents=True)
        self.runs_dir_path.mkdir(exist_ok=True, parents=True)
        (self.tira_root / "state/virtual-machines").mkdir(exist_ok=True, parents=True)
        (self.tira_root / "state/softwares").mkdir(exist_ok=True, parents=True)

        self.users_file_path.touch(exist_ok=True)
        self.vm_list_file.touch(exist_ok=True)
        self.host_list_file.touch(exist_ok=True)
        self.organizers_file_path.touch(exist_ok=True)

        modeldb.VirtualMachine.objects.create(vm_id=admin_user_name, user_password=admin_password, roles="reviewer")
        self._save_vm(vm_id=admin_user_name, user_name=admin_user_name, initial_user_password=admin_password)

    def index_model_from_files(self) -> None:
        self.vm_list_file.touch(exist_ok=True)
        dbops.index(
            self.organizers_file_path,
            self.users_file_path,
            self.vm_dir_path,
            self.tasks_dir_path,
            self.datasets_dir_path,
            self.softwares_dir_path,
            self.runs_dir_path,
        )

    def reload_vms(self) -> None:
        """reload VM and user data from the export format of the model"""
        dbops.reload_vms(self.users_file_path, self.vm_dir_path)

    def reload_datasets(self) -> None:
        """reload dataset data from the export format of the model"""
        dbops.reload_datasets(self.datasets_dir_path)

    def reload_tasks(self) -> None:
        """reload task data from the export format of the model"""
        dbops.reload_tasks(self.tasks_dir_path)

    # _load methods parse files on the fly when pages are called
    def load_review(self, dataset_id: str, vm_id: str, run_id: str) -> "Message":
        """This method loads a review or toggles auto reviewer if it does not exist."""

        review_path = self.runs_dir_path / dataset_id / vm_id / run_id
        review_file = review_path / "run-review.bin"
        if not review_file.exists():
            review = auto_reviewer(review_path, run_id)
            self._save_review(dataset_id, vm_id, run_id, review)
            return review

        review = modelpb.RunReview()
        review.ParseFromString(review_file.read_bytes())
        return review

    def _load_softwares(self, task_id: str, vm_id: str) -> "Message":
        # Leave this
        softwares_dir = self.softwares_dir_path / task_id / vm_id
        softwares_dir.mkdir(parents=True, exist_ok=True)
        software_file = softwares_dir / "softwares.prototext"
        if not software_file.exists():
            software_file.touch()

        return Parse(software_file.read_bytes(), modelpb.Softwares())

    def _load_run(self, dataset_id: str, vm_id: str, run_id: str, return_deleted: bool = False) -> "Message":
        """Load a protobuf run file with some edge-case checks."""
        run_dir = self.runs_dir_path / dataset_id / vm_id / run_id
        if not (run_dir / "run.bin").exists():
            if (run_dir / "run.prototext").exists():
                r = Parse((run_dir / "run.prototext").read_bytes(), modelpb.Run())
                (run_dir / "run.bin").write_bytes(r.SerializeToString())
            else:
                logger.error(f"Try to read a run without a run.bin: {dataset_id}-{vm_id}-{run_id}")
                run = modelpb.Run()
                run.softwareId = "This run is corrupted. Please contact the support."
                run.runId = run_id
                run.inputDataset = dataset_id
                return run

        run = modelpb.Run()
        run.ParseFromString((run_dir / "run.bin").read_bytes())
        if return_deleted is False and run.deleted:
            run.softwareId = "This run was deleted"
            run.runId = run_id
            run.inputDataset = dataset_id

        return run

    # ---------------------------------------------------------------------
    # ---- save methods to update protos
    # ---------------------------------------------------------------------

    def _save_vm(
        self,
        vm_id: "Optional[str]" = None,
        user_name: "Optional[str]" = None,
        initial_user_password: "Optional[str]" = None,
        ip: "Optional[str]" = None,
        host: "Optional[str]" = None,
        ssh: "Optional[str]" = None,
        rdp: "Optional[str]" = None,
        overwrite: bool = False,
    ) -> bool:
        new_vm_file_path = self.vm_dir_path / f"{vm_id}.prototext"

        if not overwrite and new_vm_file_path.exists():
            raise TiraModelWriteError("Failed to write vm, vm exists and overwrite is not allowed here")
        elif overwrite and new_vm_file_path.exists():
            vm = Parse(open(new_vm_file_path).read(), modelpb.VirtualMachine())
        else:
            vm = modelpb.VirtualMachine()
        vm.virtualMachineId = vm_id if vm_id else vm.virtualMachineId
        vm.vmId = vm_id if vm_id else vm.vmId
        vm.vmName = vm_id if vm_id else vm.vmName
        vm.host = host if host else vm.host
        vm.adminName = vm.adminName if vm.adminName else "admin"  # Note these are required but deprecated
        vm.adminPw = vm.adminPw if vm.adminPw else "admin"  # Note these are required but deprecated
        vm.userName = user_name if user_name else vm.userName
        vm.userPw = initial_user_password if initial_user_password else vm.userPw
        vm.ip = ip if ip else vm.ip
        vm.portSsh = rdp if rdp else vm.portSsh
        vm.portRdp = ssh if ssh else vm.portRdp

        new_vm_file_path.write_text(str(vm))

        return True

    def _save_review(self, dataset_id: str, vm_id: str, run_id: str, review: "Message") -> None:
        """Save the reivew to the protobuf dump. Create the file if it does not exist."""
        review_path = self.runs_dir_path / dataset_id / vm_id / run_id
        (review_path / "run-review.prototext").write_text(str(review))
        (review_path / "run-review.bin").write_bytes(review.SerializeToString())

    def _save_softwares(self, task_id: str, vm_id: str, softwares: "Message") -> None:
        open(self.softwares_dir_path / task_id / vm_id / "softwares.prototext", "w+").write(str(softwares))

    def _save_run(self, dataset_id: str, vm_id: str, run_id: str, run: "Message") -> None:
        run_dir = self.runs_dir_path / dataset_id / vm_id / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        (run_dir / "run.prototext").write_text(str(run))
        (run_dir / "run.bin").write_bytes(run.SerializeToString())

    #########################################
    # Public Interface Methods
    ###################################

    @staticmethod
    def _vm_as_dict(vm: modeldb.VirtualMachine) -> "dict[str, Any]":
        return {
            "vm_id": vm.vm_id,
            "user_password": vm.user_password,
            "roles": vm.roles,
            "host": vm.host,
            "admin_name": vm.admin_name,
            "admin_pw": vm.admin_pw,
            "ip": vm.ip,
            "ssh": vm.ssh,
            "rdp": vm.rdp,
            "archived": vm.archived,
        }

    def get_vm(self, vm_id: str, create_if_none: bool = False) -> "dict[str, Any]":
        if create_if_none:
            vm, _ = modeldb.VirtualMachine.objects.get_or_create(vm_id=vm_id)
        else:
            vm = modeldb.VirtualMachine.objects.get(vm_id=vm_id)
        return self._vm_as_dict(vm)

    def _task_to_dict(self, task: modeldb.Task, include_dataset_stats: bool = False) -> "dict[str, Any]":
        def _add_dataset_stats(res: "dict[str, Any]", dataset_set: modeldb.Dataset) -> "dict[str, Any]":
            if not dataset_set:
                res["dataset_last_created"] = ""
                res["dataset_first_created"] = ""
                res["dataset_last_modified"] = ""
            else:
                res["dataset_last_created"] = dataset_set.latest("created").created.year
                res["dataset_first_created"] = dataset_set.earliest("created").created.year
                res["dataset_last_modified"] = dataset_set.latest("last_modified").created
            return res

        if task.organizer:
            org_name = task.organizer.name
            org_id = task.organizer.organizer_id
            org_year = task.organizer.years
        else:
            org_name = ""
            org_year = ""
            org_id = ""
        try:
            master_vm_id = task.vm.vm_id
        except AttributeError:
            logger.error(f"Task with id {task.task_id} has no master vm associated")
            master_vm_id = "None"

        result = {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "task_description": task.task_description,
            "organizer": org_name,
            "organizer_id": org_id,
            "web": task.web,
            "year": org_year,
            "featured": task.featured,
            "require_registration": task.require_registration,
            "require_groups": task.require_groups,
            "restrict_groups": task.restrict_groups,
            "allowed_task_teams": task.allowed_task_teams,
            "master_vm_id": master_vm_id,
            "is_ir_task": task.is_ir_task,
            "irds_re_ranking_image": task.irds_re_ranking_image,
            "irds_re_ranking_command": task.irds_re_ranking_command,
            "irds_re_ranking_resource": task.irds_re_ranking_resource,
            "dataset_count": task.dataset_set.count(),
            "software_count": task.software_set.count(),
            "max_std_out_chars_on_test_data": task.max_std_out_chars_on_test_data,
            "max_std_err_chars_on_test_data": task.max_std_err_chars_on_test_data,
            "max_file_list_chars_on_test_data": task.max_file_list_chars_on_test_data,
            "command_placeholder": task.command_placeholder,
            "command_description": task.command_description,
            "dataset_label": task.dataset_label,
            "max_std_out_chars_on_test_data_eval": task.max_std_out_chars_on_test_data_eval,
            "max_std_err_chars_on_test_data_eval": task.max_std_err_chars_on_test_data_eval,
            "max_file_list_chars_on_test_data_eval": task.max_file_list_chars_on_test_data_eval,
        }

        if include_dataset_stats:
            _add_dataset_stats(result, task.dataset_set.all())

        return result

    def _tasks_to_dict(
        self, tasks: "Iterable[modeldb.Task]", include_dataset_stats: bool = False
    ) -> "Iterable[dict[str, Any]]":
        for task in tasks:
            if not task.organizer:
                continue

            yield self._task_to_dict(task, include_dataset_stats)

    def get_tasks(self, include_dataset_stats: bool = False) -> "list[dict[str, Any]]":
        return list(self._tasks_to_dict(modeldb.Task.objects.select_related("organizer").all(), include_dataset_stats))

    def get_task(self, task_id: str, include_dataset_stats: bool) -> "dict[str, Any]":
        return self._task_to_dict(
            modeldb.Task.objects.select_related("organizer").get(task_id=task_id), include_dataset_stats
        )

    def _dataset_to_dict(self, dataset: modeldb.Dataset) -> "dict[str, Any]":
        evaluator_id = None if not dataset.evaluator else dataset.evaluator.evaluator_id

        runs = modeldb.Run.objects.filter(input_dataset__dataset_id=dataset.dataset_id, deleted=False)
        dataset_format = dataset.get_format()
        truth_format = dataset.get_truth_format()
        file_listing = dataset.get_file_listing()
        trusted_eval = dataset.get_trusted_evaluation()
        format_configuration = dataset.get_format_configuration()
        truth_format_configuration = dataset.get_truth_format_configuration()

        ret = {
            "display_name": dataset.display_name,
            "evaluator_id": evaluator_id,
            "dataset_id": dataset.dataset_id,
            "is_confidential": dataset.is_confidential,
            "is_deprecated": dataset.is_deprecated,
            "year": dataset.released,
            "task": dataset.default_task.task_id,
            "organizer": dataset.default_task.organizer.name,
            "organizer_id": dataset.default_task.organizer.organizer_id,
            "software_count": modeldb.Software.objects.filter(dataset__dataset_id=dataset.dataset_id).count(),
            "runs_count": runs.count(),
            "evaluations_count": runs.filter(evaluator__isnull=False).count(),
            "evaluations_public_count": modeldb.Review.objects.filter(
                run__run_id__in=[r.run_id for r in runs.filter(evaluator__isnull=False)]
            )
            .filter(published=True)
            .count(),
            "default_upload_name": dataset.default_upload_name,
            "created": dataset.created,
            "last_modified": dataset.last_modified,
            "irds_docker_image": dataset.irds_docker_image,
            "irds_import_command": dataset.irds_import_command,
            "irds_import_truth_command": dataset.irds_import_truth_command,
            "evaluator_git_runner_image": dataset.evaluator.git_runner_image if evaluator_id else None,
            "evaluator_git_runner_command": dataset.evaluator.git_runner_command if evaluator_id else None,
            "format": dataset_format,
            "run_format": dataset_format,
            "truth_format": truth_format,
            "description": dataset.description,
            "chatnoir_id": dataset.chatnoir_id,
            "ir_datasets_id": dataset.ir_datasets_id,
            "file_listing": file_listing,
            "trusted_eval": trusted_eval,
            "format_configuration": format_configuration,
            "truth_format_configuration": truth_format_configuration,
        }

        if trusted_eval:
            from tira_app.endpoints.misc import TRUSTED_EVALUATORS

            if "additional_args" in trusted_eval and trusted_eval["additional_args"]:
                ret["additional_args"] = json.dumps(trusted_eval["additional_args"])

            if any(i in TRUSTED_EVALUATORS["Retrieval"] for i in trusted_eval["measures"]):
                ret["evaluation_type"] = "eval-5"
            elif any(i in TRUSTED_EVALUATORS["TextGeneration"] for i in trusted_eval["measures"]):
                ret["evaluation_type"] = "eval-7"
            else:
                ret["evaluation_type"] = "eval-6"

            ret["trusted_measures"] = trusted_eval["measures"]
            ret["measures"] = trusted_eval["measures"]

        return ret

    def get_dataset(self, dataset_id: str) -> "dict[str, Any]":
        try:
            return self._dataset_to_dict(
                modeldb.Dataset.objects.select_related("default_task", "evaluator").get(dataset_id=dataset_id)
            )
        except modeldb.Dataset.DoesNotExist:
            return {}

    def get_datasets(self) -> "dict[str, dict[str, Any]]":
        """Get a dict of dataset_id: dataset_json_descriptor"""
        return {
            dataset.dataset_id: self._dataset_to_dict(dataset)
            for dataset in modeldb.Dataset.objects.select_related("default_task", "evaluator").all()
        }

    def get_datasets_by_task(
        self, task_id: str, include_deprecated: bool = False, return_only_names: bool = False
    ) -> "list[dict[str, Any]]":
        """return the list of datasets associated with this task_id
        @param task_id: id string of the task the dataset belongs to
        @param include_deprecated: Default False. If True, also returns datasets marked as deprecated.
        @return: a list of json-formatted datasets, as returned by get_dataset
        """
        ret = [
            d
            for d in modeldb.TaskHasDataset.objects.filter(task=task_id)
            if not (d.dataset.is_deprecated and not include_deprecated)
        ]

        if return_only_names:
            return [{"dataset_id": d.dataset.dataset_id, "display_name": d.dataset.display_name} for d in ret]
        else:
            return [self._dataset_to_dict(d.dataset) for d in ret]

    def get_docker_software(self, docker_software_id: int) -> "dict[str, Any]":
        try:
            return self._docker_software_to_dict(
                modeldb.DockerSoftware.objects.get(docker_software_id=docker_software_id)
            )
        except modeldb.Dataset.DoesNotExist:
            return {}

    def get_docker_software_by_name(self, name: str, vm_id: str, task_id: str) -> "dict[str, Any]":
        try:
            ret = modeldb.DockerSoftware.objects.filter(
                vm__vm_id=vm_id, task__task_id=task_id, display_name=name, deleted=False
            )
            if len(ret) == 0:
                return {}

            return self._docker_software_to_dict(ret[0])
        except modeldb.Dataset.DoesNotExist:
            return {}

    def run_is_public_and_unblinded(self, run_id: str) -> bool:
        run_id = modeldb.Run.objects.get(input_run__run_id=run_id).run_id
        review = modeldb.Review.objects.get(run_id=run_id)
        return review.published and not review.blinded

    def get_reranking_docker_softwares(self) -> "list[dict[str, Any]]":
        return [
            self._docker_software_to_dict(i) for i in modeldb.DockerSoftware.objects.filter(ir_re_ranking_input=True)
        ]

    def get_all_docker_software_rerankers(self) -> "list[dict[str, Any]]":
        return [self._docker_software_to_dict(i) for i in modeldb.DockerSoftware.objects.filter(ir_re_ranker=True)]

    def get_runs_for_docker_software(self, docker_software_id: int) -> "list[dict[str, Any]]":
        docker_software = modeldb.DockerSoftware.objects.get(docker_software_id=docker_software_id)

        return [self._run_as_dict(i) for i in modeldb.Run.objects.filter(docker_software=docker_software)]

    def update_input_run_id_for_run(self, run_id: str, input_run_id: str) -> None:
        print(f"Set input_run to {input_run_id} for run_id={run_id}")
        run = modeldb.Run.objects.get(run_id=run_id)
        run.input_run = modeldb.Run.objects.get(run_id=input_run_id) if input_run_id else None
        run.save()

    def _organizer_to_dict(self, organizer: modeldb.Organizer) -> "dict[str, Any]":
        git_integrations = []

        for git_integration in organizer.git_integrations.all():
            git_integrations += [{"namespace_url": git_integration.namespace_url, "private_token": "<OMMITTED>"}]

        git_integrations += [{"namespace_url": "", "private_token": ""}]

        return {
            "organizer_id": organizer.organizer_id,
            "name": organizer.name,
            "years": organizer.years,
            "web": organizer.web,
            "gitUrlToNamespace": git_integrations[0]["namespace_url"],
            "gitPrivateToken": git_integrations[0]["private_token"],
        }

    def get_organizer(self, organizer_id: str) -> "dict[str, Any]":
        return self._organizer_to_dict(modeldb.Organizer.objects.get(organizer_id=organizer_id))

    @staticmethod
    def create_submission_git_repo(
        repo_url: str,
        vm_id: str,
        docker_registry_user: str,
        docker_registry_token: str,
        discourse_api_key: str,
        reference_repository_url: str,
        external_owner: "Optional[str]",
        discourse_api_user: "Optional[str]",
        discourse_api_descr: str,
    ) -> modeldb.SoftwareSubmissionGitRepository:
        return modeldb.SoftwareSubmissionGitRepository.objects.create(
            repository_url=repo_url,
            vm=modeldb.VirtualMachine.objects.get(vm_id=vm_id),
            reference_repository_url=reference_repository_url,
            external_owner=external_owner,
            docker_registry_token=docker_registry_token,
            docker_registry_user=docker_registry_user,
            tira_client_token=discourse_api_key,
            tira_client_user=discourse_api_user,
            tira_client_description=discourse_api_descr,
        )

    @overload
    def get_submission_git_repo_or_none(
        self, repository_url: str, vm_id: str, return_object: "Literal[False]" = False
    ) -> dict[str, str]: ...

    @overload
    def get_submission_git_repo_or_none(
        self, repository_url: str, vm_id: str, return_object: "Literal[True]"
    ) -> "Optional[modeldb.SoftwareSubmissionGitRepository]": ...

    def get_submission_git_repo_or_none(
        self, repository_url: str, vm_id: str, return_object: bool = False
    ) -> "Union[dict[str, str], Optional[modeldb.SoftwareSubmissionGitRepository]]":
        try:
            ret = modeldb.SoftwareSubmissionGitRepository.objects.get(repository_url=repository_url, vm__vm_id=vm_id)

            if return_object:
                return ret

            return {
                "repo_url": ret.repository_url,
                "http_repo_url": "https://github.com/" + ret.repository_url,
                "ssh_repo_url": f"git@github.com:{ret.repository_url}.git",
                "owner_url": ret.external_owner,
                "http_owner_url": "https://github.com/" + ret.external_owner,
            }
        except Exception:
            return {} if not return_object else None

    def get_host_list(self) -> list[str]:
        return [line.strip() for line in self.host_list_file.read_text().splitlines()]

    def get_ova_list(self) -> list[str]:
        return [f"{ova_file.stem}.ova" for ova_file in self.ova_dir.glob("*.ova")]

    def get_organizer_list(self) -> "list[dict[str, Any]]":
        return [self._organizer_to_dict(organizer) for organizer in modeldb.Organizer.objects.all()]

    def get_vm_list(self) -> list[list[str]]:
        """load the vm-info file which stores all active vms as such:
        <hostname>\t<vm_id>[\t<state>]\n
        ...

        returns a list of tuples (hostname, vm_id, state)
        """

        def parse_vm_list(vm_list: "Iterable[str]") -> "Iterable[list[str]]":
            for list_entry in vm_list:
                try:
                    tmp = list_entry.split("\t")
                    yield [tmp[0], tmp[1].strip(), tmp[2].strip() if len(tmp) > 2 else ""]
                except IndexError as e:
                    logger.error(e, list_entry)

        return list(parse_vm_list(open(self.vm_list_file, "r")))

    @staticmethod
    def get_vms_by_dataset(dataset_id: str) -> list[str]:
        """return a list of vm_id's that have runs on this dataset"""
        return [
            run.software.vm.vm_id
            for run in modeldb.Run.objects.select_related("input_dataset", "software")
            .exclude(input_dataset=None)
            .filter(input_dataset__dataset_id=dataset_id)
            .exclude(software=None)
            .all()
        ]

    @staticmethod
    def _run_as_dict(run: modeldb.Run) -> "dict[str, Any]":
        is_evaluation = (
            False if not run.input_run or run.input_run.run_id == "none" or run.input_run.run_id == "None" else True
        )
        software = None
        vm = None
        software_id, evaluator_id, docker_software_id, upload_id = None, None, None, None
        if run.software:
            software = run.software.software_id
            software_id = run.software.software_id
        elif run.evaluator:
            software = run.evaluator.evaluator_id
            evaluator_id = software
        elif run.docker_software:
            software = run.docker_software.display_name
            vm = run.docker_software.vm.vm_id
            is_evaluation = False
            docker_software_id = run.docker_software.docker_software_id
        elif run.upload:
            software = run.upload.display_name
            upload_id = run.upload.id
            vm = run.upload.vm.vm_id

        return {
            "software": software,
            "vm": vm,
            "run_id": run.run_id,
            "input_run_id": (
                ""
                if not run.input_run or run.input_run.run_id == "none" or run.input_run.run_id == "None"
                else run.input_run.run_id
            ),
            "is_evaluation": is_evaluation,
            "dataset": "" if not run.input_dataset else run.input_dataset.dataset_id,
            "downloadable": run.downloadable,
            "software_id": software_id,
            "evaluator_id": evaluator_id,
            "docker_software_id": docker_software_id,
            "upload_id": upload_id,
        }

    def get_run(
        self, dataset_id: "Optional[str]", vm_id: "Optional[str]", run_id: str, return_deleted: bool = False
    ) -> "dict[str, Any]":
        run = modeldb.Run.objects.select_related("software", "input_dataset").get(run_id=run_id)

        if run.deleted and not return_deleted:
            return {}
        return self._run_as_dict(run)

    def get_vm_runs_by_dataset(
        self, dataset_id: str, vm_id: str, return_deleted: bool = False
    ) -> "list[dict[str, Any]]":
        return [
            self._run_as_dict(run)
            for run in modeldb.Run.objects.select_related("software", "input_dataset").filter(
                input_dataset__dataset_id=dataset_id, software__vm__vm_id=vm_id
            )
            if (run.deleted or not return_deleted)
        ]

    def _get_ordered_runs_from_reviews(
        self, reviews, vm_id: str, preloaded: bool = True, is_upload: bool = False, is_docker: bool = False
    ) -> "Iterable[dict[str, Any]]":
        """yields all runs with reviews and their evaluation runs with reviews produced by software from a given vm
            evaluation runs (which have a run as input run) are yielded directly after the runs they use.

        :param reviews: a querySet of modeldb.Review objects to
        :param vm_id: the vm_id of the software or upload
        :param preloaded: If False, do a new database request to get the evaluation runs.
            Otherwise assume they were preloaded
        :param is_upload: if true, get only uploaded runs
        """

        def _run_dict(review_obj: modeldb.Review) -> "dict[str, Any]":
            run = self._run_as_dict(review_obj.run)
            run["review"] = self._review_as_dict(review_obj)
            run["reviewed"] = (
                True
                if not review_obj.has_errors and not review_obj.has_no_errors and not review_obj.has_warnings
                else False
            )
            run["is_upload"] = is_upload
            run["is_docker"] = is_docker
            return run

        if is_upload:
            reviews_qs = reviews.filter(run__upload__vm__vm_id=vm_id).all()
        elif is_docker:
            reviews_qs = reviews.filter(run__docker_software__vm__vm_id=vm_id).all()
        else:
            reviews_qs = reviews.filter(run__software__vm__vm_id=vm_id).all()

        for review in reviews_qs:
            yield _run_dict(review)

            r2 = (
                reviews.filter(run__input_run__run_id=review.run.run_id).all()
                if preloaded
                else modeldb.Review.objects.select_related("run").filter(run__input_run__run_id=review.run.run_id).all()
            )

            for review2 in r2:
                yield _run_dict(review2)

    def upload_to_dict(self, upload: modeldb.Upload, vm_id: str) -> "dict[str, Any]":
        def _runs_by_upload(up: modeldb.Upload) -> "list[dict[str, Any]]":
            reviews = (
                modeldb.Review.objects.select_related(
                    "run", "run__upload", "run__evaluator", "run__input_run", "run__input_dataset"
                )
                .filter(run__upload=up)
                .all()
            )

            return list(self._get_ordered_runs_from_reviews(reviews, vm_id, preloaded=False, is_upload=True))

        return {
            "id": upload.id,
            "task_id": upload.task.task_id,
            "vm_id": upload.vm.vm_id,
            "dataset": None if not upload.dataset else upload.dataset.dataset_id,
            "last_edit": upload.last_edit_date,
            "runs": _runs_by_upload(upload),
            "display_name": upload.display_name,
            "description": upload.description,
            "paper_link": upload.paper_link,
            "rename_to": upload.rename_to,
        }

    def get_upload_with_runs(self, task_id: str, vm_id: str) -> "list[dict[str, Any]]":
        ret = []
        for upload in self.get_uploads(task_id, vm_id, return_names_only=False):
            ret += [self.upload_to_dict(upload, vm_id)]

        return ret

    def get_upload(self, task_id: str, vm_id: str, upload_id: str) -> "dict[str, Any]":
        return self.upload_to_dict(modeldb.Upload.objects.get(vm__vm_id=vm_id, id=upload_id), vm_id)

    def get_discourse_token_for_user(self, vm_id: str) -> "Optional[str]":
        try:
            return modeldb.DiscourseTokenForUser.objects.get(vm_id__vm_id=vm_id).token
        except Exception:
            return None

    def create_discourse_token_for_user(self, vm_id: str, discourse_api_key: str) -> None:
        modeldb.DiscourseTokenForUser.objects.create(
            vm_id=modeldb.VirtualMachine.objects.get(vm_id=vm_id), token=discourse_api_key
        )

    @overload
    @staticmethod
    def get_uploads(task_id: str, vm_id: str, return_names_only: "Literal[True]" = True) -> "list[dict[str, Any]]": ...

    @overload
    @staticmethod
    def get_uploads(task_id: str, vm_id: str, return_names_only: "Literal[False]") -> modeldb.Upload: ...

    @staticmethod
    def get_uploads(
        task_id: str, vm_id: str, return_names_only: bool = True
    ) -> "Union[list[dict[str, Any]], modeldb.Upload]":
        ret = modeldb.Upload.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, deleted=False)

        if return_names_only:
            return [{"id": i.id, "display_name": i.display_name} for i in ret]
        else:
            return ret

    def _docker_software_to_dict(self, ds: modeldb.DockerSoftware) -> "dict[str, Any]":
        input_docker_software = None
        previous_stages = None
        if ds.input_docker_software:
            input_docker_software = ds.input_docker_software.display_name
        if ds.input_upload:
            input_docker_software = "Upload " + ds.input_upload.display_name

        if input_docker_software:
            previous_stages = [input_docker_software]
            additional_inputs = (
                modeldb.DockerSoftwareHasAdditionalInput.objects.select_related("input_docker_software", "input_upload")
                .filter(docker_software__docker_software_id=ds.docker_software_id)
                .order_by("position")
            )
            for i in additional_inputs:
                if i.input_docker_software:
                    previous_stages += [i.input_docker_software.display_name]
                else:
                    previous_stages += [i.input_upload.display_name]
        link_code = None

        try:
            link_code = modeldb.LinkToSoftwareSubmissionGitRepository.objects.get(
                docker_software__docker_software_id=ds.docker_software_id
            )
            link_code = self.__link_to_code(link_code.build_environment)
        except Exception:
            link_code = None

        mount_hf_model = None
        hf_models = modeldb.HuggingFaceModelsOfSoftware.objects.filter(
            docker_software__docker_software_id=ds.docker_software_id
        ).only("mount_hf_model")

        if hf_models and len(hf_models) > 0:
            mount_hf_model = hf_models[0].mount_hf_model

        source_code_remotes = None
        try:
            source_code_remotes = None if not ds.source_code_remotes else json.loads(ds.source_code_remotes)
        except Exception:
            pass

        if source_code_remotes:
            source_code_remotes = [{"display_name": k, "name": v} for k, v in source_code_remotes.items()]

            if ds.source_code_commit:
                for i in source_code_remotes:
                    remote = i["name"]
                    if remote.startswith("https://github.com/"):
                        i["href"] = remote.replace(".git", "") + "/tree/" + ds.source_code_commit
                    if remote.startswith("git@github.com:"):
                        i["href"] = (
                            "https://github.com/"
                            + remote.split("git@github.com:")[1].replace(".git", "")
                            + "/tree/"
                            + ds.source_code_commit
                        )

        return {
            "docker_software_id": ds.docker_software_id,
            "display_name": ds.display_name,
            "user_image_name": ds.user_image_name,
            "command": ds.command,
            "tira_image_name": ds.tira_image_name,
            "task_id": ds.task.task_id,
            "vm_id": ds.vm.vm_id,
            "description": ds.description,
            "paper_link": ds.paper_link,
            "input_docker_software": input_docker_software,
            "source_code_active_branch": ds.source_code_active_branch,
            "source_code_commit": ds.source_code_commit,
            "source_code_remotes": source_code_remotes,
            "input_docker_software_id": (
                ds.input_docker_software.docker_software_id if ds.input_docker_software else None
            ),
            "input_upload_id": ds.input_upload.id if ds.input_upload else None,
            "ir_re_ranker": True if ds.ir_re_ranker else False,
            "public_image_name": ds.public_image_name,
            "ir_re_ranking_input": True if ds.ir_re_ranking_input else False,
            "previous_stages": previous_stages,
            "tira_image_workdir": ds.tira_image_workdir,
            "link_code": link_code,
            "mount_hf_model": mount_hf_model,
        }

    @staticmethod
    def cloned_submissions_of_user(vm_id: str, task_id: str) -> "list[dict[str, Any]]":
        ret: list[dict[str, Any]] = []
        for i in modeldb.SoftwareClone.objects.filter(vm__vm_id=vm_id, task__task_id=task_id).select_related(
            "docker_software", "upload"
        ):
            if i.docker_software:
                ret += [
                    {
                        "docker_software_id": i.docker_software.docker_software_id,
                        "display_name": i.docker_software.display_name,
                        "type": "docker",
                    }
                ]
            elif i.upload:
                ret += [{"id": i.upload.id, "display_name": i.upload.display_name, "type": "upload"}]

        return ret

    @staticmethod
    def submissions_of_user(vm_id: str) -> "list[dict[str, Any]]":
        ret: list[dict[str, Any]] = []
        for i in modeldb.DockerSoftware.objects.filter(vm__vm_id=vm_id, deleted=False):
            ret += [
                {
                    "title": i.task_id + "/" + i.display_name,
                    "task_id": i.task_id,
                    "type": "docker",
                    "id": i.docker_software_id,
                }
            ]

        for i in modeldb.Upload.objects.filter(vm__vm_id=vm_id, deleted=False):
            ret += [{"title": i.task_id + "/" + i.display_name, "task_id": i.task_id, "type": "upload", "id": i.id}]

        return ret

    @staticmethod
    def import_submission(task_id, vm_id: str, submission_type: str, s_id: str) -> None:
        docker_software, upload = None, None
        if submission_type == "docker":
            docker_software = modeldb.DockerSoftware.objects.filter(
                vm__vm_id=vm_id, docker_software_id=s_id, deleted=False
            )[0]
        else:
            upload = modeldb.Upload.objects.filter(vm__vm_id=vm_id, id=s_id, deleted=False)[0]

        modeldb.SoftwareClone.objects.create(
            vm=modeldb.VirtualMachine.objects.get(vm_id=vm_id),
            task=modeldb.Task.objects.get(task_id=task_id),
            docker_software=docker_software,
            upload=upload,
        )

    def get_count_of_missing_reviews(self, task_id: str) -> list[dict[str, str]]:
        prepared_statement = """
        SELECT
            tira_run.input_dataset_id,
            SUM(CASE WHEN tira_review.has_errors = False AND tira_review.has_no_errors = FALSE AND
                tira_review.has_warnings = FALSE THEN 1 ELSE 0 END) as ToReview,
            COUNT(*) as submissions
        FROM
            tira_run
        INNER JOIN
            tira_taskhasdataset ON tira_run.input_dataset_id = tira_taskhasdataset.dataset_id
        LEFT JOIN
            tira_review ON tira_run.run_id = tira_review.run_id
        WHERE
            tira_taskhasdataset.task_id = %s
        GROUP BY
            tira_run.input_dataset_id;
        """

        ret: list[dict[str, str]] = []
        rows = self.__execute_raw_sql_statement(prepared_statement, params=[task_id])
        for dataset_id, to_review, submissions in rows:
            ret += [{"dataset_id": dataset_id, "to_review": to_review, "submissions": submissions}]

        return ret

    def get_count_of_team_submissions(self, task_id: str) -> "list[dict[str, Any]]":
        task = self.get_task(task_id, False)
        all_teams_on_task = set([i.strip() for i in task["allowed_task_teams"].split() if i.strip()])
        prepared_statement = """
            SELECT
                tira_dockersoftware.vm_id as vm,
                SUM(CASE WHEN tira_review.has_errors = False AND tira_review.has_no_errors = FALSE AND
                    tira_review.has_warnings = FALSE THEN 1 ELSE 0 END) as ToReview,
                COUNT(*) - SUM(CASE WHEN tira_review.has_errors = False AND tira_review.has_no_errors = FALSE AND
                    tira_review.has_warnings = FALSE THEN 1 ELSE 0 END) as submissions,
                COUNT(*) as total
            FROM
                tira_run
            INNER JOIN
                tira_taskhasdataset ON tira_run.input_dataset_id = tira_taskhasdataset.dataset_id
            LEFT JOIN
                tira_review ON tira_run.run_id = tira_review.run_id
            LEFT JOIN
                tira_dockersoftware ON tira_run.docker_software_id = tira_dockersoftware.docker_software_id
            WHERE
                tira_taskhasdataset.task_id = %s
            GROUP BY
                tira_dockersoftware.vm_id;
            """

        ret: list[dict[str, Any]] = []
        rows = self.__execute_raw_sql_statement(prepared_statement, params=[task_id])
        for vm, to_review, submissions, total in rows:
            if vm is not None:
                ret += [
                    {
                        "team": vm,
                        "reviewed": submissions,
                        "to_review": to_review,
                        "total": total,
                        "link": link_to_discourse_team(vm),
                    }
                ]
        for team in all_teams_on_task:
            if team not in [t["team"] for t in ret]:
                ret += [{"team": team, "reviewed": 0, "to_review": 0, "total": 0, "link": link_to_discourse_team(team)}]
        return ret

    def all_runs(self) -> dict:
        prepared_statement = """SELECT
                    tira_run.run_id, tira_run.task_id, tira_run.input_dataset_id,
                    tira_software.software_id, tira_software.vm_id, tira_dockersoftware.docker_software_id,
                    tira_dockersoftware.vm_id, tira_dockersoftware.display_name,
                    tira_upload.id, tira_upload.vm_id, tira_upload.display_name,
                    tira_run_review.published, tira_run_review.blinded
            FROM
                tira_run as evaluation_run
            INNER JOIN
                tira_run as tira_run ON evaluation_run.input_run_id = tira_run.run_id
            LEFT JOIN
                tira_upload ON tira_run.upload_id = tira_upload.id
            LEFT JOIN
                tira_software ON tira_run.software_id = tira_software.id
            LEFT JOIN
                tira_dockersoftware ON tira_run.docker_software_id = tira_dockersoftware.docker_software_id
            LEFT JOIN
                tira_review as tira_run_review ON evaluation_run.run_id = tira_run_review.run_id
            LEFT JOIN
                tira_softwareclone AS software_clone ON
                        tira_dockersoftware.docker_software_id = software_clone.docker_software_id
            LEFT JOIN
                tira_softwareclone AS upload_clone ON tira_run.upload_id = upload_clone.upload_id

            ORDER BY
                tira_run.run_id ASC;
        """
        ret: dict[Any, Any] = {}
        for (
            run_id,
            task_id,
            dataset_id,
            software_id,
            software_vm,
            docker_id,
            docker_vm,
            docker_title,
            upload_id,
            upload_vm,
            upload_title,
            published,
            blinded,
        ) in self.__execute_raw_sql_statement(prepared_statement, []):
            vm = None
            title = None
            if software_vm is not None:
                assert docker_vm is None and upload_vm is None
                vm = software_vm
                title = software_id
                identifier = software_id
                t = "VM"
            if docker_vm is not None and software_vm is None and upload_vm is None:
                vm = docker_vm
                title = docker_title
                identifier = docker_id
                t = "Docker"
            if upload_vm is not None and software_vm is None and docker_id is None:
                vm = upload_vm
                title = upload_title
                identifier = upload_id
                t = "Upload"

            if vm is None:
                continue
            assert vm is not None and title is not None

            if vm not in ret:
                ret[vm] = {}
            if title not in ret[vm]:
                ret[vm][title] = {}

            if run_id in ret[vm][title]:
                blinded = ret[vm][title][run_id]["blinded"] and blinded
                published = ret[vm][title][run_id]["published"] or published

            ret[vm][title][run_id] = {
                "type": t,
                "published": published,
                "blinded": blinded,
                "task": task_id,
                "dataset": dataset_id,
                "software-id": identifier,
            }

        return ret

    def all_run_formats(self):
        prepared_statement = """
            SELECT
                tira_run.run_id, tira_run.software_id, tira_run.upload_id,
                tira_run.docker_software_id, tira_run.input_dataset_id, tira_run.valid_formats
            FROM
                tira_run
            LEFT JOIN
                tira_review as tira_run_review ON tira_run.run_id = tira_run_review.run_id
            WHERE
                valid_formats is not NULL and tira_run_review.published = TRUE AND tira_run_review.blinded = FALSE
            """
        ret = {"Docker": {}, "Upload": {}, "VM": {}}

        rows = self.__execute_raw_sql_statement(prepared_statement, params=[])
        for run_id, software_id, upload_id, docker_software_id, input_dataset_id, valid_formats in rows:
            if software_id:
                field = "VM"
                identifier = software_id
            elif upload_id:
                field = "Upload"
                identifier = upload_id
            elif docker_software_id:
                field = "Docker"
                identifier = docker_software_id

            if identifier not in ret[field]:
                ret[field][identifier] = {}

            ret[field][identifier][input_dataset_id] = json.loads(valid_formats)
        return ret

    def runs(self, task_id: str, dataset_id: str, vm_id: str, software_id: str) -> "list[dict[str, Any]]":
        prepared_statement = """
                SELECT
                    tira_run.run_id, tira_dockersoftware.docker_software_id, tira_upload.id
                FROM
                    tira_run
                LEFT JOIN
                    tira_upload ON tira_run.upload_id = tira_upload.id
                LEFT JOIN
                    tira_software ON tira_run.software_id = tira_software.id
                LEFT JOIN
                    tira_dockersoftware ON tira_run.docker_software_id = tira_dockersoftware.docker_software_id
                LEFT JOIN
                    tira_review as tira_run_review ON tira_run.run_id = tira_run_review.run_id
                LEFT JOIN
                    tira_softwareclone AS software_clone ON
                        tira_dockersoftware.docker_software_id = software_clone.docker_software_id
                LEFT JOIN
                    tira_softwareclone AS upload_clone ON tira_run.upload_id = upload_clone.upload_id
                WHERE
                    ((tira_run_review.published = TRUE AND tira_run_review.blinded = FALSE) OR
                        tira_dockersoftware.task_id = 'ir-lab-padua-2024' OR
                        tira_dockersoftware.task_id = 'ir-lab-sose-2024')
                    AND tira_run.input_dataset_id = %s
                    AND (tira_dockersoftware.task_id = %s OR tira_upload.task_id = %s OR tira_software.task_id = %s  or
                        software_clone.task_id = %s or upload_clone.task_id = %s)
                    AND (tira_dockersoftware.vm_id = %s OR tira_upload.vm_id = %s OR tira_software.vm_id = %s)
                    AND (tira_dockersoftware.display_name = %s OR tira_upload.display_name = %s OR
                        tira_software.id = %s)

                ORDER BY
                    tira_run.run_id ASC;
                """
        params = [
            dataset_id,
            task_id,
            task_id,
            task_id,
            task_id,
            task_id,
            vm_id,
            vm_id,
            vm_id,
            software_id,
            software_id,
            software_id,
        ]
        return [
            {"run_id": i[0], "software_id": i[1], "upload_id": i[2]}
            for i in self.__execute_raw_sql_statement(prepared_statement, params)
        ]

    def get_runs_for_vm(
        self,
        vm_id: str,
        docker_software_id: "Optional[int]",
        upload_id: "Optional[int]",
        include_unpublished: bool = True,
        round_floats: bool = True,
        show_only_unreviewed: bool = False,
    ) -> "tuple[list[str], list[dict[str, Any]]]":
        prepared_statement = """
        SELECT
            evaluation_run.input_dataset_id, evaluation_run.run_id, input_run.run_id, tira_upload.display_name,
            tira_upload.vm_id, tira_software.vm_id, tira_dockersoftware.display_name, tira_dockersoftware.vm_id,
            tira_evaluation_review.published, tira_evaluation_review.blinded, tira_run_review.published,
            tira_run_review.blinded, tira_evaluation.measure_key, tira_evaluation.measure_value,
            tira_run_review.reviewer_id, tira_run_review.no_errors, tira_run_review.has_errors,
            tira_run_review.has_no_errors, tira_evaluation_review.reviewer_id, tira_run_review.reviewer_id,
            tira_linktosoftwaresubmissiongitrepository.build_environment
        FROM
            tira_run as evaluation_run
        INNER JOIN
             tira_run as input_run ON evaluation_run.input_run_id = input_run.run_id
        LEFT JOIN
             tira_upload ON input_run.upload_id = tira_upload.id
        LEFT JOIN
             tira_software ON input_run.software_id = tira_software.id
        LEFT JOIN
             tira_dockersoftware ON input_run.docker_software_id = tira_dockersoftware.docker_software_id
        LEFT JOIN
             tira_linktosoftwaresubmissiongitrepository ON
                tira_dockersoftware.docker_software_id = tira_linktosoftwaresubmissiongitrepository.docker_software_id
        LEFT JOIN
            tira_review as tira_evaluation_review ON evaluation_run.run_id = tira_evaluation_review.run_id
        LEFT JOIN
            tira_review as tira_run_review ON input_run.run_id = tira_run_review.run_id
        LEFT JOIN
            tira_evaluation ON tira_evaluation.run_id = evaluation_run.run_id
        WHERE
            evaluation_run.input_run_id is not null AND evaluation_run.deleted = FALSE
             AND evaluation_run.evaluator_id IS NOT NULL AND input_run.deleted = False
             AND (tira_dockersoftware.vm_id = %s OR tira_upload.vm_id = %s OR tira_software.vm_id = %s ) AND <CLAUSE>
        ORDER BY
            tira_evaluation.id ASC;
        """

        params: list[Union[str, int]] = [vm_id, vm_id, vm_id]

        if upload_id:
            prepared_statement = prepared_statement.replace("<CLAUSE>", "tira_upload.id = %s")
            params += [upload_id]
        else:
            assert docker_software_id is not None
            prepared_statement = prepared_statement.replace("<CLAUSE>", "tira_dockersoftware.docker_software_id = %s")
            params += [docker_software_id]

        rows = self.__execute_raw_sql_statement(prepared_statement, params)
        ret = self.__parse_submissions(rows, include_unpublished, round_floats, True, show_only_unreviewed)
        from_uploads = []

        if upload_id:
            prepared_statement = """
                    SELECT
                        input_run.input_dataset_id, input_run.run_id, tira_upload.display_name
                    FROM
                        tira_run as input_run
                   INNER JOIN
                        tira_upload ON input_run.upload_id = tira_upload.id
                    LEFT JOIN
                        tira_run as evaluation_run ON evaluation_run.input_run_id = input_run.run_id
                    WHERE
                        evaluation_run.input_run_id is null AND input_run.deleted = False
                        AND tira_upload.vm_id = %s AND tira_upload.id = %s
                    ORDER BY
                        input_run.run_id ASC;
                    """

            rows = self.__execute_raw_sql_statement(prepared_statement, [vm_id, upload_id])

            for dataset_id, run_id, display_name in rows:
                print(run_id)
                from_uploads += [
                    {
                        "dataset_id": dataset_id,
                        "vm_id": vm_id,
                        "input_software_name": display_name,
                        "run_id": run_id,
                        "input_run_id": run_id,
                        "published": False,
                        "blinded": True,
                        "is_upload": True,
                        "is_software": False,
                        "review_state": "no-review",
                        "measures": {},
                    }
                ]

        return ret[0], (ret[1] + from_uploads)

    def get_docker_softwares_with_runs(self, task_id: str, vm_id: str) -> "list[dict[str, Any]]":
        def _runs_by_docker_software(ds: modeldb.DockerSoftware) -> "list[dict[str, Any]]":
            reviews = (
                modeldb.Review.objects.select_related(
                    "run", "run__upload", "run__evaluator", "run__input_run", "run__input_dataset"
                )
                .filter(run__docker_software=ds)
                .all()
            )

            return list(self._get_ordered_runs_from_reviews(reviews, vm_id, preloaded=False, is_docker=True))

        docker_softwares = self.get_docker_softwares(task_id, vm_id, return_only_names=False)

        docker_softwares = [
            {**self._docker_software_to_dict(ds), "runs": _runs_by_docker_software(ds)} for ds in docker_softwares
        ]

        return docker_softwares

    @overload
    @staticmethod
    def get_docker_softwares(
        task_id: str, vm_id: str, return_only_names: "Literal[False]", return_code_submissions: bool = False
    ) -> "BaseManager[modeldb.DockerSoftware]": ...

    @overload
    @staticmethod
    def get_docker_softwares(
        task_id: str, vm_id: str, return_only_names: "Literal[True]" = True, return_code_submissions: bool = False
    ) -> "list[dict[str, Any]]": ...

    @staticmethod
    def get_docker_softwares(
        task_id: str, vm_id: str, return_only_names: bool = True, return_code_submissions: bool = False
    ):
        ret = modeldb.DockerSoftware.objects.filter(
            vm__vm_id=vm_id,
            task__task_id=task_id,
            deleted=False,
            source_code_commit__isnull=not return_code_submissions,
        )

        if return_only_names:
            return [{"docker_software_id": i.docker_software_id, "display_name": i.display_name} for i in ret]
        else:
            return ret

    def get_public_docker_softwares(self, task_id: str, return_only_names: bool = True, return_details: bool = True):
        ret = modeldb.DockerSoftware.objects.filter(
            task__task_id=task_id, deleted=False, public_image_name__isnull=False
        )

        ret = [i for i in ret if i.public_image_name and i.public_image_size]

        if return_only_names:
            return [
                {"docker_software_id": i.docker_software_id, "display_name": i.display_name, "vm_id": i.vm_id}
                for i in ret
            ]
        elif return_details:
            return [self._docker_software_to_dict(i) for i in ret]
        else:
            return ret

    def delete_docker_software(self, task_id: str, vm_id: str, docker_software_id: str) -> bool:
        software_qs = modeldb.DockerSoftware.objects.filter(
            vm_id=vm_id, task_id=task_id, docker_software_id=docker_software_id
        )

        reviews_qs = modeldb.Review.objects.filter(
            run__input_run__docker_software__docker_software_id=docker_software_id,
            run__input_run__docker_software__task_id=task_id,
            run__input_run__docker_software__vm_id=vm_id,
            no_errors=True,
        )

        if not reviews_qs.exists() and software_qs.exists():
            software_qs.delete()
            return True

        return False

    def get_irds_docker_software_id(
        self, task_id, vm_id, software_id: "Optional[str]", docker_software_id: int
    ) -> "Optional[modeldb.DockerSoftware]":
        task = self.get_task(task_id, False)

        is_ir_task = task.get("is_ir_task", False)
        irds_re_ranking_image = task.get("irds_re_ranking_image", "")
        irds_re_ranking_command = task.get("irds_re_ranking_command", "")
        irds_re_ranking_resource = task.get("irds_re_ranking_resource", "")
        irds_display_name = (
            "IRDS-Job For " + task_id + f" (vm: {vm_id}, software: {software_id}, docker: {docker_software_id})"
        )

        if not is_ir_task or not irds_re_ranking_image or not irds_re_ranking_command or not irds_re_ranking_resource:
            raise ValueError("This is not a irds-re-ranking task:" + str(task))

        task = modeldb.Task.objects.get(task_id=task_id)
        vm = modeldb.VirtualMachine.objects.get(vm_id="froebe")

        ret = modeldb.DockerSoftware.objects.filter(
            vm=vm,
            task=task,
            command=irds_re_ranking_command,
            tira_image_name=irds_re_ranking_image,
            user_image_name=irds_re_ranking_image,
            display_name=irds_display_name,
        )

        if len(ret) > 0:
            return ret[0]

        modeldb.DockerSoftware.objects.create(
            vm=vm,
            task=task,
            command=irds_re_ranking_command,
            tira_image_name=irds_re_ranking_image,
            user_image_name=irds_re_ranking_image,
            display_name=irds_display_name,
        )

        ret = modeldb.DockerSoftware.objects.filter(
            vm=vm,
            task=task,
            command=irds_re_ranking_command,
            tira_image_name=irds_re_ranking_image,
            user_image_name=irds_re_ranking_image,
            display_name=irds_display_name,
        )

        return ret[0] if len(ret) > 0 else None

    def get_evaluations_of_run(self, vm_id: str, run_id: str) -> list:
        prepared_statement = """
            SELECT
                evaluation_run.run_id
            FROM
                tira_run as evaluation_run
            INNER JOIN
                tira_run as input_run ON evaluation_run.input_run_id = input_run.run_id
            LEFT JOIN
                tira_upload ON input_run.upload_id = tira_upload.id
            LEFT JOIN
                tira_software ON input_run.software_id = tira_software.id
            LEFT JOIN
                tira_dockersoftware ON input_run.docker_software_id = tira_dockersoftware.docker_software_id
            WHERE
                evaluation_run.input_run_id = %s and evaluation_run.evaluator_id IS NOT NULL
                AND (tira_upload.vm_id = %s OR tira_software.vm_id = %s OR tira_dockersoftware.vm_id = %s)
            """
        return [i[0] for i in self.__execute_raw_sql_statement(prepared_statement, [run_id, vm_id, vm_id, vm_id])]

    def get_vms_with_reviews(self, dataset_id: str) -> "list[dict[str, Any]]":
        """returns a list of dicts with:
        {"vm_id": vm_id,
        "runs": [{run, review}, ...],
        "unreviewed_count": unreviewed_count,
        "blinded_count": blinded_count,
        "published_count": published_count}
        """
        results: list[dict[str, Any]] = []
        reviews = (
            modeldb.Review.objects.select_related(
                "run", "run__software", "run__docker_software", "run__evaluator", "run__upload", "run__input_run"
            )
            .filter(run__input_dataset__dataset_id=dataset_id)
            .all()
        )

        upload_vms = {vm_id["run__upload__vm__vm_id"] for vm_id in reviews.values("run__upload__vm__vm_id")}
        software_vms = {vm_id["run__software__vm__vm_id"] for vm_id in reviews.values("run__software__vm__vm_id")}
        docker_vms = {
            vm_id["run__docker_software__vm__vm_id"] for vm_id in reviews.values("run__docker_software__vm__vm_id")
        }

        for vm_id in upload_vms.union(software_vms).union(docker_vms):
            if not vm_id:
                continue
            runs = []
            if vm_id in upload_vms:
                runs += list(self._get_ordered_runs_from_reviews(reviews, vm_id, is_upload=True))
            if vm_id in software_vms:
                runs += list(self._get_ordered_runs_from_reviews(reviews, vm_id, is_upload=False))
            if vm_id in docker_vms:
                runs += list(self._get_ordered_runs_from_reviews(reviews, vm_id, is_docker=True))

            results.append(
                {
                    "vm_id": vm_id,
                    "runs": runs,
                    "unreviewed_count": len([_["reviewed"] for _ in runs if _["reviewed"] is True]),
                    "blinded_count": len([_["review"]["blinded"] for _ in runs if _["review"]["blinded"] is True]),
                    "published_count": len(
                        [_["review"]["published"] for _ in runs if _["review"]["published"] is True]
                    ),
                }
            )
        return results

    def get_vm_runs_by_task(self, task_id: str, vm_id: str, return_deleted: bool = False) -> "list[dict[str, Any]]":
        """returns a list of all the runs of a user over all datasets in json (as returned by _load_user_runs)"""
        return [
            self._run_as_dict(run)
            for run in modeldb.Run.objects.select_related("software", "input_dataset").filter(
                software__vm__vm_id=vm_id, input_dataset__default_task__task_id=task_id, software__task__task_id=task_id
            )
            if (run.deleted or not return_deleted)
        ]

    def get_evaluator(self, dataset_id: str, task_id: "Optional[str]" = None) -> "dict[str, Any]":
        """returns a dict containing the evaluator parameters:

        vm_id: id of the master vm running the evaluator
        host: ip or hostname of the host
        command: command to execute to run the evaluator. NOTE: contains variables the host needs to resolve
        working_dir: where to execute the command
        """
        evaluator = modeldb.Dataset.objects.get(dataset_id=dataset_id).evaluator
        vmhe = modeldb.VirtualMachineHasEvaluator.objects.filter(evaluator=evaluator)
        if vmhe:
            master_vm = vmhe[0].vm
            vm_id = master_vm.vm_id
            host = master_vm.host
        else:
            vm_id = ""
            host = ""

        if not task_id:
            dataset = modeldb.Dataset.objects.filter(evaluator=evaluator).latest("last_modified")
            task_id = dataset.default_task.task_id

        return {
            "vm_id": vm_id,
            "host": host,
            "command": evaluator.command,
            "task_id": task_id,
            "evaluator_id": evaluator.evaluator_id,
            "working_dir": evaluator.working_directory,
            "measures": evaluator.measures,
            "is_git_runner": evaluator.is_git_runner,
            "git_runner_image": evaluator.git_runner_image,
            "git_runner_command": evaluator.git_runner_command,
            "git_repository_id": evaluator.git_repository_id,
        }

    @staticmethod
    def get_vm_evaluations_by_dataset(
        dataset_id: str, vm_id: str, only_public_results: bool = True
    ) -> "dict[str, dict[str, Any]]":
        """Return a dict of run_id: evaluation_results for the given vm on the given dataset
            {run_id: {measure.key: measure.value for measure in evaluation.measure}}

        @param only_public_results: only return the measures for published datasets.
        """
        result: dict[str, dict[str, Any]] = {}
        for run in modeldb.Run.objects.filter(
            software__vm__vm_id=vm_id, input_dataset__dataset_id=dataset_id, deleted=False
        ):
            if only_public_results and modeldb.Review.objects.filter(run=run).exists():
                if not modeldb.Review.objects.get(run=run).published:
                    continue
            result[run.run_id] = {
                evaluation.measure_key: evaluation.measure_value for evaluation in run.evaluation_set.all()
            }
        return result

    def get_evaluations_with_keys_by_dataset(
        self,
        dataset_id: str,
        include_unpublished: bool = False,
        round_floats: bool = True,
        show_only_unreviewed: bool = False,
    ):
        """
        This function returns the data to render the Leaderboards: A list of keys 'ev-keys' of the evaluation measures
            which will be the column titles, and a list of evaluations. Each evaluations contains the vm and run id
            to identify it, and a key 'measures' which holds the scores in the same order as 'ev-keys'/


        @param include_unpublished: If True, also contains evaluations that were not marked as 'published'
        @param round_floats: If True, round float-valued scores to 3 digits.
        :returns: a tuple (ev_keys, evaluation),
            ev-keys is a list of keys of the evaluation measure
            evaluation is a list of evaluations, each evaluation is a dict with
                {vm_id: str, run_id: str, measures: list}
        """
        prepared_statement = """
        SELECT
            evaluation_run.input_dataset_id, evaluation_run.run_id, input_run.run_id, tira_upload.display_name,
            tira_upload.vm_id, tira_software.vm_id, tira_dockersoftware.display_name, tira_dockersoftware.vm_id,
            tira_evaluation_review.published, tira_evaluation_review.blinded, tira_run_review.published,
            tira_run_review.blinded, tira_evaluation.measure_key, tira_evaluation.measure_value,
            tira_run_review.reviewer_id, tira_run_review.no_errors, tira_run_review.has_errors,
            tira_run_review.has_no_errors, tira_evaluation_review.reviewer_id, tira_run_review.reviewer_id,
            tira_linktosoftwaresubmissiongitrepository.build_environment
        FROM
            tira_run as evaluation_run
        INNER JOIN
            tira_run as input_run ON evaluation_run.input_run_id = input_run.run_id
        LEFT JOIN
            tira_upload ON input_run.upload_id = tira_upload.id
        LEFT JOIN
            tira_software ON input_run.software_id = tira_software.id
        LEFT JOIN
            tira_dockersoftware ON input_run.docker_software_id = tira_dockersoftware.docker_software_id
        LEFT JOIN
            tira_linktosoftwaresubmissiongitrepository ON
                tira_dockersoftware.docker_software_id = tira_linktosoftwaresubmissiongitrepository.docker_software_id
        LEFT JOIN
            tira_review as tira_evaluation_review ON evaluation_run.run_id = tira_evaluation_review.run_id
        LEFT JOIN
            tira_review as tira_run_review ON input_run.run_id = tira_run_review.run_id
        LEFT JOIN
            tira_evaluation ON tira_evaluation.run_id = evaluation_run.run_id
        WHERE
            evaluation_run.input_run_id is not null AND evaluation_run.deleted = FALSE AND input_run.deleted = False
            AND evaluation_run.evaluator_id IS NOT NULL AND <DATASET_ID_STATEMENT>
        ORDER BY
            tira_evaluation.id ASC;
        """

        dataset_id_statement = []
        dataset_ids = [dataset_id]
        additional_datasets = modeldb.Dataset.objects.get(dataset_id=dataset_id).meta_dataset_of

        if additional_datasets:
            dataset_ids += [j.strip() for j in additional_datasets.split(",") if j.strip()]

        for _ in dataset_ids:
            dataset_id_statement += ["evaluation_run.input_dataset_id = %s"]
        dataset_id_statement_joined = " OR ".join(dataset_id_statement)
        prepared_statement = prepared_statement.replace("<DATASET_ID_STATEMENT>", f"({dataset_id_statement_joined})")

        rows = self.__execute_raw_sql_statement(prepared_statement, params=dataset_ids)
        return self.__parse_submissions(
            rows, include_unpublished, round_floats, show_only_unreviewed, show_only_unreviewed
        )

    @staticmethod
    def __link_to_code(build_environment_json: "Optional[str]") -> "Optional[str]":
        if not build_environment_json:
            return None

        try:
            build_environment = json.loads(json.loads(build_environment_json))
        except Exception:
            return None

        if (
            "GITHUB_REPOSITORY" not in build_environment
            or "GITHUB_WORKFLOW" not in build_environment
            or "GITHUB_SHA" not in build_environment
        ):
            return None

        if build_environment["GITHUB_WORKFLOW"] == "Upload Docker Software to TIRA":
            if "TIRA_DOCKER_PATH" not in build_environment:
                return None

            return f'https://github.com/{build_environment["GITHUB_REPOSITORY"]}/tree/{build_environment["GITHUB_SHA"]}/{build_environment["TIRA_DOCKER_PATH"]}'

        if (
            build_environment["GITHUB_WORKFLOW"] == ".github/workflows/upload-notebook-submission.yml"
            or build_environment["GITHUB_WORKFLOW"] == "Upload Notebook to TIRA"
        ):
            if "TIRA_JUPYTER_NOTEBOOK" not in build_environment:
                return None

            return f'https://github.com/{build_environment["GITHUB_REPOSITORY"]}/tree/{build_environment["GITHUB_SHA"]}/jupyter-notebook-submissions/{build_environment["TIRA_JUPYTER_NOTEBOOK"]}'

        return None

    def __parse_submissions(
        self,
        rows,
        include_unpublished: bool,
        round_floats: bool,
        include_without_evaluation: bool = False,
        show_only_unreviewed: bool = False,
    ) -> "tuple[list[str], list[dict[str, Any]]]":
        keys: dict[str, str] = dict()
        input_run_to_evaluation: dict[str, dict[str, Any]] = {}

        def round_if_float(fl: "Any") -> "Any":
            if not round_floats:
                return fl
            try:
                return round(float(fl), 3)
            except ValueError:
                return fl

        for (
            dataset_id,
            run_id,
            input_run_id,
            upload_display_name,
            upload_vm_id,
            software_vm_id,
            docker_display_name,
            docker_vm_id,
            eval_published,
            eval_blinded,
            run_published,
            run_blinded,
            m_key,
            m_value,
            reviewer_id,
            no_errors,
            has_errors,
            has_no_errors,
            tira_evaluation_reviewer_id,
            tira_run_reviewer_id,
            build_environment,
        ) in rows:

            if (not include_without_evaluation and not m_key) or (not include_unpublished and not eval_published):
                continue

            if show_only_unreviewed and tira_evaluation_reviewer_id != "tira" and tira_run_reviewer_id != "tira":
                continue

            if run_id not in input_run_to_evaluation:
                input_run_to_evaluation[run_id] = {"measures": {}}

            vm_id = "None"
            software_name = ""
            pretty_run_id = run_id if "-evaluated-run-" not in run_id else run_id.split("-evaluated-run-")[1]
            is_upload, is_software = False, False
            if upload_display_name and upload_vm_id:
                vm_id = upload_vm_id
                is_upload = True
                software_name = upload_display_name
            elif docker_display_name and docker_vm_id:
                vm_id = docker_vm_id
                is_software = True
                software_name = docker_display_name
            elif software_vm_id:
                vm_id = software_vm_id
                is_software = True

            review_state = "no-review"
            if reviewer_id and reviewer_id != "tira":
                review_state = "valid" if no_errors and has_no_errors and not has_errors else "invalid"

            input_run_to_evaluation[run_id]["dataset_id"] = dataset_id
            input_run_to_evaluation[run_id]["vm_id"] = vm_id
            input_run_to_evaluation[run_id]["input_software_name"] = software_name
            input_run_to_evaluation[run_id]["run_id"] = pretty_run_id
            input_run_to_evaluation[run_id]["input_run_id"] = input_run_id
            input_run_to_evaluation[run_id]["published"] = eval_published
            input_run_to_evaluation[run_id]["blinded"] = eval_blinded or run_blinded
            input_run_to_evaluation[run_id]["is_upload"] = is_upload
            input_run_to_evaluation[run_id]["is_software"] = is_software
            input_run_to_evaluation[run_id]["review_state"] = review_state
            input_run_to_evaluation[run_id]["link_code"] = self.__link_to_code(build_environment)

            if m_key:
                input_run_to_evaluation[run_id]["measures"][m_key] = m_value
                keys[m_key] = ""

        keylist = list(keys.keys())
        ret: list[dict[str, Any]] = []

        for i in input_run_to_evaluation.values():
            i["measures"] = [round_if_float(i["measures"].get(k, "-")) for k in keylist]
            ret += [i]

        return keylist, ret

    def __execute_raw_sql_statement(
        self, prepared_statement: str, params: "Optional[Union[Sequence[Any], Mapping[str, Any]]]"
    ):
        from django.db import connection

        ret = []
        with connection.cursor() as cursor:
            cursor.execute(prepared_statement, params=params)
            for i in cursor.fetchall():
                ret += [i]

        return ret

    def get_evaluation(self, run_id: str) -> dict[str, str]:
        try:
            evaluation = modeldb.Evaluation.objects.filter(run__run_id=run_id).all()
            return {ev.measure_key: ev.measure_value for ev in evaluation}

        except modeldb.Evaluation.DoesNotExist:
            logger.exception(f"Tried to load evaluation for run {run_id}, but it does not exist")

        return {}

    def get_software_with_runs(self, task_id: str, vm_id: str) -> "list[dict[str, Any]]":
        def _runs_by_software(software: modeldb.Software) -> "list[dict[str, Any]]":
            reviews = (
                modeldb.Review.objects.select_related(
                    "run", "run__software", "run__evaluator", "run__input_run", "run__input_dataset"
                )
                .filter(run__software=software)
                .all()
            )
            return list(self._get_ordered_runs_from_reviews(reviews, vm_id, preloaded=False))

        return [
            {"software": self._software_to_dict(s), "runs": _runs_by_software(s)}
            for s in modeldb.Software.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, deleted=False)
        ]

    @staticmethod
    def _review_as_dict(review: modeldb.Review) -> "dict[str, Any]":
        return {
            "reviewer": review.reviewer_id,
            "noErrors": review.no_errors,
            "missingOutput": review.missing_output,
            "extraneousOutput": review.extraneous_output,
            "invalidOutput": review.invalid_output,
            "hasErrorOutput": review.has_error_output,
            "otherErrors": review.other_errors,
            "comment": review.comment,
            "hasErrors": review.has_errors,
            "hasWarnings": review.has_warnings,
            "hasNoErrors": review.has_no_errors,
            "published": review.published,
            "blinded": review.blinded,
        }

    def get_run_review(self, dataset_id: "Optional[str]", vm_id: "Optional[str]", run_id: str) -> dict:
        review = modeldb.Review.objects.get(run__run_id=run_id)
        return self._review_as_dict(review)

    def get_vm_reviews_by_dataset(self, dataset_id: str, vm_id: str) -> dict:
        return {
            review.run.run_id: self._review_as_dict(review)
            for review in modeldb.Review.objects.select_related("run").filter(
                run__input_dataset__dataset_id=dataset_id, run__software__vm__vm_id=vm_id
            )
        }

    @staticmethod
    def _software_to_dict(software: "Message") -> "dict[str, Any]":
        return {
            "id": software.software_id,
            "count": software.count,
            "task_id": software.task.task_id,
            "vm_id": software.vm.vm_id,
            "command": software.command,
            "working_directory": software.working_directory,
            "dataset": None if not software.dataset else software.dataset.dataset_id,
            "run": "none",  # always none, this is a relict from a past version we keep for compatibility.
            "creation_date": software.creation_date,
            "last_edit": software.last_edit_date,
        }

    def get_software(self, task_id: str, vm_id: str, software_id: str) -> "dict[str, Any]":
        """Returns the software with the given name of a vm on a task"""
        return self._software_to_dict(
            modeldb.Software.objects.get(vm__vm_id=vm_id, task__task_id=task_id, software_id=software_id)
        )

    def get_software_by_task(self, task_id: str, vm_id: str) -> "list[dict[str, Any]]":
        return [
            self._software_to_dict(sw)
            for sw in modeldb.Software.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, deleted=False)
        ]

    def get_software_by_vm(self, task_id: str, vm_id: str) -> "list[dict[str, Any]]":
        """Returns the software of a vm on a task in json"""
        return [
            self._software_to_dict(software)
            for software in modeldb.Software.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, deleted=False)
        ]

    def add_vm(
        self, vm_id: str, user_name: str, initial_user_password: str, ip: str, host: str, ssh: str, rdp: str
    ) -> None:
        """Add a new task to the database.
        This will not overwrite existing files and instead do nothing and return false
        """
        if self._save_vm(vm_id, user_name, initial_user_password, ip, host, ssh, rdp):
            try:
                modeldb.VirtualMachine.objects.create(
                    vm_id=vm_id, user_password=initial_user_password, roles="user", host=host, ip=ip, ssh=ssh, rdp=rdp
                )
            except IntegrityError as e:
                logger.exception(f"Failed to add new vm {vm_id} with ", exc_info=e)
                raise TiraModelIntegrityError(e)
        else:
            raise TiraModelWriteError(f"Failed to write VM {vm_id}")

    def add_registration(self, data: dict[str, str]) -> None:
        task = modeldb.Task.objects.select_related("organizer").get(task_id=data["task_id"])

        if data["group"] not in task.allowed_task_teams and task.restrict_groups:
            raise ValueError(f'Team name is not allowed "{data["group"]}". Allowed: {task.allowed_task_teams}')

        if (
            data["group"]
            and data["group"].strip()
            and data["group"] not in task.allowed_task_teams
            and not task.restrict_groups
        ):
            allowed_task_teams = task.allowed_task_teams
            allowed_task_teams = "" if not allowed_task_teams else allowed_task_teams
            allowed_task_teams += "\n" + (data["group"].strip())
            task.allowed_task_teams = allowed_task_teams.strip()
            task.save()

        modeldb.Registration.objects.create(
            initial_owner=data["initial_owner"],
            team_name=data["group"],
            team_members=data["team"],
            registered_on_task=task,
            name=data["username"],
            email=data["email"],
            affiliation=data["affiliation"],
            country=data["country"],
            employment=data["employment"],
            participates_for=data["participation"],
            instructor_name=data["instructorName"],
            instructor_email=data["instructorEmail"],
            questions=data["questions"],
        )

    def all_registered_teams(self) -> set[str]:
        return set([i["team_name"] for i in modeldb.Registration.objects.values("team_name")])

    def _fdb_create_task(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        master_vm_id: str,
        organizer_id: str,
        website: str,
        help_command: "Optional[str]" = None,
        help_text: "Optional[str]" = None,
    ) -> None:
        new_task_file_path = self.tasks_dir_path / f"{task_id}.prototext"
        task = modelpb.Tasks.Task()
        task.taskId = task_id
        task.taskName = task_name
        task.taskDescription = task_description
        task.virtualMachineId = master_vm_id
        task.hostId = organizer_id
        task.web = website
        task.commandPlaceholder = help_command
        task.commandDescription = help_text
        new_task_file_path.write_text(str(task))

    def create_task(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        featured: bool,
        master_vm_id: str,
        organizer: str,
        website: str,
        require_registration: bool,
        require_groups: bool,
        restrict_groups: bool,
        help_command: "Optional[str]" = None,
        help_text: "Optional[str]" = None,
        allowed_task_teams: "Optional[str]" = None,
    ) -> "dict[str, Any]":
        """Add a new task to the database.
        CAUTION: This function does not do any sanity checks and will OVERWRITE existing tasks"""
        new_task = modeldb.Task.objects.create(
            task_id=task_id,
            task_name=task_name,
            vm=modeldb.VirtualMachine.objects.get(vm_id=master_vm_id),
            task_description=task_description,
            organizer=modeldb.Organizer.objects.get(organizer_id=organizer),
            web=website,
            featured=featured,
            require_registration=require_registration,
            require_groups=require_groups,
            restrict_groups=restrict_groups,
            allowed_task_teams=allowed_task_teams,
        )
        if help_command:
            new_task.command_placeholder = help_command
        if help_text:
            new_task.command_description = help_text
        new_task.save()

        self._fdb_create_task(
            task_id, task_name, task_description, master_vm_id, organizer, website, help_command, help_text
        )

        return self._task_to_dict(new_task)

    def _fdb_add_dataset_to_task(self, task_id: str, dataset_id: str, dataset_type: str) -> None:
        task_file_path = self.tasks_dir_path / f"{task_id}.prototext"
        task = Parse(task_file_path.read_bytes(), modelpb.Tasks.Task())
        if dataset_type == "test":
            task.testDataset.append(dataset_id)
        else:
            task.trainingDataset.append(dataset_id)
        task_file_path.write_text(str(task))

    def _fdb_add_dataset(
        self, task_id: str, dataset_id: str, display_name: str, dataset_type: str, evaluator_id: str
    ) -> None:
        """dataset_dir_path/task_id/dataset_id.prototext"""
        new_dataset_file_path = self.datasets_dir_path / task_id / f"{dataset_id}.prototext"

        ds = modelpb.Dataset()
        ds.datasetId = dataset_id
        ds.displayName = display_name
        ds.evaluatorId = evaluator_id
        if dataset_type == "test":
            ds.isConfidential = True
        else:
            ds.isConfidential = False

        (self.datasets_dir_path / task_id).mkdir(exist_ok=True, parents=True)
        new_dataset_file_path.write_text(str(ds))

    def get_new_dataset_id(self, dataset_id: str, task_id: str, dataset_type: str) -> str:
        candidates = [""] + [f"_{i}" for i in range(100)]
        for cand in candidates:
            dataset_id_candidate = f"{dataset_id}-{get_today_timestamp()}{cand}-{dataset_type}"
            if (
                self.dataset_exists(dataset_id_candidate)
                or (self.data_path / f"{dataset_type}-datasets" / task_id / dataset_id_candidate).exists()
                or (self.data_path / f"{dataset_type}-datasets-truth" / task_id / dataset_id_candidate).exists()
            ):
                continue

            return dataset_id_candidate

        raise ValueError("I could not find a dataset id.")

    def add_dataset(
        self,
        task_id: str,
        dataset_id: str,
        dataset_type: str,
        dataset_name: str,
        upload_name: str,
        irds_docker_image: "Optional[str]" = None,
        irds_import_command: "Optional[str]" = None,
        irds_import_truth_command: "Optional[str]" = None,
        dataset_format: "Optional[str]" = None,
        description: "Optional[str]" = None,
        chatnoir_id: "Optional[str]" = None,
        ir_datasets_id: "Optional[str]" = None,
        truth_format=None,
        format_configuration=None,
        truth_format_configuration=None,
    ) -> "tuple[dict[str, Any], list[str]]":
        """Add a new dataset to a task
        CAUTION: This function does not do any sanity (existence) checks and will OVERWRITE existing datasets"""
        dataset_id = self.get_new_dataset_id(dataset_id, task_id, dataset_type)

        if self.dataset_exists(dataset_id):
            raise FileExistsError(f"Dataset with id {dataset_id} already exists")

        for_task = modeldb.Task.objects.get(task_id=task_id)

        ds, _ = modeldb.Dataset.objects.update_or_create(
            dataset_id=dataset_id,
            defaults={
                "default_task": for_task,
                "display_name": dataset_name,
                "is_confidential": True if dataset_type == "test" else False,
                "released": str(dt.now()),
                "default_upload_name": upload_name,
                "irds_docker_image": irds_docker_image,
                "irds_import_command": irds_import_command,
                "irds_import_truth_command": irds_import_truth_command,
                "format": None if not dataset_format else json.dumps(dataset_format),
                "description": None if not description else description,
                "chatnoir_id": None if not chatnoir_id else chatnoir_id,
                "ir_datasets_id": None if not ir_datasets_id else ir_datasets_id,
                "truth_format": None if not truth_format else json.dumps(truth_format),
                "format_configuration": None if not format_configuration else json.dumps(format_configuration),
                "truth_format_configuration": (
                    None if not truth_format_configuration else json.dumps(truth_format_configuration)
                ),
            },
        )

        thds = modeldb.TaskHasDataset.objects.select_related("dataset").filter(task__task_id=task_id)

        if dataset_type == "test" and dataset_id not in {thd.dataset.dataset_id for thd in thds if thd.is_test}:
            modeldb.TaskHasDataset.objects.create(task=for_task, dataset=ds, is_test=True)
        elif dataset_type == "training" and dataset_id not in {
            thd.dataset.dataset_id for thd in thds if not thd.is_test
        }:
            modeldb.TaskHasDataset.objects.create(task=for_task, dataset=ds, is_test=False)
        elif dataset_type not in {"training", "dev", "test"}:
            raise KeyError("dataset type must be test, training, or dev")

        self._fdb_add_dataset_to_task(task_id, dataset_id, dataset_type)
        self._fdb_add_dataset(task_id, dataset_id, dataset_name, dataset_type, "not-set")

        # create dirs data_path/dataset/test-dataset[-truth]/task_id/dataset-id-type
        new_dirs = [
            (self.data_path / f"{dataset_type}-datasets" / task_id / dataset_id),
            (self.data_path / f"{dataset_type}-datasets-truth" / task_id / dataset_id),
        ]

        for d in new_dirs:
            d.mkdir(parents=True, exist_ok=True)

        return self._dataset_to_dict(ds), [str(nd) for nd in new_dirs]

    def _fdb_add_evaluator_to_vm(
        self, vm_id: "Optional[str]", evaluator_id: str, command: str, working_directory: "Path", measures: str
    ) -> None:
        """Add the evaluator the the <vm_id>.prototext file in the Filedatabase
        This file is potentially read by the host.
          If it is not read by the host anymore, remove this function and all it's calls
        """
        vm_file_path = self.vm_dir_path / f"{vm_id}.prototext"
        vm = Parse(open(vm_file_path).read(), modelpb.VirtualMachine())

        ev = modelpb.Evaluator()
        ev.evaluatorId = evaluator_id
        ev.command = command
        ev.workingDirectory = working_directory
        ev.measures = str(measures)  # ",".join([x[0].strip('\r') for x in measures])
        # ev.measureKeys.extend([x[1].strip('\r') for x in measures])
        vm.evaluators.append(ev)
        vm_file_path.write_text(str(vm))

    def _fdb_add_evaluator_to_dataset(self, task_id: str, dataset_id: str, evaluator_id: str) -> None:
        """Add the evaluator the the dataset.prototext file in the Filedatabase
        This file is potentially read by the host.
          If it is not read by the host anymore, remove this function and all it's calls
        """
        dataset_file_path = self.datasets_dir_path / task_id / f"{dataset_id}.prototext"
        ds = Parse(dataset_file_path.read_bytes(), modelpb.Dataset())
        ds.evaluatorId = evaluator_id
        dataset_file_path.write_text(str(ds))

    def add_evaluator(
        self,
        vm_id: "Optional[str]",
        task_id: str,
        dataset_id: str,
        command: str,
        working_directory: Path,
        measures: str,
        is_git_runner: bool,
        git_runner_image: "Optional[str]",
        git_runner_command: "Optional[str]",
        git_repository_id: "Optional[str]",
        trusted_evaluation,
    ) -> None:
        """Add a new Evaluator to the model (and the filedatabase as long as needed)

        @param vm_id: vm id as string as usual
        @param task_id: task_id as string as usual
        @param dataset_id: dataset_id as string as usual
        @param command: The command (including variables) that should be executed to run the evaluator
        @param working_directory: the directory in the master vm from where command should be executed
        @param measures: a string: the header columns of the measures, colon-separated
        @param is_git_runner: a bool. If true, run_evaluations are done via git CI (see git_runner.py)
        @param git_repository_id: the repo ID where the new run will be conducted
        @param git_runner_command: the command for the runner
        @param git_runner_image: which image should be run for the evalution
        """
        evaluator_id = f"{dataset_id}-evaluator"

        ev, _ = modeldb.Evaluator.objects.update_or_create(
            evaluator_id=evaluator_id,
            defaults={
                "command": command,
                "working_directory": working_directory,
                "measures": measures,
                "is_git_runner": is_git_runner,
                "git_runner_image": git_runner_image,
                "git_runner_command": git_runner_command,
                "git_repository_id": git_repository_id,
                "trusted_evaluation": trusted_evaluation,
            },
        )

        # add evaluator to master vm
        if vm_id and not is_git_runner:
            vm = modeldb.VirtualMachine.objects.get(vm_id=vm_id)
            vmhe, _ = modeldb.VirtualMachineHasEvaluator.objects.update_or_create(evaluator_id=evaluator_id, vm=vm)

        if not is_git_runner:
            self._fdb_add_evaluator_to_dataset(task_id, dataset_id, evaluator_id)
            self._fdb_add_evaluator_to_vm(vm_id, evaluator_id, command, working_directory, measures)

        modeldb.Dataset.objects.filter(dataset_id=dataset_id).update(evaluator=ev)

    def get_job_details(self, task_id: str, vm_id: str, job_id: str) -> "Optional[dict[str, Any]]":
        ret = modeldb.BackendProcess.objects.filter(id=job_id, vm__vm_id=vm_id, task__task_id=task_id)

        if ret is None or len(ret) == 0:
            return None
        else:
            ret = ret[0]
            return {
                "title": ret.title,
                "last_contact": ret.last_contact,
                "job_id": job_id,
                "exit_code": ret.exit_code,
                "stdout": ret.stdout,
            }

    def add_software(self, task_id: str, vm_id: str) -> "dict[str, Any]":
        software = modelpb.Softwares.Software()
        s = self._load_softwares(task_id, vm_id)
        date = now()

        new_software_id = randomname.get_name()
        software.id = new_software_id
        software.count = ""
        software.command = ""
        software.workingDirectory = ""
        software.dataset = ""
        software.run = ""
        software.creationDate = date
        software.lastEditDate = date
        software.deleted = False

        s.softwares.append(software)
        self._save_softwares(task_id, vm_id, s)
        sw = modeldb.Software.objects.create(
            software_id=new_software_id,
            vm=modeldb.VirtualMachine.objects.get(vm_id=vm_id),
            task=modeldb.Task.objects.get(task_id=task_id),
            count="",
            command="",
            working_directory="",
            dataset=None,
            creation_date=date,
            last_edit_date=date,
        )
        return self._software_to_dict(sw)

    def update_software(
        self,
        task_id,
        vm_id,
        software_id,
        command: "Optional[str]" = None,
        working_directory: "Optional[str]" = None,
        dataset: "Optional[str]" = None,
        run: "Optional[str]" = None,
        deleted: bool = False,
    ):
        def update(x: "_T", y: "Optional[_T]") -> "_T":
            return y if y is not None else x

        s = self._load_softwares(task_id, vm_id)
        date = now()
        for software in s.softwares:
            if software.id == software_id:
                software.command = update(software.command, command)
                software.workingDirectory = update(software.workingDirectory, working_directory)
                software.dataset = update(software.dataset, dataset)
                software.run = update(software.run, run)
                software.deleted = update(software.deleted, deleted)
                software.lastEditDate = date

                self._save_softwares(task_id, vm_id, s)
                modeldb.Software.objects.filter(software_id=software_id, vm__vm_id=vm_id).update(
                    command=software.command,
                    working_directory=software.workingDirectory,
                    deleted=software.deleted,
                    dataset=modeldb.Dataset.objects.get(dataset_id=software.dataset),
                    last_edit_date=date,
                )
                if run:
                    modeldb.SoftwareHasInputRun.objects.filter(
                        software=modeldb.Software.objects.get(software_id=software_id, vm__vm_id=vm_id),
                        input_run=modeldb.Run.objects.get(run_id=run),
                    )

                return software

        return False

    def update_review(
        self,
        dataset_id: str,
        vm_id: str,
        run_id: str,
        reviewer_id: "Optional[str]" = None,
        review_date: "Optional[str]" = None,
        has_errors: "Optional[bool]" = None,
        has_no_errors: "Optional[bool]" = None,
        no_errors: "Optional[bool]" = None,
        missing_output: "Optional[bool]" = None,
        extraneous_output: "Optional[bool]" = None,
        invalid_output: "Optional[bool]" = None,
        has_error_output: "Optional[bool]" = None,
        other_errors: "Optional[bool]" = None,
        comment: "Optional[str]" = None,
        published: "Optional[bool]" = None,
        blinded: "Optional[bool]" = None,
        has_warnings: bool = False,
    ) -> bool:
        """updates the review specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """

        def __update(x: "_T", y: "Optional[_T]") -> "_T":
            return y if y is not None else x

        try:
            # This changes the contents in the protobuf files
            review = modeldb.Review.objects.prefetch_related("run").get(run__run_id=run_id)

            review_proto = modelpb.RunReview(
                runId=run_id,
                reviewerId=__update(review.reviewer_id, reviewer_id),
                reviewDate=__update(review.review_date, review_date),
                hasErrors=__update(review.has_errors, has_errors),
                hasWarnings=__update(review.has_warnings, has_warnings),
                hasNoErrors=__update(review.has_no_errors, has_no_errors),
                noErrors=__update(review.no_errors, no_errors),
                missingOutput=__update(review.missing_output, missing_output),
                extraneousOutput=__update(review.extraneous_output, extraneous_output),
                invalidOutput=__update(review.invalid_output, invalid_output),
                hasErrorOutput=__update(review.has_error_output, has_error_output),
                otherErrors=__update(review.other_errors, other_errors),
                comment=__update(review.comment, comment),
                published=__update(review.published, published),
                blinded=__update(review.blinded, blinded),
            )

            modeldb.Review.objects.filter(run__run_id=run_id).update(
                reviewer_id=review_proto.reviewerId,
                review_date=review_proto.reviewDate,
                no_errors=review_proto.noErrors,
                missing_output=review_proto.missingOutput,
                extraneous_output=review_proto.extraneousOutput,
                invalid_output=review_proto.invalidOutput,
                has_error_output=review_proto.hasErrorOutput,
                other_errors=review_proto.otherErrors,
                comment=review_proto.comment,
                has_errors=review_proto.hasErrors,
                has_warnings=review_proto.hasWarnings,
                has_no_errors=review_proto.hasNoErrors,
                published=review_proto.published,
                blinded=review_proto.blinded,
            )

            self._save_review(dataset_id, vm_id, run_id, review_proto)
            return True

        except Exception as e:
            logger.exception(f"Exception while saving review ({dataset_id}, {vm_id}, {run_id}): {e}")
            return False

    def add_run(self, dataset_id: str, vm_id: str, run_id: str) -> str:
        """Parses the specified run and adds it to the model. Does nothing if the run does not exist in the
        FileDB.
        Runs the auto reviewer to generate an initial review.
        Also loads evaluations if present
        """
        return dbops.parse_run(self.runs_dir_path, dataset_id, vm_id, run_id)

    def _list_files(self, startpath: str) -> str:
        import os

        tree = ""
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, "").count(os.sep)
            indent = ".." * 2 * (level)
            tree += "{}|-- {}/\n".format(indent, os.path.basename(root))
            subindent = ".." * 2 * (level + 1)
            for f in files:
                tree += "{}|-- {}\n".format(subindent, f)
        return tree

    def _assess_uploaded_files(self, run_dir: Path, output_dir: Path):
        dirs = sum([1 if d.is_dir() else 0 for d in output_dir.glob("*")])
        files = sum([1 if not d.is_dir() else 0 for d in output_dir.rglob("*[!.zip]")])
        root_files = list(output_dir.glob("*[!.zip]"))

        def count_lines(file_name: Path) -> "Union[str, int]":
            try:
                if file_name.suffix == ".gz":
                    return len(gzip.open(file_name, "r").readlines())
                else:
                    return len(file_name.read_text().splitlines())
            except Exception:
                return "--"

        if root_files and not root_files[0].is_dir():
            lines = count_lines(root_files[0])
            size: Union[str, int] = root_files[0].stat().st_size
        else:
            lines = "--"
            size = "--"
        (run_dir / "size.txt").write_text(f"0\n{size}\n{lines}\n{files}\n{dirs}")
        (run_dir / "file-list.txt").write_text(self._list_files(str(output_dir)))

    def add_upload(self, task_id: str, vm_id: str, rename_to: "Optional[str]" = None):
        upload = modeldb.Upload.objects.create(
            vm=modeldb.VirtualMachine.objects.get(vm_id=vm_id),
            task=modeldb.Task.objects.get(task_id=task_id),
            rename_to=rename_to,
            display_name=randomname.get_name(),
            description="Please add a description that describes uploads of this type.",
        )

        return self.upload_to_dict(upload, vm_id)

    def delete_upload(self, task_id: str, vm_id: str, upload_id: str) -> None:
        modeldb.Upload.objects.filter(
            id=upload_id,
            vm__vm_id=vm_id,
            task__task_id=task_id,
        ).update(deleted=True)

    def add_uploaded_run(
        self, task_id: str, vm_id: str, dataset_id: str, upload_id: str, uploaded_file: "UploadedFile"
    ) -> "dict[str, Any]":
        # First add to data
        new_id = get_tira_id()
        run_dir = self.runs_dir_path / dataset_id / vm_id / new_id
        (run_dir / "output").mkdir(parents=True)

        # Second add to proto dump
        run = modelpb.Run()
        run.softwareId = "upload"
        run.runId = new_id
        run.inputDataset = dataset_id
        run.deleted = False
        run.downloadable = True
        run.taskId = task_id
        # Third add to database
        try:
            upload = modeldb.Upload.objects.get(vm__vm_id=vm_id, task__task_id=task_id, id=upload_id)
        except Exception:
            upload = modeldb.Upload.objects.get(vm__vm_id=vm_id, id=upload_id)

        upload.last_edit_date = now()
        upload.save()

        db_run = modeldb.Run.objects.create(
            run_id=new_id,
            upload=upload,
            input_dataset=modeldb.Dataset.objects.get(dataset_id=dataset_id),
            task=modeldb.Task.objects.get(task_id=task_id),
            downloadable=True,
        )

        (run_dir / "run.bin").write_bytes(run.SerializeToString())
        (run_dir / "run.prototext").write_text(str(run))

        if uploaded_file.name.endswith(".zip"):
            with open(run_dir / "output" / uploaded_file.name, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            with zipfile.ZipFile(run_dir / "output" / uploaded_file.name, "r") as zip_ref:
                zip_ref.extractall(run_dir / "output")

        else:
            default_filename = modeldb.Dataset.objects.get(dataset_id=dataset_id).default_upload_name
            if upload.rename_to and upload.rename_to.replace(" ", "").replace("\\", "").replace("/", "").strip():
                default_filename = upload.rename_to.replace(" ", "").replace("\\", "").replace("/", "").strip()

            if not (run_dir / "output" / default_filename).is_file():
                with open(run_dir / "output" / default_filename, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

        # Add size.txt and stdout and stderr, and file-list.txt
        self._assess_uploaded_files(run_dir, (run_dir / "output"))
        (run_dir / "stdout.txt").write_text("This run was successfully uploaded.")
        (run_dir / "stderr.txt").write_text("No errors.")

        # add the review
        review = auto_reviewer(run_dir, run_dir.stem)
        (run_dir / "run-review.prototext").write_text(str(review))
        (run_dir / "run-review.bin").write_bytes(review.SerializeToString())

        modeldb.Review.objects.update_or_create(
            run=db_run,
            defaults={
                "reviewer_id": review.reviewerId,
                "review_date": review.reviewDate,
                "no_errors": review.noErrors,
                "missing_output": review.missingOutput,
                "extraneous_output": review.extraneousOutput,
                "invalid_output": review.invalidOutput,
                "has_error_output": review.hasErrorOutput,
                "other_errors": review.otherErrors,
                "comment": review.comment,
                "has_errors": review.hasErrors,
                "has_warnings": review.hasWarnings,
                "has_no_errors": review.hasNoErrors,
                "published": review.published,
                "blinded": review.blinded,
            },
        )

        returned_run = self._run_as_dict(db_run)
        returned_run["review"] = self.get_run_review(dataset_id, vm_id, run.runId)

        return {"run": returned_run, "last_edit_date": upload.last_edit_date, "run_dir": run_dir}

    def update_upload_metadata(
        self, task_id: str, vm_id: str, upload_id: str, display_name: str, description: str, paper_link: str
    ) -> None:
        modeldb.Upload.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, id=upload_id).update(
            display_name=display_name,
            description=description,
            paper_link=paper_link,
        )

    def add_docker_software_mounts(self, docker_software: "dict[str, Any]", mounts):
        docker_software = modeldb.DockerSoftware.objects.get(docker_software_id=docker_software["docker_software_id"])
        modeldb.HuggingFaceModelsOfSoftware.objects.create(
            docker_software=docker_software,
            hf_home=mounts["HF_HOME"],
            mount_hf_model=mounts["MOUNT_HF_MODEL"],
            models_scan=mounts["HF_CACHE_SCAN"],
        )

    def add_docker_software(
        self,
        task_id: str,
        vm_id: str,
        user_image_name: str,
        command: str,
        tira_image_name: str,
        input_docker_job: "Optional[dict[int, str]]" = None,
        input_upload: "Optional[dict[int, str]]" = None,
        submission_git_repo: "Optional[str]" = None,
        build_environment: "Optional[str]" = None,
        source_code_remotes: "Optional[str]" = None,
        commit: "Optional[str]" = None,
        active_branch: "Optional[str]" = None,
        try_run_metadata_uuid: "Optional[str]" = None,
    ) -> "dict[str, Any]":
        input_docker_software: Optional[modeldb.DockerSoftware] = None
        input_upload_software: Optional[modeldb.Upload] = None
        try_run_metadata: Optional[modeldb.AnonymousUploads] = None
        if input_docker_job and 0 in input_docker_job:
            input_docker_software = modeldb.DockerSoftware.objects.get(docker_software_id=input_docker_job[0])
        if input_upload is not None and 0 in input_upload:
            input_upload_software = modeldb.Upload.objects.get(id=int(input_upload[0]))
        if try_run_metadata_uuid is not None:
            try_run_metadata = modeldb.AnonymousUploads.objects.get(uuid=try_run_metadata_uuid)

        docker_software = modeldb.DockerSoftware.objects.create(
            vm=modeldb.VirtualMachine.objects.get(vm_id=vm_id),
            task=modeldb.Task.objects.get(task_id=task_id),
            command=command,
            tira_image_name=tira_image_name,
            user_image_name=user_image_name,
            display_name=randomname.get_name(),
            input_docker_software=input_docker_software,
            input_upload=input_upload_software,
            source_code_remotes=source_code_remotes,
            source_code_commit=commit,
            source_code_active_branch=active_branch,
            try_run_metadata=try_run_metadata,
        )

        additional_inputs = range(
            1, (0 if not input_upload else len(input_upload)) + (0 if not input_docker_job else len(input_docker_job))
        )
        for i in additional_inputs:
            inp, upl = None, None
            if input_docker_job and i in input_docker_job:
                inp = modeldb.DockerSoftware.objects.get(docker_software_id=input_docker_job[i])
            else:
                assert input_upload is not None
                upl = modeldb.Upload.objects.get(id=int(input_upload[i]))

            modeldb.DockerSoftwareHasAdditionalInput.objects.create(
                docker_software=docker_software, input_docker_software=inp, input_upload=upl
            )

        if submission_git_repo:
            modeldb.LinkToSoftwareSubmissionGitRepository.objects.create(
                docker_software=docker_software,
                software_submission_git_repository=submission_git_repo,
                commit_hash="",
                link_to_file="",
                build_environment=build_environment,
            )

        return self._docker_software_to_dict(docker_software)

    def update_docker_software_metadata(
        self,
        docker_software_id: str,
        display_name: str,
        description: str,
        paper_link: str,
        ir_re_ranker: str,
        ir_re_ranking_input: str,
    ) -> None:
        modeldb.DockerSoftware.objects.update_or_create(
            docker_software_id=docker_software_id,
            defaults={
                "display_name": display_name,
                "description": description,
                "paper_link": paper_link,
                "ir_re_ranker": ir_re_ranker,
                "ir_re_ranking_input": ir_re_ranking_input,
            },
        )

    def update_run(self, dataset_id: str, vm_id: str, run_id: str, deleted: "Optional[bool]" = None) -> None:
        """updates the run specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """
        try:
            run = self._load_run(dataset_id, vm_id, run_id)

            def update(x: "_T", y: "Optional[_T]") -> "_T":
                return y if y is not None else x

            run.deleted = update(run.deleted, deleted)
            modeldb.Run.objects.filter(run_id=run_id).delete()

            self._save_run(dataset_id, vm_id, run_id, run)
        except Exception as e:
            raise TiraModelWriteError(f"Exception while saving run ({dataset_id}, {vm_id}, {run_id})") from e

    def _fdb_edit_task(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        master_vm_id: str,
        organizer_id: str,
        website: str,
        help_command: "Optional[str]" = None,
        help_text: "Optional[str]" = None,
    ) -> None:
        task_file_path = self.tasks_dir_path / f"{task_id}.prototext"
        if not task_file_path.exists():
            logger.exception(
                f"Can not save task {task_id} because the task file {task_file_path} does not exist. Creating this file"
                " now."
            )
            self._fdb_create_task(
                task_id, task_name, task_description, master_vm_id, organizer_id, website, help_command, help_text
            )
            return
        task = Parse(task_file_path.read_bytes(), modelpb.Tasks.Task())
        task.taskId = task_id
        task.taskName = task_name
        task.taskDescription = task_description
        task.virtualMachineId = master_vm_id
        task.hostId = organizer_id
        task.web = website
        task.commandPlaceholder = help_command
        task.commandDescription = help_text
        task_file_path.write_text(str(task))

    def edit_task(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        featured: bool,
        master_vm_id,
        organizer: str,
        website: str,
        require_registration: str,
        require_groups: str,
        restrict_groups: str,
        help_command: "Optional[str]" = None,
        help_text: "Optional[str]" = None,
        allowed_task_teams: "Optional[str]" = None,
        is_ir_task: bool = False,
        irds_re_ranking_image: str = "",
        irds_re_ranking_command: str = "",
        irds_re_ranking_resource: str = "",
    ):

        task = modeldb.Task.objects.filter(task_id=task_id)
        vm = modeldb.VirtualMachine.objects.get(vm_id=master_vm_id)
        task.update(
            task_name=task_name,
            task_description=task_description,
            vm=vm,
            organizer=modeldb.Organizer.objects.get(organizer_id=organizer),
            web=website,
            featured=featured,
            require_registration=require_registration,
            require_groups=require_groups,
            restrict_groups=restrict_groups,
            allowed_task_teams=allowed_task_teams,
            is_ir_task=is_ir_task,
            irds_re_ranking_image=irds_re_ranking_image,
            irds_re_ranking_command=irds_re_ranking_command,
            irds_re_ranking_resource=irds_re_ranking_resource,
        )

        if help_command:
            task.update(command_placeholder=help_command)
        if help_text:
            task.update(command_description=help_text)

        self._fdb_edit_task(
            task_id, task_name, task_description, master_vm_id, organizer, website, help_command, help_text
        )
        return self._task_to_dict(modeldb.Task.objects.get(task_id=task_id))

    def _fdb_edit_dataset(
        self, task_id: str, dataset_id: str, display_name: str, dataset_type: str, evaluator_id: str
    ) -> None:
        """dataset_dir_path/task_id/dataset_id.prototext"""
        dataset_file_path = self.datasets_dir_path / task_id / f"{dataset_id}.prototext"
        ds = Parse(dataset_file_path.read_bytes(), modelpb.Dataset())

        ds.displayName = display_name
        ds.evaluatorId = evaluator_id
        if dataset_type == "test":
            ds.isConfidential = True
        else:
            ds.isConfidential = False

        dataset_file_path.write_text(str(ds))

    def _fdb_edit_evaluator_to_vm(
        self, vm_id: str, evaluator_id: str, command: str, working_directory: str, measures: str
    ) -> None:
        """Edit the evaluator in the <vm_id>.prototext file in the Filedatabase
        This file is potentially read by the host.
          If it is not read by the host anymore, remove this function and all it's calls
        """
        vm_file_path = self.vm_dir_path / f"{vm_id}.prototext"
        vm = Parse(open(vm_file_path).read(), modelpb.VirtualMachine())

        for evaluator in vm.evaluators:
            if evaluator.evaluatorId == evaluator_id:
                evaluator.command = command
                evaluator.workingDirectory = working_directory
                evaluator.measures = measures

        vm_file_path.write_text(str(vm))

    def edit_dataset(
        self,
        task_id: str,
        dataset_id: str,
        dataset_name: str,
        command: str,
        working_directory: str,
        measures: str,
        upload_name: str,
        is_confidential: bool,
        is_git_runner: bool,
        git_runner_image: "Optional[str]",
        git_runner_command: "Optional[str]",
        git_repository_id: "Optional[str]",
        dataset_format: "Optional[str]",
        description: "Optional[str]",
        chatnoir_id: "Optional[str]" = None,
        ir_datasets_id: "Optional[str]" = None,
        truth_format=None,
        trusted_evaluation=None,
        dataset_format_configuration=None,
        truth_format_configuration=None,
    ) -> "dict[str, Any]":
        """

        @param is_git_runner: a bool. If true, run_evaluations are done via git CI (see git_runner.py)
        @param git_repository_id: the repo ID where the new run will be conducted
        @param git_runner_command: the command for the runner
        @param git_runner_image: which image should be run for the evalution

        """
        for_task = modeldb.Task.objects.get(task_id=task_id)
        modeldb.Dataset.objects.filter(dataset_id=dataset_id).update(
            default_task=for_task,
            display_name=dataset_name,
            default_upload_name=upload_name,
            is_confidential=is_confidential,
            format=None if not dataset_format else json.dumps(dataset_format),
            truth_format=None if not truth_format else json.dumps(truth_format),
            description=description,
            chatnoir_id=None if not chatnoir_id else chatnoir_id,
            ir_datasets_id=None if not ir_datasets_id else ir_datasets_id,
            format_configuration=None if not dataset_format_configuration else json.dumps(dataset_format_configuration),
            truth_format_configuration=(
                None if not truth_format_configuration else json.dumps(truth_format_configuration)
            ),
        )

        ds = modeldb.Dataset.objects.get(dataset_id=dataset_id)
        modeldb.TaskHasDataset.objects.filter(dataset=ds).update(task=for_task)
        dataset_type = "test" if is_confidential else "training"

        ev = modeldb.Evaluator.objects.filter(dataset__dataset_id=dataset_id)
        ev.update(
            command=command,
            working_directory=working_directory,
            measures=measures,
            is_git_runner=is_git_runner,
            git_runner_image=git_runner_image,
            git_runner_command=git_runner_command,
            git_repository_id=git_repository_id,
            trusted_evaluation=trusted_evaluation,
        )
        ev_id = modeldb.Evaluator.objects.get(dataset__dataset_id=dataset_id).evaluator_id

        self._fdb_edit_dataset(task_id, dataset_id, dataset_name, dataset_type, ev_id)

        try:
            vm_id = modeldb.VirtualMachineHasEvaluator.objects.filter(evaluator__evaluator_id=ev_id)[0].vm.vm_id
            self._fdb_edit_evaluator_to_vm(vm_id, ev_id, command, working_directory, measures)
        except Exception as e:
            logger.exception(
                f"failed to query 'VirtualMachineHasEvaluator' for evauator {ev_id}. Will not save changes made to the"
                " Filestore.",
                e,
            )

        return self._dataset_to_dict(ds)

    def delete_software(self, task_id: str, vm_id: str, software_id: str) -> bool:
        """Delete a software.
        Deletion is denied when
        - there is a successful evlauation assigned.
        """
        reviews_qs = modeldb.Review.objects.filter(
            run__input_run__software__software_id=software_id,
            run__input_run__software__task_id=task_id,
            run__input_run__software__vm_id=vm_id,
            no_errors=True,
        )
        if reviews_qs.exists():
            return False

        s = self._load_softwares(task_id, vm_id)
        found = False
        for software in s.softwares:
            if software.id == software_id:
                software.deleted = True
                found = True

        self._save_softwares(task_id, vm_id, s)
        modeldb.Software.objects.filter(software_id=software_id, vm__vm_id=vm_id).delete()

        return found

    def delete_run(self, dataset_id: str, vm_id: str, run_id: str) -> bool:
        """delete the run in the database.

        Do not delete if:
          - the run is on the leaderboard.
          - the run is valid

            @return: true if it was deleted, false if it can not be deleted
        """
        run = modeldb.Run.objects.get(run_id=run_id)

        review = modeldb.Review.objects.get(run=run)
        if review and (review.published or review.no_errors):
            return False

        modeldb.Run.objects.filter(input_run=run).delete()
        modeldb.Run.objects.filter(run_id=run_id).delete()
        return True

    def _fdb_delete_task(self, task_id: str) -> None:
        task_file_path = self.tasks_dir_path / f"{task_id}.prototext"
        os.remove(task_file_path)

    def delete_task(self, task_id: str) -> None:
        modeldb.Task.objects.filter(task_id=task_id).delete()
        self._fdb_delete_task(task_id)

    def _fdb_delete_dataset(self, task_id: str, dataset_id: str) -> None:
        dataset_file_path = self.datasets_dir_path / task_id / f"{dataset_id}.prototext"
        os.remove(dataset_file_path)

    def _fdb_delete_dataset_from_task(self, task_id: str, dataset_id: str) -> None:
        task_file_path = self.tasks_dir_path / f"{task_id}.prototext"
        task = Parse(task_file_path.read_bytes(), modelpb.Tasks.Task())
        for ind, ds in enumerate(task.testDataset):
            if ds == dataset_id:
                del task.testDataset[ind]

        for ind, ds in enumerate(task.trainingDataset):
            if ds == dataset_id:
                del task.trainingDataset[ind]

        task_file_path.write_text(str(task))

    def _fdb_delete_evaluator_from_vm(self, vm_id: str, evaluator_id: str) -> None:
        vm_file_path = self.vm_dir_path / f"{vm_id}.prototext"
        vm = Parse(open(vm_file_path).read(), modelpb.VirtualMachine())

        for ind, ev in enumerate(vm.evaluators):
            if ev.evaluatorId == evaluator_id:
                del vm.evaluators[ind]

        vm_file_path.write_text(str(vm))

    def delete_dataset(self, dataset_id: str) -> None:
        modeldb.Dataset.objects.filter(dataset_id=dataset_id).update(is_deprecated=True)
        # ds = modeldb.Dataset.objects.select_related('default_task', 'evaluator').get(dataset_id=dataset_id)
        # task_id = ds.default_task.task_id
        # vm_id = ds.default_task.vm.vm_id
        # try:
        #    evaluator_id = ds.evaluator.evaluator_id
        #    self._fdb_delete_evaluator_from_vm(vm_id, evaluator_id)
        # except AttributeError as e:
        #    logger.exception(f"Exception deleting evaluator while deleting dataset {dataset_id}. "
        #                     f"Maybe It never existed?", exc_info=e)
        # self._fdb_delete_dataset_from_task(task_id, dataset_id)
        # self._fdb_delete_dataset(task_id, dataset_id)
        # ds.delete()

    def edit_organizer(
        self, organizer_id: str, name: str, years: str, web: str, git_integrations: "list[dict[str, Any]]" = []
    ) -> modeldb.Organizer:
        org, _ = modeldb.Organizer.objects.update_or_create(
            organizer_id=organizer_id, defaults={"name": name, "years": years, "web": web}
        )
        org.git_integrations.set(git_integrations)

        return org

    def _git_integration_to_dict(self, git_integration: modeldb.GitIntegration) -> "dict[str, Any]":
        return {
            "namespace_url": git_integration.namespace_url,
            "host": git_integration.host,
            "private_token": git_integration.private_token,
            "user_name": git_integration.user_name,
            "user_password": git_integration.user_password,
            "gitlab_repository_namespace_id": git_integration.gitlab_repository_namespace_id,
            "image_registry_prefix": git_integration.image_registry_prefix,
            "user_repository_branch": git_integration.user_repository_branch,
        }

    def get_git_integration(
        self, namespace_url: str, private_token: str, return_dict: bool = False, create_if_not_exists: bool = True
    ) -> "Optional[dict[str, Any]]":
        if not namespace_url or not namespace_url.strip():
            return None

        defaults = {"private_token": private_token}

        if not private_token or not private_token.strip() or "<OMMITTED>".lower() in private_token.lower():
            defaults = {}

        if create_if_not_exists:
            git_integration, _ = modeldb.GitIntegration.objects.get_or_create(
                namespace_url=namespace_url, defaults=defaults
            )
        else:
            git_integration = modeldb.GitIntegration.objects.get(namespace_url=namespace_url)

        return self._git_integration_to_dict(git_integration) if return_dict else git_integration

    def all_git_integrations(self, return_dict: bool = False) -> "list[dict[str, Any]]":
        ret = modeldb.GitIntegration.objects.all()

        if return_dict:
            ret = [self._git_integration_to_dict(i) for i in ret]

        return ret

    def _registration_to_dict(self, registration: modeldb.Registration) -> "dict[str, Any]":
        return {
            "team_name": registration.team_name,
            "initial_owner": registration.initial_owner,
            "name": registration.name,
            "email": registration.email,
            "affiliation": registration.affiliation,
            "country": registration.country,
            "employment": registration.employment,
            "registered_on_task": registration.registered_on_task.task_id,
            "instructor_name": registration.instructor_name,
            "instructor_email": registration.instructor_email,
            "questions": registration.questions,
            "created": registration.created,
            "last_modified": registration.last_modified,
        }

    # methods to check for existence
    @staticmethod
    def task_exists(task_id: str) -> bool:
        return modeldb.Task.objects.filter(task_id=task_id).exists()

    @staticmethod
    def dataset_exists(dataset_id: str) -> bool:
        return modeldb.Dataset.objects.filter(dataset_id=dataset_id).exists()

    @staticmethod
    def vm_exists(vm_id: str) -> bool:
        return modeldb.VirtualMachine.objects.filter(vm_id=vm_id).exists()

    @staticmethod
    def organizer_exists(organizer_id: str) -> bool:
        return modeldb.Organizer.objects.filter(organizer_id=organizer_id).exists()

    @staticmethod
    def run_exists(vm_id: str, dataset_id: str, run_id: str) -> bool:
        return modeldb.Run.objects.filter(run_id=run_id).exists()

    @staticmethod
    def software_exists(task_id: str, vm_id: str, software_id: str) -> bool:
        return modeldb.Software.objects.filter(software_id=software_id, vm__vm_id=vm_id).exists()

    @staticmethod
    def all_matching_run_ids(
        vm_id: "Optional[str]",
        input_dataset_id: "Optional[str]",
        task_id: str,
        software_id: "Optional[str]",
        docker_software_id: "Optional[int]",
        upload_id: "Optional[int]",
    ) -> list[str]:
        ret: list[str] = []

        if software_id:
            ret += [
                i.run_id
                for i in modeldb.Run.objects.filter(
                    software__software_id=software_id, task__task_id=task_id, input_dataset__dataset_id=input_dataset_id
                )
            ]

        if docker_software_id:
            ret += [
                i.run_id
                for i in modeldb.Run.objects.filter(
                    docker_software__docker_software_id=docker_software_id, input_dataset__dataset_id=input_dataset_id
                )
            ]

        if not software_id and not docker_software_id and vm_id:
            ret += [
                i.run_id
                for i in modeldb.Run.objects.filter(
                    upload__vm__vm_id=vm_id,
                    input_dataset__dataset_id=input_dataset_id,
                )
            ]

        if upload_id:
            ret += [
                i.run_id
                for i in modeldb.Run.objects.filter(upload__id=upload_id, input_dataset__dataset_id=input_dataset_id)
            ]

        return [i for i in ret if i]

    def get_ordered_additional_input_runs_of_software(
        self, docker_software: "dict[str, Any]"
    ) -> "list[tuple[Optional[int], Optional[modeldb.Upload]]]":
        ret: list[tuple[Optional[int], Optional[modeldb.Upload]]] = []

        if not docker_software or "docker_software_id" not in docker_software:
            return []

        additional_inputs = modeldb.DockerSoftwareHasAdditionalInput.objects.filter(
            docker_software__docker_software_id=docker_software["docker_software_id"]
        ).order_by("position")

        for i in additional_inputs:
            ret += [
                (
                    i.input_docker_software.docker_software_id if i.input_docker_software else None,
                    i.input_upload.id if i.input_upload else None,
                )
            ]

        return ret

    def all_registrations(self, task_id: str) -> "list[dict[str, Any]]":
        task = modeldb.Task.objects.get(task_id=task_id)
        ret: list[dict[str, Any]] = []

        for i in modeldb.Registration.objects.filter(registered_on_task=task):
            ret += [self._registration_to_dict(i)]

        return ret


# modeldb.EvaluationLog.objects.filter(vm_id='nlptasks-master').delete()
# print(modeldb.Run.objects.all().exclude(upload=None).values())

# Note: To Reindex faulty runs
# dataset_ids = set([run.input_dataset_id for run in modeldb.Run.objects.filter(upload=None, software=None, docker_software=None, evaluator=None)])
# runs_dir = settings.TIRA_ROOT / Path("data/runs")
# for d in dataset_ids:
#     if not d:
#         print("d is None")
#         continue
#     for vm_dir in (runs_dir / d).glob("*"):
#         print(dbops.parse_runs_for_vm(runs_dir, d, vm_dir.stem, verbose=True))
