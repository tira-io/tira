#!/usr/bin/env python

from configparser import ConfigParser
from datetime import datetime
from google.protobuf.text_format import Parse, MessageToString
from pathlib import Path
import logging
from proto import TiraClientWebMessages_pb2 as modelpb
from proto import tira_host_pb2 as model_host
import uuid
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

config = ConfigParser()
config.read('conf/grpc_service.ini')
TIRA_ROOT = config.get('main', 'tira_model_path')

logger = logging.getLogger(__name__)


class FileDatabase(FileSystemEventHandler):
    tira_root = TIRA_ROOT
    datasets_dir_path = tira_root / Path("model/datasets")
    softwares_dir_path = tira_root / Path("model/softwares")
    tasks_dir_path = tira_root / Path("model/tasks")
    users_file_path = tira_root / Path("model/users/users.prototext")
    vm_dir_path = tira_root / Path("model/virtual-machines")
    RUNS_DIR_PATH = tira_root / Path("data/runs")
    SUBMISSIONS_PATH = tira_root / Path("state/softwares")

    def __init__(self):
        logger.info("Start loading dataset")

        self.grpc_service = None
        self.datasets = None  # dict of dataset_id: modelpb.Dataset
        self.software = None  # dict of task_id$vm_id: modelpb.Software
        self.software_by_vm = None  # vm_id: [modelpb.Software]
        self.tasks = None  # dict of task_id: modelpb.Tasks.Task
        self.vms = None  # dict of vm_id: modelpb.User

        observer = PollingObserver()
        observer.schedule(self, path=str(self.users_file_path), recursive=False)
        observer.start()

        self.build_model()

    def build_model(self):
        self._parse_dataset_list()
        self._parse_software_list()
        self._parse_task_list()
        self._parse_vm_list()

    def on_modified(self, event):
        logger.info(f"Reload {self.users_file_path}...")
        self._parse_vm_list()

    def _parse_vm_list(self):
        users = modelpb.Users()
        Parse(open(self.users_file_path, "r").read(), users)
        self.vms = {user.userName: user for user in users.users}

    def _parse_dataset_list(self):
        """ Load all the datasets from the Filedatabase.
        :return: a dict {dataset_id: dataset protobuf object}
        """
        datasets = {}
        for dataset_file in self.datasets_dir_path.rglob("*.prototext"):
            dataset = Parse(open(dataset_file, "r").read(), modelpb.Dataset())
            datasets[dataset.datasetId] = dataset

        self.datasets = datasets

    def _parse_software_list(self):
        """ extract the software files. We invent a new id for the lookup since software has none:
          - <task_name>$<user_name>
        Afterwards sets self.software: a dict with the new key and a list of software objects as value
        """
        software = {}

        for task_dir in self.softwares_dir_path.glob("*"):
            for user_dir in task_dir.glob("*"):
                s = Parse(open(user_dir / "softwares.prototext", "r").read(), modelpb.Softwares())
                software_list = [user_software for user_software in s.softwares if not user_software.deleted]
                software[f"{task_dir.stem}${user_dir.stem}"] = software_list

        self.software = software

    def _parse_task_list(self):
        """ Parse the PB Database and extract all tasks.
        :return:
        1. a dict with the tasks {"taskId": {"name", "description", "dataset_count", "organizer", "year", "web"}}
        2. a dict with default tasks of datasets {"dataset_id": "task_id"}
        """
        tasks = {}
        logger.info('loading tasks')
        for task_path in self.tasks_dir_path.glob("*"):
            task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
            tasks[task.taskId] = task

        self.tasks = tasks

    def _load_run(self, dataset_id, vm_id, run_id, return_deleted=False, as_json=False):
        run_dir = self.get_run_dir(dataset_id, vm_id, run_id)
        if not (run_dir / "run.bin").exists():
            logger.error(f"Try to read a run without a run.bin: {dataset_id}-{vm_id}-{run_id}")
            # TODO check if it is better to return empty runs vs. returning None vs. raising
            return None

        run = modelpb.Run()
        run.ParseFromString(open(run_dir / "run.bin", "rb").read())
        if return_deleted is False and run.deleted:
            run.softwareId = "This run was deleted"
            run.runId = run_id
            run.inputDataset = dataset_id

        if as_json:
            return {"software": run.softwareId,
                    "run_id": run.runId, "input_run_id": run.inputRun,
                    "dataset": run.inputDataset, "downloadable": run.downloadable}
        return run

    def _load_softwares(self, task_id, vm_id):
        softwares_dir = self.softwares_dir_path / task_id / vm_id
        softwares_dir.mkdir(parents=True, exist_ok=True)
        software_file = softwares_dir / "softwares.prototext"
        if not software_file.exists():
            software_file.touch()

        return Parse(open(self.softwares_dir_path / task_id / vm_id / "softwares.prototext", "r").read(),
                     modelpb.Softwares())

    def get_run_dir(self, dataset_id, vm_id, run_id):
        return self.RUNS_DIR_PATH / dataset_id / vm_id / run_id

    def get_submissions_dir(self, vm_id):
        submissions_dir = self.SUBMISSIONS_PATH / vm_id
        submissions_dir.mkdir(parents=True, exist_ok=True)
        return submissions_dir

    def _save_run(self, dataset_id, vm_id, run_id, run):
        run_dir = self.get_run_dir(dataset_id, vm_id, run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        open(run_dir / "run.prototext", 'w').write(str(run))
        open(run_dir / "run.bin", 'wb').write(run.SerializeToString())

    def create_run(self, vm_id, software_id, run_id, dataset_id, input_run_id, task_id):
        """
        :param vm_id:
        :param software_id:
        :param run_id:
        :param dataset_id:
        :param input_run_id:
        :param task_id:
        :return:
        """
        run = modelpb.Run()
        run.softwareId = software_id
        run.runId = run_id
        run.inputDataset = dataset_id
        run.inputRun = input_run_id if input_run_id else "none"
        run.downloadable = False
        run.deleted = False
        run.taskId = task_id
        run.accessToken = str(uuid.uuid4())

        self._save_run(dataset_id, vm_id, run_id, run)

    def update_run(self, dataset_id, vm_id, run_id, deleted: bool = None):
        """ updates the run specified by dataset_id, vm_id, and run_id with the values given in the parameters.
            Required Parameters are also required in the function
        """
        run = self._load_run(dataset_id, vm_id, run_id, as_json=False)

        def update(x, y):
            return y if y is not None else x

        run.deleted = update(run.deleted, deleted)

        try:
            self._save_run(dataset_id, vm_id, run_id, run)
            return True
        except Exception as e:
            logger.exception(f"Exception while saving run ({dataset_id}, {vm_id}, {run_id}): {e}")
            return False

    def get_dataset(self, dataset_id: str) -> dict:

        def extract_year_from_dataset_id():
            try:
                splits = dataset_id.split("-")
                return splits[-3] if len(splits) > 3 and (1990 <= int(splits[-3])) else ""
            except Exception:
                return ""

        dataset = self.datasets[dataset_id]
        return {
            "display_name": dataset.displayName, "evaluator_id": dataset.evaluatorId,
            "dataset_id": dataset.datasetId,
            "is_confidential": dataset.isConfidential, "is_deprecated": dataset.isDeprecated,
            "year": extract_year_from_dataset_id(),
            "task": self.default_tasks.get(dataset.datasetId, ""),
            'organizer': self.task_organizers.get(dataset.datasetId, ""),
            "software_count": self.software_count_by_dataset.get(dataset.datasetId, 0)
        }

    def get_datasets(self) -> dict:
        """ Get a dict of dataset_id: dataset_json_descriptor """
        return {dataset_id: self.get_dataset(dataset_id) for dataset_id in self.datasets.keys()}

    def get_datasets_by_task(self, task_id: str, include_deprecated=False) -> list:
        """ return the list of datasets associated with this task_id
        @param task_id: id string of the task the dataset belongs to
        @param include_deprecated: Default False. If True, also returns datasets marked as deprecated.
        @return: a list of json-formatted datasets, as returned by get_dataset
        """
        return [self.get_dataset(dataset.datasetId)
                for dataset in self.datasets.values()
                if task_id == self.default_tasks.get(dataset.datasetId, "") and
                not (dataset.isDeprecated and not include_deprecated)]

    def get_software(self, task_id, vm_id, software_id=None):
        """ Returns the software of a vm on a task in json """
        sw = [{"id": software.id, "count": software.count,
               "task_id": task_id, "vm_id": vm_id,
               "command": software.command, "working_directory": software.workingDirectory,
               "dataset": software.dataset, "run": software.run, "creation_date": software.creationDate,
               "last_edit": software.lastEditDate}
              for software in self.software.get(f"{task_id}${vm_id}", [])]

        if not software_id:
            return sw

        for s in sw:
            if s["id"] == software_id:
                return s

    def get_vm_by_id(self, vm_id: str):
        return self.vms.get(vm_id, None)
