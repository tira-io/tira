#!/usr/bin/env python

from datetime import datetime
from google.protobuf.text_format import Parse, MessageToString
from pathlib import Path
import logging
from proto import TiraClientWebMessages_pb2 as modelpb
from proto import tira_host_pb2 as model_host
import time
import socket

logger = logging.getLogger(__name__)
# TODO: get TIRA_ROOT from settings
TIRA_ROOT = "/mnt/nfs/tira/"


class FileDatabase(object):
    tira_root = TIRA_ROOT
    users_file_path = tira_root / Path("model/users/users.prototext")

    def __init__(self):
        logger.info("Start loading dataset")
        self.hostname = socket.gethostname()
        self.command_states_path = self.tira_root / Path("state/commands/" + self.hostname + ".prototext")
        self.command_logs_path = self.tira_root / Path("log/virtual-machine-hosts/" + self.hostname + "/")
        self.command_logs_path.mkdir(exist_ok=True)

        self.vms = None  # dict of vm_id: modelpb.User
        self.commandState = None

        self._create_command_state_file()

        self._parse_vm_list()
        self._parse_command_state()

    def _parse_command_state(self):
        """
        Parse the command state file.
        """
        self.commandState = Parse(open(self.command_states_path, "r").read(), model_host.CommandState())

    def _update_command_state_file(self):
        with open(self.command_states_path, "w") as f:
            f.write(MessageToString(self.commandState))

    def _create_command_state_file(self):
        """
        Create state file for the current host. Check and rename if the file already exists.
        """
        if self.command_states_path.is_file() and self.command_states_path.stat().st_size > 0:
            self.command_states_path.rename(
                self.command_states_path.with_suffix(
                    "." + datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%SZ") + ".prototext"))
        self.command_states_path.touch()

    def create_command(self, request, command_id, command_string):
        """
        Add new Command to the state file and create command log file.
        :return: Command object
        """
        new_command = self.commandState.commands.add()
        new_command.id = command_id
        new_command.commandString = command_string
        new_command.startTime = datetime.strftime(datetime.utcnow(), "%Y-%m-%dT%H:%M:%SZ")
        new_command.status = model_host.Response.Status.RUNNING
        if request.bulkCommandId:
            new_command.bulkCommandId = request.bulkCommandId

        # command_name = new_command.startTime + "_" + command_string.strip()[0]
        log_file_path = self.command_logs_path / Path(command_id + ".log")
        log_file_path.touch()
        new_command.logFile = str(log_file_path)

        self._update_command_state_file()

        return new_command

    def update_command(self, command_id, **kwargs):
        """
        Update command object with passed key-value pairs
        :param command_id:
        :param kwargs:
        """
        for c in self.commandState.commands:
            if c.id == command_id:
                for key, value in kwargs.items():
                    setattr(c, key, value)
        self._update_command_state_file()

    # def update_command_log(self, command_id, output):

    def remove_commands(self, commands_to_remove):
        """
        Remove finished commands
        """
        for c in self.commandState.commands:
            if c.id in commands_to_remove:
                self.commandState.commands.remove(c)

        self._update_command_state_file()

    def clean_command_state(self, time_ago):
        """
        Update command state file and remove commands older then 'time_ago'.
        :param time_ago:
        """
        for command in self.commandState.commands:
            if command.endTime and time.mktime(
                    datetime.strptime(command.endTime, "%Y-%m-%dT%H:%M:%SZ").timetuple()) < time_ago:
                self.commandState.commands.remove(command)
        self._update_command_state_file()

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

    def get_software(self, task_id, vm_id):
        """ Returns the software of a vm on a task in json """
        return [{"id": software.id, "count": software.count,
                 "task_id": task_id, "vm_id": vm_id,
                 "command": software.command, "working_directory": software.workingDirectory,
                 "dataset": software.dataset, "run": software.run, "creation_date": software.creationDate,
                 "last_edit": software.lastEditDate}
                for software in self.software[f"{task_id}${vm_id}"]]

    def get_vm_by_id(self, vm_id: str):
        print(vm_id)
        return self.vms.get(vm_id)
