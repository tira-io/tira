import logging
import re
from datetime import datetime
from datetime import datetime as dt
from datetime import timezone
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, overload

from django.conf import settings
from google.protobuf.text_format import Parse

from ..proto import TiraClientWebMessages_pb2 as modelpb
from ..util import TiraModelWriteError, auto_reviewer, extract_year_from_dataset_id

if TYPE_CHECKING:
    from typing import _T, Any, Iterable, Optional, Union

    from google.protobuf.message import Message


logger = logging.getLogger("tira")


def _coalesce(*args: "Optional[_T]") -> "Optional[_T]":
    """
    Returns the first argument that is not None. Returns None if no such value exists.
    """
    for x in args:
        if x is not None:
            return x
    return None


class FileDatabase(object):
    """
    This is the class to interface a TIRA Filedatabase.
    All objects are loaded and stored as protobuf objects.
    All public methods return dicts.
    _parse methods are for loading and cashing (i.e. store in memory)
    _load methods are for loading and returning (non persistent)
    _get methods are for conversion from proto to dict
    _save is to store objects in the file structure
    add is the public IF to add to the model
    get is the public IF to get data from the model
    """

    tira_root: Path = settings.TIRA_ROOT
    tasks_dir_path = tira_root / Path("model/tasks")
    users_file_path = tira_root / Path("model/users/users.prototext")
    organizers_file_path = tira_root / Path("model/organizers/organizers.prototext")
    vm_list_file = tira_root / Path("model/virtual-machines/virtual-machines.txt")
    vm_dir_path = tira_root / Path("model/virtual-machines")
    host_list_file = tira_root / Path("model/virtual-machine-hosts/virtual-machine-hosts.txt")
    ova_dir = tira_root / Path("data/virtual-machine-templates/")
    datasets_dir_path = tira_root / Path("model/datasets")
    softwares_dir_path = tira_root / Path("model/softwares")
    data_path = tira_root / Path("data/datasets")
    RUNS_DIR_PATH = tira_root / Path("data/runs")

    def __init__(self) -> None:
        logger.info("Start loading dataset")
        self.organizers: Optional[dict[str, Message]] = None  # dict of host objects host_id: modelpb.Host
        self.vms: Optional[dict[str, Message]] = None  # dict of vm_id: modelpb.User
        self.tasks: Optional[dict[str, Message]] = None  # dict of task_id: modelpb.Tasks.Task
        self.datasets: Optional[dict[str, Message]] = None  # dict of dataset_id: modelpb.Dataset
        self.software: Optional[dict[str, Message]] = None  # dict of task_id$vm_id: modelpb.Software
        self.default_tasks: Optional[dict[str, str]] = None  # dataset_id: task_id
        self.task_organizers: Optional[dict[str, str]] = None  # dataset_id: modelpb.Hosts.Host.name
        self.software_by_task: Optional[dict[str, list[Message]]] = None  # task_id: [modelpb.Software]
        self.software_by_vm: Optional[dict[str, list[Message]]] = None  # vm_id: [modelpb.Software]
        self.software_count_by_dataset: Optional[dict[str, int]] = None  # dataset_id: int()
        self.evaluators: dict[str, Message] = {}  # dataset_id: [modelpb.Evaluator] used as cache
        self.updates = {
            "organizers": dt.now(),
            "vms": dt.now(),
            "tasks": dt.now(),
            "datasets": dt.now(),
            "software": dt.now(),
            "default_tasks": dt.now(),
            "software_by_vm": dt.now(),
            "software_count_by_dataset": dt.now(),
        }

        self.build_model()

    def build_model(self) -> None:
        print("build_model")
        self._parse_organizer_list()
        self._parse_vm_list()
        self._parse_task_list()
        self._parse_dataset_list()
        self._parse_software_list()

        self._build_task_relations()
        self._build_software_relations()
        self._build_software_counts()

    def reload_vms(self) -> None:
        """reload VM and user data from the export format of the model"""
        self._parse_vm_list()

    def reload_datasets(self) -> None:
        """reload dataset data from the export format of the model"""
        self._parse_dataset_list()

    def reload_tasks(self) -> None:
        """reload task data from the export format of the model"""
        self._parse_task_list()
        self._build_task_relations()
        self._build_software_relations()
        self._build_software_counts()

    def reload_runs(self, vm_id: str) -> None:
        """reload run data for a VM from the export format of the model"""
        raise NotImplementedError("Not Implemented: Runs are loaded on access when using FileDatabase")

    def _parse_organizer_list(self) -> None:
        """Parse the PB Database and extract all hosts.
        :return: a dict {hostId: {"name", "years"}
        """
        if (dt.now() - self.updates["organizers"]).seconds < 10 and self.organizers:
            return
        organizers = modelpb.Hosts()
        Parse(open(self.organizers_file_path, "r").read(), organizers)

        self.organizers = {org.hostId: org for org in organizers.hosts}

    def _parse_vm_list(self) -> None:
        if (dt.now() - self.updates["vms"]).seconds < 10 and self.vms:
            return
        print("parsing vms")
        users = modelpb.Users()
        Parse(open(self.users_file_path, "r").read(), users)
        self.vms = {user.userName: user for user in users.users}

    def _parse_task_list(self) -> None:
        """Parse the PB Database and extract all tasks.
        :return:
        1. a dict with the tasks {"taskId": {"name", "description", "dataset_count", "organizer", "year", "web"}}
        2. a dict with default tasks of datasets {"dataset_id": "task_id"}
        """
        if (dt.now() - self.updates["tasks"]).seconds < 10 and self.tasks:
            return
        print("parsing tasks")

        tasks = {}
        logger.info("loading tasks")
        for task_path in self.tasks_dir_path.glob("*"):
            task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
            tasks[task.taskId] = task

        self.tasks = tasks

    def _parse_dataset_list(self) -> None:
        """Load all the datasets from the Filedatabase.
        :return: a dict {dataset_id: dataset protobuf object}
        """
        if (dt.now() - self.updates["datasets"]).seconds < 10 and self.datasets:
            return
        print("parsing datasets")
        datasets: dict[str, Message] = {}
        logger.info("loading datasets")
        for dataset_file in self.datasets_dir_path.rglob("*.prototext"):
            dataset = Parse(dataset_file.read_bytes(), modelpb.Dataset())
            datasets[dataset.datasetId] = dataset

        self.datasets = datasets

    def _parse_software_list(self) -> None:
        """extract the software files. We invent a new id for the lookup since software has none:
          - <task_name>$<user_name>
        Afterwards sets self.software: a dict with the new key and a list of software objects as value
        """
        if (dt.now() - self.updates["software"]).seconds < 10 and self.software:
            return
        print("parsing software")
        software = {}
        logger.info("loading softwares")
        for task_dir in self.softwares_dir_path.glob("*"):
            for user_dir in task_dir.glob("*"):
                s = Parse(open(user_dir / "softwares.prototext", "r").read(), modelpb.Softwares())
                software_list = [user_software for user_software in s.softwares if not user_software.deleted]
                software[f"{task_dir.stem}${user_dir.stem}"] = software_list

        self.software = software

    # _build methods reconstruct the relations once per parse. This is a shortcut for frequent joins.
    def _build_task_relations(self) -> None:
        """parse the relation dicts self.default_tasks and self.task_organizers from self.tasks"""
        assert self.tasks is not None and self.organizers is not None
        default_tasks: dict[str, str] = {}
        task_organizers: dict[str, str] = {}
        for task_id, task in self.tasks.items():
            for td in task.trainingDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers.get(task.hostId, modelpb.Hosts.Host()).name
            for td in task.testDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers.get(task.hostId, modelpb.Hosts.Host()).name

        self.default_tasks = default_tasks
        self.task_organizers = task_organizers

    def _build_software_relations(self) -> None:
        assert self.software is not None
        software_by_task: dict[str, list] = {}
        software_by_vm: dict[str, list] = {}

        for software_id, software_list in self.software.items():
            task_id = software_id.split("$")[0]
            vm_id = software_id.split("$")[1]
            _swbd = software_by_task.get(task_id, list())
            _swbd.extend(software_list)
            software_by_task[task_id] = _swbd

            _swbu = software_by_vm.get(vm_id, list())
            _swbu.extend(software_list)
            software_by_vm[vm_id] = _swbu

        self.software_by_vm = software_by_vm
        self.software_by_task = software_by_task

    def _build_software_counts(self) -> None:
        assert self.software is not None
        counts: dict[str, int] = {}

        for software_list in self.software.values():
            for software in software_list:
                c = counts.get(software.dataset, 0)
                c += 1
                counts[software.dataset] = c

        self.software_count_by_dataset = counts

    # _load methods parse files on the fly when pages are called
    def load_review(self, dataset_id: str, vm_id: str, run_id: str):
        """This method loads a review or toggles auto reviewer if it does not exist."""

        review_path = self.RUNS_DIR_PATH / dataset_id / vm_id / run_id
        review_file = review_path / "run-review.bin"
        if not review_file.exists():
            review = auto_reviewer(review_path, run_id)
            self._save_review(dataset_id, vm_id, run_id, review)
            return review

        review = modelpb.RunReview()
        review.ParseFromString(review_file.read_bytes())
        return review

    def _load_vm(self, vm_id: str):
        """load a vm object from vm_dir_path"""
        return Parse((self.vm_dir_path / f"{vm_id}.prototext").read_bytes(), modelpb.VirtualMachine())

    def _load_softwares(self, task_id: str, vm_id: str):
        softwares_dir = self.softwares_dir_path / task_id / vm_id
        softwares_dir.mkdir(parents=True, exist_ok=True)
        software_file = softwares_dir / "softwares.prototext"
        if not software_file.exists():
            software_file.touch()

        return Parse(software_file.read_bytes(), modelpb.Softwares())

    def _load_run(self, dataset_id: str, vm_id: str, run_id: str, return_deleted: bool = False):
        run_dir = self.RUNS_DIR_PATH / dataset_id / vm_id / run_id
        if not (run_dir / "run.bin").exists():
            if (run_dir / "run.prototext").exists():
                r: "Message" = Parse((run_dir / "run.prototext").read_bytes(), modelpb.Run())
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

    def _load_vm_evaluations(self, dataset_id: str, vm_id: str, only_published: bool) -> dict[str, Message]:
        """load all evaluations for a user on a given dataset
        :param dataset_id: id/name of the dataset
        :param vm_id: id/name of the user
        :return: {run_id: modelpb.Evaluation}
        """
        evaluations = {}
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*"):
            if not (run_id_dir / "output/evaluation.bin").exists():
                continue
            if only_published is True and self.load_review(dataset_id, vm_id, run_id_dir.stem).published is False:
                continue

            evaluation = modelpb.Evaluation()
            evaluation.ParseFromString(open(run_id_dir / "output/evaluation.bin", "rb").read())

            evaluations[run_id_dir.stem] = evaluation

        return evaluations

    def get_evaluation_measures(self, evaluation) -> "dict[str, Any]":
        return {measure.key: measure.value for measure in evaluation.measure}

    # ---------------------------------------------------------------------
    # ---- save methods to update protos
    # ---------------------------------------------------------------------

    def _save_task(self, task_proto: "Message", overwrite: bool = False) -> None:
        """makes persistant changes to task: store in memory and to file.
        Returns false if task exists and overwrite is false."""
        assert self.tasks is not None
        # open(f'/home/tira/{task_id}.prototext', 'wb').write(new_task.SerializeToString())
        new_task_file_path = self.tasks_dir_path / f"{task_proto.taskId}.prototext"
        if not overwrite and new_task_file_path.exists():
            raise TiraModelWriteError("Failed to write vm, vm exists and overwrite is not allowed here")
        self.tasks[task_proto.taskId] = task_proto
        new_task_file_path.write_text(str(task_proto))
        self._build_task_relations()

    def _save_vm(self, vm_proto: "Message", overwrite: bool = False) -> None:
        new_vm_file_path = self.vm_dir_path / f"{vm_proto.virtualMachineId}.prototext"
        if not overwrite and new_vm_file_path.exists():
            raise TiraModelWriteError("Failed to write vm, vm exists and overwrite is not allowed here")
        # self.vms[vm_proto.virtualMachineId] = vm_proto  # TODO see issue:30
        new_vm_file_path.write_text(str(vm_proto))

    def _save_dataset(self, dataset_proto: "Message", task_id: str, overwrite: bool = False) -> None:
        """dataset_dir_path/task_id/dataset_id.prototext"""
        assert self.datasets is not None
        new_dataset_file_path = self.datasets_dir_path / task_id / f"{dataset_proto.datasetId}.prototext"
        if not overwrite and new_dataset_file_path.exists():
            raise TiraModelWriteError("Failed to write dataset, dataset exists and overwrite is not allowed here")
        (self.datasets_dir_path / task_id).mkdir(exist_ok=True, parents=True)
        new_dataset_file_path.write_text(str(dataset_proto))
        self.datasets[dataset_proto.datasetId] = dataset_proto

    def _save_review(self, dataset_id: str, vm_id: str, run_id: str, review: "Message") -> None:
        review_path: Path = self.RUNS_DIR_PATH / dataset_id / vm_id / run_id
        (review_path / "run-review.prototext").write_text(str(review))
        (review_path / "run-review.bin").write_text(review.SerializeToString())

    def _save_softwares(self, task_id: str, vm_id: str, softwares) -> None:
        with open(self.softwares_dir_path / task_id / vm_id / "softwares.prototext", "w+") as prototext_file:
            # update file
            prototext_file.write(str(softwares))

    def _save_run(self, dataset_id: str, vm_id: str, run_id: str, run: "Message") -> None:
        run_dir: Path = self.RUNS_DIR_PATH / dataset_id / vm_id / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        (run_dir / "run.prototext").write_text(str(run))
        (run_dir / "run.bin").write_text(run.SerializeToString())

    # ------------------------------------------------------------
    # add methods to add new data to the model
    # ------------------------------------------------------------

    def add_vm(
        self, vm_id: str, user_name: str, initial_user_password: str, ip: str, host: str, ssh: str, rdp: str
    ) -> None:
        """Add a new task to the database.
        This will not overwrite existing files and instead do nothing and return false
        """
        new_vm = modelpb.VirtualMachine()
        new_vm.virtualMachineId = vm_id
        new_vm.vmId = vm_id
        new_vm.vmName = vm_id
        new_vm.host = host
        new_vm.adminName = "admin"  # Note these are required but deprecated
        new_vm.adminPw = "admin"  # Note these are required but deprecated
        new_vm.userName = user_name
        new_vm.userPw = initial_user_password
        new_vm.ip = ip
        new_vm.portSsh = ssh
        new_vm.portRdp = rdp
        self._save_vm(new_vm)

    def create_task(
        self, task_id: str, task_name: str, task_description: str, master_vm_id: str, organizer: str, website: str
    ) -> None:
        """Add a new task to the database.
        CAUTION: This function does not do any sanity checks and will OVERWRITE existing tasks"""
        new_task = modelpb.Tasks.Task()
        new_task.taskId = task_id
        new_task.taskName = task_name
        new_task.taskDescription = task_description
        new_task.virtualMachineId = master_vm_id
        new_task.hostId = organizer
        new_task.web = website
        self._save_task(new_task)

    def add_dataset(self, task_id: str, dataset_id: str, dataset_type: str, dataset_name: str) -> list[str]:
        """TODO documentation"""
        assert self.tasks is not None

        # update task_dir_path/task_id.prototext:
        dataset_id = f"{dataset_id}-{dataset_type}"
        for_task = self.tasks.get(task_id, None)
        if for_task is None:
            raise KeyError(f"No task with id {task_id}")

        if dataset_type == "test" and dataset_id not in for_task.testDataset:
            for_task.testDataset.append(dataset_id)
        elif dataset_type in {"training", "dev"} and dataset_id not in for_task.trainingDataset:
            for_task.trainingDataset.append(dataset_id)
        elif dataset_type not in {"training", "dev", "test"}:
            raise KeyError("dataset type must be test, training, or dev")
        self._save_task(for_task, overwrite=True)

        # create new dataset_dir_path/task_id/dataset_id.prototext
        ds = modelpb.Dataset()
        ds.datasetId = dataset_id
        ds.displayName = dataset_name
        ds.isDeprecated = False
        ds.isConfidential = True if dataset_type == "test" else False
        self._save_dataset(ds, task_id)

        # create dirs data_path/dataset/test-dataset[-truth]/task_id/dataset-id-type
        new_dirs: list[Path] = []
        if dataset_type == "test":
            new_dirs.append((self.data_path / "test-datasets" / task_id / dataset_id))
            new_dirs.append((self.data_path / "test-datasets-truth" / task_id / dataset_id))
        else:
            new_dirs.append((self.data_path / "training-datasets" / task_id / dataset_id))
            new_dirs.append((self.data_path / "training-datasets-truth" / task_id / dataset_id))
        for d in new_dirs:
            d.mkdir(parents=True, exist_ok=True)

        return [str(nd) for nd in new_dirs]

    def _add_software(self, task_id: str, vm_id: str) -> None:
        # TODO crashes if software prototext does not exist.
        assert self.software is not None
        software = modelpb.Softwares.Software()
        s = self._load_softwares(task_id, vm_id)
        try:
            last_software_count = re.search(r"\d+$", s.softwares[-1].id)
            software_count = int(last_software_count.group()) + 1 if last_software_count else None
            if software_count is None:
                # invalid software id value
                return

            software.id = f"software{software_count}"
            software.count = str(software_count)

        except IndexError:
            # no software present yet
            software.id = "software1"
            software.count = "1"

        software.command = ""
        software.workingDirectory = ""
        software.dataset = "None"
        software.run = ""
        software.creationDate = datetime.now(timezone.utc).strftime("%a %b %d %X %Z %Y")
        software.lastEditDate = software.creationDate
        software.deleted = False

        s.softwares.append(software)
        self._save_softwares(task_id, vm_id, s)

        software_list = self.software.get(f"{task_id}${vm_id}", [])
        software_list.append(software)
        self.software[f"{task_id}${vm_id}"] = software_list

    def add_evaluator(
        self,
        vm_id: str,
        task_id: str,
        dataset_id: str,
        dataset_type: str,
        command: str,
        working_directory: str,
        measures: str,
    ) -> None:
        """TODO documentation"""
        assert self.datasets is not None
        evaluator_id = f"{dataset_id}-evaluator"
        dataset_id = f"{dataset_id}-{dataset_type}"

        # update dataset_id.prototext
        dataset = self.datasets.get(dataset_id)
        assert dataset is not None
        dataset.evaluatorId = evaluator_id
        self._save_dataset(dataset, task_id, overwrite=True)

        # add evaluators to vm
        vm = self._load_vm(vm_id)
        if evaluator_id not in {ev.evaluatorId for ev in vm.evaluators}:
            ev = modelpb.Evaluator()
            ev.evaluatorId = evaluator_id
            ev.command = command
            ev.workingDirectory = working_directory
            ev.measures = ",".join([x[0].strip("\r") for x in measures])
            ev.measureKeys.extend([x[1].strip("\r") for x in measures])
            vm.evaluators.append(ev)
            self._save_vm(vm, overwrite=True)

    def _update_review(
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
        has_warnings: "Optional[bool]" = False,
    ) -> None:
        """updates the review specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """
        review = self.load_review(dataset_id, vm_id, run_id)

        review.reviewerId = _coalesce(reviewer_id, review.reviewerId)
        review.reviewDate = _coalesce(review_date, review.reviewDate)
        review.hasErrors = _coalesce(has_errors, review.hasErrors)
        review.hasWarnings = _coalesce(has_warnings, review.hasWarnings)
        review.hasNoErrors = _coalesce(has_no_errors, review.hasNoErrors)
        review.noErrors = _coalesce(no_errors, review.noErrors)
        review.missingOutput = _coalesce(missing_output, review.missingOutput)
        review.extraneousOutput = _coalesce(extraneous_output, review.extraneousOutput)
        review.invalidOutput = _coalesce(invalid_output, review.invalidOutput)
        review.hasErrorOutput = _coalesce(has_error_output, review.hasErrorOutput)
        review.otherErrors = _coalesce(other_errors, review.otherErrors)
        review.comment = _coalesce(comment, review.comment)
        review.published = _coalesce(published, review.published)
        review.blinded = _coalesce(blinded, review.blinded)

        self._save_review(dataset_id, vm_id, run_id, review)

    def _update_run(self, dataset_id: str, vm_id: str, run_id: str, deleted: "Optional[bool]" = None) -> None:
        """updates the run specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """
        run = self._load_run(dataset_id, vm_id, run_id)

        def update(x: _T, y: "Optional[_T]") -> "_T":
            return y if y is not None else x

        run.deleted = update(run.deleted, deleted)
        self._save_run(dataset_id, vm_id, run_id, run)

    def update_software(
        self,
        task_id: str,
        vm_id: str,
        software_id: str,
        command: "Optional[str]" = None,
        working_directory: "Optional[str]" = None,
        dataset: "Optional[str]" = None,
        run: "Optional[str]" = None,
        deleted: bool = False,
    ):
        assert self.software is not None

        def update(x: "_T", y: "Optional[_T]") -> "_T":
            return y if y is not None else x

        s = self._load_softwares(task_id, vm_id)
        for software in s.softwares:
            if software.id == software_id:
                software.command = update(software.command, command)
                software.workingDirectory = update(software.workingDirectory, working_directory)
                software.dataset = update(software.dataset, dataset)
                software.run = update(software.run, run)
                software.deleted = update(software.deleted, deleted)
                software.lastEditDate = datetime.now(timezone.utc).strftime("%a %b %d %X %Z %Y")

                self._save_softwares(task_id, vm_id, s)
                software_list = [user_software for user_software in s.softwares if not user_software.deleted]
                self.software[f"{task_id}${vm_id}"] = software_list
                return software

    # TODO add option to truly delete the software.
    def delete_software(self, task_id: str, vm_id: str, software_id: str) -> None:
        assert self.software is not None

        s = self._load_softwares(task_id, vm_id)

        for software in s.softwares:
            if software.id == software_id:
                break
        else:
            raise TiraModelWriteError(f"Software does not exist: {task_id}, {vm_id}, {software_id}")
        software_list = [software for software in s.softwares if not software.deleted]
        self.software[f"{task_id}${vm_id}"] = software_list
        self._save_softwares(task_id, vm_id, s)

    def delete_run(self, dataset_id: str, vm_id: str, run_id: str) -> None:
        run_dir = Path(self.RUNS_DIR_PATH / dataset_id / vm_id / run_id)
        rmtree(run_dir)

    #########################################
    # get methods are the public interface.
    ###################################

    def get_vm(self, vm_id: str, create_if_none: bool = False) -> "Message":
        # TODO should return as dict
        assert self.vms is not None
        return self.vms.get(vm_id, None)

    def get_tasks(self) -> "list[dict[str, Any]]":
        assert self.tasks is not None
        return [self.get_task(task.taskId) for task in self.tasks.values()]

    def get_run(self, dataset_id: str, vm_id: str, run_id: str, return_deleted: bool = False) -> "dict[str, Any]":
        run = self._load_run(dataset_id, vm_id, run_id, return_deleted)
        return {
            "software": run.softwareId,
            "run_id": run.runId,
            "input_run_id": run.inputRun,
            "dataset": run.inputDataset,
            "downloadable": run.downloadable,
        }

    def get_task(self, task_id: str) -> "dict[str, Any]":
        assert self.tasks is not None and self.software_by_task is not None and self.organizers is not None
        t = self.tasks[task_id]

        return {
            "task_name": t.taskName,
            "description": t.taskDescription,
            "commandPlaceholder": (
                ""
                if t.commandPlaceholder == "mySoftware -c $inputDataset -r $inputRun -o $outputDir"
                else t.commandPlaceholder
            ),
            "commandDescription": (
                ""
                if t.commandDescription
                == "Available variables: <code>$inputDataset</code>, <code>$inputRun</code>, <code>$outputDir</code>,"
                " <code>$dataServer</code>, and <code>$token</code>."
                else t.commandDescription
            ),
            "task_id": t.taskId,
            "dataset_count": len(t.trainingDataset) + len(t.testDataset),
            "software_count": len(self.software_by_task.get(t.taskId, {0})),
            "web": t.web,
            "organizer": self.organizers.get(t.hostId, modelpb.Hosts.Host()).name,
            "year": self.organizers.get(t.hostId, modelpb.Hosts.Host()).years,
        }

    def get_dataset(self, dataset_id: str) -> "dict[str, Any]":
        assert (
            self.datasets is not None
            and self.default_tasks is not None
            and self.task_organizers is not None
            and self.software_count_by_dataset is not None
        )
        dataset = self.datasets[dataset_id]
        return {
            "display_name": dataset.displayName,
            "evaluator_id": dataset.evaluatorId,
            "dataset_id": dataset.datasetId,
            "is_confidential": dataset.isConfidential,
            "is_deprecated": dataset.isDeprecated,
            "year": extract_year_from_dataset_id(dataset_id),
            "task": self.default_tasks.get(dataset.datasetId, "None"),
            "organizer": self.task_organizers.get(dataset.datasetId, ""),
            "software_count": self.software_count_by_dataset.get(dataset.datasetId, 0),
        }

    def get_datasets(self) -> "dict[str, dict[str, Any]]":
        """Get a dict of dataset_id: dataset_json_descriptor"""
        assert self.datasets is not None
        return {dataset_id: self.get_dataset(dataset_id) for dataset_id in self.datasets}

    def get_datasets_by_task(self, task_id: str, include_deprecated=False) -> "list[dict[str, Any]]":
        """return the list of datasets associated with this task_id
        @param task_id: id string of the task the dataset belongs to
        @param include_deprecated: Default False. If True, also returns datasets marked as deprecated.
        @return: a list of json-formatted datasets, as returned by get_dataset
        """
        assert self.datasets is not None and self.default_tasks is not None
        return [
            self.get_dataset(dataset.datasetId)
            for dataset in self.datasets.values()
            if task_id == self.default_tasks.get(dataset.datasetId, "")
            and not (dataset.isDeprecated and not include_deprecated)
        ]

    def get_organizer(self, organizer_id: str) -> "Message":
        # TODO should return as dict
        assert self.organizers is not None
        return self.organizers[organizer_id]

    def get_host_list(self) -> list[str]:
        return self.host_list_file.read_text().splitlines()

    def get_ova_list(self) -> list[str]:
        return [f"{ova_file.stem}.ova" for ova_file in self.ova_dir.glob("*.ova")]

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

        return list(parse_vm_list(self.vm_list_file.read_text().splitlines()))

    def get_vms_by_dataset(self, dataset_id: str) -> list[str]:
        """return a list of vm_id's that have runs on this dataset"""
        return [user_run_dir.stem for user_run_dir in (self.RUNS_DIR_PATH / dataset_id).glob("*")]

    def get_vm_runs_by_dataset(self, dataset_id: str, vm_id: str, return_deleted: bool = False) -> list[dict]:
        runs = {}
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*"):
            run_id = run_id_dir.stem
            run = self.get_run(dataset_id, vm_id, run_id, return_deleted=return_deleted)

            if run is not None:
                runs[run_id] = run

        return list(runs.values())

    def get_vm_runs_by_task(self, task_id: str, vm_id: str, return_deleted: bool = False) -> list:
        """returns a list of all the runs of a user over all datasets in json (as returned by _load_user_runs)"""
        relevant_datasets = {software["dataset"] for software in self.get_software(task_id, vm_id)}
        runs = []
        for dataset_id in relevant_datasets:
            runs.extend(self.get_vm_runs_by_dataset(dataset_id, vm_id, return_deleted=return_deleted))
        return runs

    def get_vms_with_reviews(self, dataset_id: str) -> "list[dict[str, Any]]":
        vm_ids = self.get_vms_by_dataset(dataset_id)
        # This enforces an order to the measures, since they differ between datasets and are rendered dynamically
        vm_reviews = {vm_id: self.get_vm_reviews_by_dataset(dataset_id, vm_id) for vm_id in vm_ids}
        vm_runs = {vm_id: self.get_vm_runs_by_dataset(dataset_id, vm_id) for vm_id in vm_ids}

        vms = []
        for vm_id, run in vm_runs.items():
            runs = [
                {"run": run, "review": vm_reviews.get(vm_id, {}).get(run["run_id"], [])}
                for run in vm_runs.get(vm_id, [])
            ]
            unreviewed_count = len(
                [
                    1
                    for r in vm_reviews[vm_id].values()
                    if not r.get("hasErrors", None) and not r.get("hasNoErrors", None)
                ]
            )
            published_count = len([1 for r in vm_reviews[vm_id].values() if r.get("published", None)])
            blinded_count = len([1 for r in vm_reviews[vm_id].values() if r.get("blinded", None)])
            vms.append(
                {
                    "vm_id": vm_id,
                    "runs": runs,
                    "unreviewed_count": unreviewed_count,
                    "blinded_count": blinded_count,
                    "published_count": published_count,
                }
            )
        return vms

    def get_evaluations_with_keys_by_dataset(
        self, dataset_id: str, include_unpublished: str
    ) -> tuple[list[str], list[dict[str, Any]]]:
        vm_ids = self.get_vms_by_dataset(dataset_id)
        vm_evaluations = {
            vm_id: self.get_vm_evaluations_by_dataset(dataset_id, vm_id, only_public_results=not include_unpublished)
            for vm_id in vm_ids
        }
        keys: set[str] = set()
        for e1 in vm_evaluations.values():
            for e2 in e1.values():
                keys.update(e2.keys())
        ev_keys = list(keys)
        if include_unpublished:
            vm_reviews = {vm_id: self.get_vm_reviews_by_dataset(dataset_id, vm_id) for vm_id in vm_ids}
            evaluations = [
                {
                    "vm_id": vm_id,
                    "run_id": run_id,
                    "blinded": vm_reviews.get(vm_id, {}).get(run_id, {}).get("blinded", False),
                    "published": vm_reviews.get(vm_id, {}).get(run_id, {}).get("published", False),
                    "measures": [measures.get(k, "-") for k in ev_keys],
                }
                for vm_id, measures_by_runs in vm_evaluations.items()
                for run_id, measures in measures_by_runs.items()
            ]
        else:
            evaluations = [
                {"vm_id": vm_id, "run_id": run_id, "measures": [measures.get(k, "-") for k in ev_keys]}
                for vm_id, measures_by_runs in vm_evaluations.items()
                for run_id, measures in measures_by_runs.items()
            ]
        return ev_keys, evaluations

    def get_evaluator(self, dataset_id, task_id=None):
        """returns a dict containing the evaluator parameters:

        vm_id: id of the master vm running the evaluator
        host: ip or hostname of the host
        command: command to execute to run the evaluator. NOTE: contains variables the host needs to resolve
        working_dir: where to execute the command
        """
        dataset = self.datasets[dataset_id]
        evaluator_id = dataset.evaluatorId
        if task_id is None:
            task_id = self.default_tasks.get(dataset.datasetId, None)

        task = self.tasks.get(task_id)
        vm_id = task.virtualMachineId
        master_vm = Parse(open(self.vm_dir_path / f"{vm_id}.prototext", "r").read(), modelpb.VirtualMachine())
        result = {"vm_id": vm_id, "host": master_vm.host}

        for evaluator in master_vm.evaluators:
            if evaluator.evaluatorId == evaluator_id:
                result["command"] = evaluator.command
                result["working_dir"] = evaluator.workingDirectory
                break

        return result

    def get_vm_evaluations_by_dataset(
        self, dataset_id: str, vm_id: str, only_public_results: bool = True
    ) -> "dict[str, dict[str, Any]]":
        """Return a dict of run_id: evaluation_results for the given vm on the given dataset
        @param only_public_results: only return the measures for published datasets.
        """
        return {
            run_id: self.get_evaluation_measures(ev)
            for run_id, ev in self._load_vm_evaluations(dataset_id, vm_id, only_published=only_public_results).items()
        }

    def get_run_review(self, dataset_id: str, vm_id: str, run_id: str) -> "dict[str, Any]":
        review = self.load_review(dataset_id, vm_id, run_id)

        return {
            "reviewer": review.reviewerId,
            "noErrors": review.noErrors,
            "missingOutput": review.missingOutput,
            "extraneousOutput": review.extraneousOutput,
            "invalidOutput": review.invalidOutput,
            "hasErrorOutput": review.hasErrorOutput,
            "otherErrors": review.otherErrors,
            "comment": review.comment,
            "hasErrors": review.hasErrors,
            "hasWarnings": review.hasWarnings,
            "hasNoErrors": review.hasNoErrors,
            "published": review.published,
            "blinded": review.blinded,
        }

    def get_vm_reviews_by_dataset(self, dataset_id: str, vm_id: str) -> dict:
        return {
            run_id_dir.stem: self.get_run_review(dataset_id, vm_id, run_id_dir.stem)
            for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*")
        }

    @overload
    def get_software(self, task_id: str, vm_id: str, software_id: None = None) -> "list[dict[str, Any]]": ...

    @overload
    def get_software(self, task_id: str, vm_id: str, software_id: str) -> "Optional[dict[str, Any]]": ...

    def get_software(
        self, task_id: str, vm_id: str, software_id: "Optional[str]" = None
    ) -> "Union[list[dict[str, Any]], Optional[dict[str, Any]]]":
        """Returns the software with the given name of a vm on a task"""
        assert self.software is not None
        sw = [
            {
                "id": software.id,
                "count": software.count,
                "task_id": task_id,
                "vm_id": vm_id,
                "command": software.command,
                "working_directory": software.workingDirectory,
                "dataset": software.dataset,
                "run": software.run,
                "creation_date": software.creationDate,
                "last_edit": software.lastEditDate,
            }
            for software in self.software.get(f"{task_id}${vm_id}", [])
        ]

        if software_id is None:
            return sw

        for s in sw:
            if s["id"] == software_id:
                return s
        return None

    def get_software_by_vm(self, task_id, vm_id):
        """Returns the softwares of a vm on a task"""
        return [
            {
                "id": software.id,
                "count": software.count,
                "task_id": task_id,
                "vm_id": vm_id,
                "command": software.command,
                "working_directory": software.workingDirectory,
                "dataset": software.dataset,
                "run": software.run,
                "creation_date": software.creationDate,
                "last_edit": software.lastEditDate,
            }
            for software in self.software.get(f"{task_id}${vm_id}", [])
        ]

    def get_software_with_runs(self, task_id, vm_id):
        softwares = self.get_software_by_vm(task_id, vm_id)
        runs = self.get_vm_runs_by_task(task_id, vm_id)

        runs_with_input = {}  # get the runs which have an input_run_id
        for r in runs:
            # if we loop once, might as well get the review-info here.
            r["review"] = self.get_run_review(r.get("dataset"), vm_id, r.get("run_id"))
            if r.get("input_run_id") == "none":
                continue
            runs_with_input.setdefault(r.get("input_run_id"), []).append(r)

        runs_without_input = [r for r in runs if r.get("input_run_id") == "none"]
        runs_by_software = {}
        for r in runs_without_input:
            runs_by_software.setdefault(r.get("software"), []).append(r)
            runs_by_software.setdefault(r.get("software"), []).extend(runs_with_input.pop(r.get("run_id"), []))

        for k, v in runs_with_input.items():  # left-over runs_with_input, where the input-run does not exist anymore
            for r in v:
                runs_by_software.setdefault(r.get("software"), []).append(r)

        return [{"software": sw, "runs": runs_by_software.get(sw["id"])} for sw in softwares]

    # ------------------------------------------------------------
    # add methods to add new data to the model
    # ------------------------------------------------------------

    def add_software(self, task_id: str, vm_id: str):
        try:
            self._add_software(task_id, vm_id)
        except FileNotFoundError as e:
            logger.exception(f"Exception while adding software ({task_id}, {vm_id}): {e}")
            raise TiraModelWriteError(f"Failed to write VM {vm_id}")

    def update_review(
        self,
        dataset_id,
        vm_id,
        run_id,
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
        try:
            self._update_review(
                dataset_id,
                vm_id,
                run_id,
                reviewer_id,
                review_date,
                has_errors,
                has_no_errors,
                no_errors,
                missing_output,
                extraneous_output,
                invalid_output,
                has_error_output,
                other_errors,
                comment,
                published,
                blinded,
                has_warnings,
            )
            return True
        except Exception as e:
            logger.exception(f"Exception while saving review ({dataset_id}, {vm_id}, {run_id}): {e}")
            return False

    def add_run(self, *args, **kwargs):
        """The FileDatabase loads runs and reviews from the Protobuf files every time,
        so this method currently does nothing."""
        pass

    def update_run(self, dataset_id, vm_id, run_id, deleted: "Optional[bool]" = None):
        """updates the run specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """
        try:
            self._update_run(dataset_id, vm_id, run_id, deleted)
            return True
        except Exception as e:
            logger.exception(f"Exception while saving run ({dataset_id}, {vm_id}, {run_id}): {e}")
            return False

    # ------------------------------------------------------------
    # add methods to check for existence
    # ------------------------------------------------------------

    def task_exists(self, task_id: str) -> bool:
        assert self.tasks is not None
        return task_id in self.tasks

    def dataset_exists(self, dataset_id: str) -> bool:
        assert self.datasets is not None
        return dataset_id in self.datasets

    def vm_exists(self, vm_id: str) -> bool:
        assert self.vms is not None
        return vm_id in self.vms

    def organizer_exists(self, organizer_id: str) -> bool:
        assert self.organizers is not None
        return organizer_id in self.organizers

    def run_exists(self, vm_id: str, dataset_id: str, run_id: str) -> bool:
        return True if self.get_run(dataset_id, vm_id, run_id) else False

    def software_exists(self, task_id: str, vm_id: str, software_id: str) -> bool:
        assert self.software is not None
        for software in self.software.get(f"{task_id}${vm_id}", []):
            if software_id == software.id:
                return True
        return False
