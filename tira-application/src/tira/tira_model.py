"""
p.stat().st_mtime - change time
"""
import TiraClientWebMessages_pb2 as modelpb
from google.protobuf.text_format import Parse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileDatabase(object):
    MODEL_ROOT = Path("/mnt/ceph/tira/model")
    TASKS_DIR_PATH = MODEL_ROOT / Path("tasks")
    ORGANIZERS_FILE_PATH = MODEL_ROOT / Path("organizers/organizers.prototext")
    DATASETS_DIR_PATH = MODEL_ROOT / Path("datasets")
    SOFTWARES_DIR_PATH = MODEL_ROOT / Path("softwares")

    def __init__(self):
        logger.info("Start loading dataset")
        self.organizers = self._parse_organizer_list()
        self.softwares_count = self._parse_softwares_list()
        self.tasks, self.default_tasks, self.task_organizers = self._parse_task_list()
        self.datasets = self._parse_dataset_list()

    def _parse_organizer_list(self):
        """ Parse the PB Database and extract all hosts.
        :return: a dict {hostId: {"name", "years"}
        """
        organizers = modelpb.Hosts()
        Parse(open(self.ORGANIZERS_FILE_PATH, "r").read(), organizers)
        return {org.hostId: {"name": org.name, "years": org.years} for org in organizers.hosts}

    def _parse_task_list(self):
        """ Parse the PB Database and extract all tasks.
        :return:
        1. a dict with the tasks {"taskId": {"name", "description", "dataset_count", "organizer", "year", "web"}}
        2. a dict with default tasks of datasets {"dataset_id": "task_id"}
        """
        tasks = {}
        default_tasks = {}
        task_organizers = {}

        for task_path in self.TASKS_DIR_PATH.glob("*"):
            task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
            tasks[task.taskId] = {"name": task.taskName, "description": task.taskDescription,
                                  "dataset_count": len(task.trainingDataset) + len(task.testDataset),
                                  "web": task.web, "organizer": self.organizers[task.hostId]["name"],
                                  "year": self.organizers[task.hostId]["years"]
                                  }
            for td in task.trainingDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers[task.hostId]["name"]
            for td in task.testDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers[task.hostId]["name"]

        return tasks, default_tasks, task_organizers

    def _parse_dataset_list(self):
        """ Load all the datasets from the Filedatabase. Combines with information parsed from tasks
        :return: a dict {dataset_id: {name, "evaluator_id", "is_confidential", "is_deprecated",
                    "year", "task", 'organizer'}}
        """

        def extract_year_from_dataset_id(dataset_id):
            try:
                splits = dataset_id.split("-")
                return splits[-3] if len(splits) > 3 and (1990 <= int(splits[-3])) else ""
            except Exception:
                return ""

        datasets = {}
        for dataset_file in self.DATASETS_DIR_PATH.rglob("*.prototext"):
            dataset = Parse(open(dataset_file, "r").read(), modelpb.Dataset())
            datasets[dataset.datasetId] = {
                "name": dataset.datasetId, "evaluator_id": dataset.evaluatorId,
                "is_confidential": dataset.isConfidential, "is_deprecated": dataset.isDeprecated,
                "year": extract_year_from_dataset_id(dataset.datasetId),
                "task": self.default_tasks.get(dataset.datasetId, ""),
                'organizer': self.task_organizers.get(dataset.datasetId, ""),
                "softwares": self.softwares_count.get(dataset.datasetId, 0)
            }

        return datasets

    def _parse_softwares_list(self):
        """ extract the number of users and softwares for each dataset """
        softwares = {}
        for software_file in self.SOFTWARES_DIR_PATH.rglob("*.prototext"):
            s = Parse(open(software_file, "r").read(), modelpb.Softwares())
            for software in s.softwares:
                if not software.deleted:
                    softwares[software.dataset] = softwares.setdefault(software.dataset, 0) + 1
        return softwares
