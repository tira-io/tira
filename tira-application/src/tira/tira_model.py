"""
p.stat().st_mtime - change time
"""
from google.protobuf.text_format import Parse
from pathlib import Path
import logging
from django.conf import settings
from .proto import TiraClientWebMessages_pb2 as modelpb

logger = logging.getLogger(__name__)


class FileDatabase(object):
    tira_root = settings.TIRA_ROOT
    tasks_dir_path = tira_root / Path("model/tasks")
    users_file_path = tira_root / Path("model/users/users.prototext")
    organizers_file_path = tira_root / Path("model/organizers/organizers.prototext")
    datasets_dir_path = tira_root / Path("model/datasets")
    softwares_dir_path = tira_root / Path("model/softwares")
    RUNS_DIR_PATH = tira_root / Path("data/runs")

    def __init__(self):
        logger.info("Start loading dataset")
        self.organizers = self._parse_organizer_list()
        self.users = self._parse_users_list()

        self.softwares_by_task, self.softwares_by_user = self._parse_softwares_list()
        self.softwares_count_by_dataset = {}
        for k, v in self.softwares_by_task.items():
            for d in v:
                self.softwares_count_by_dataset.setdefault(d["dataset"], 0) + 1

        self.tasks, self.default_tasks, self.task_organizers = self._parse_task_list()
        self.datasets = self._parse_dataset_list()

    def _parse_organizer_list(self):
        """ Parse the PB Database and extract all hosts.
        :return: a dict {hostId: {"name", "years"}
        """
        organizers = modelpb.Hosts()
        Parse(open(self.organizers_file_path, "r").read(), organizers)
        # return {org.hostId: {"name": org.name, "years": org.years} for org in organizers.hosts}
        return {org.hostId: org for org in organizers.hosts}

    def _parse_users_list(self):
        users = modelpb.Users()
        Parse(open(self.users_file_path, "r").read(), users)
        return {user.userName: user for user in users.users}

    def _parse_task_list(self):
        """ Parse the PB Database and extract all tasks.
        :return:
        1. a dict with the tasks {"taskId": {"name", "description", "dataset_count", "organizer", "year", "web"}}
        2. a dict with default tasks of datasets {"dataset_id": "task_id"}
        """
        tasks = {}
        default_tasks = {}
        task_organizers = {}

        for task_path in self.tasks_dir_path.glob("*"):
            task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
            tasks[task.taskId] = {"name": task.taskName, "description": task.taskDescription, "task_id": task.taskId,
                                  "dataset_count": len(task.trainingDataset) + len(task.testDataset),
                                  "software_count": len(self.softwares_by_task.get(task.taskId, {0})),
                                  "web": task.web, "organizer": self.organizers.get(task.hostId, modelpb.Hosts.Host()).name,
                                  "year": self.organizers.get(task.hostId, modelpb.Hosts.Host()).years
                                  }
            for td in task.trainingDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers.get(task.hostId, modelpb.Hosts.Host()).name
            for td in task.testDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers.get(task.hostId, modelpb.Hosts.Host()).name

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
        for dataset_file in self.datasets_dir_path.rglob("*.prototext"):
            dataset = Parse(open(dataset_file, "r").read(), modelpb.Dataset())
            datasets[dataset.datasetId] = {
                "name": dataset.datasetId, "evaluator_id": dataset.evaluatorId,
                "dataset_id": dataset.datasetId,
                "is_confidential": dataset.isConfidential, "is_deprecated": dataset.isDeprecated,
                "year": extract_year_from_dataset_id(dataset.datasetId),
                "task": self.default_tasks.get(dataset.datasetId, ""),
                'organizer': self.task_organizers.get(dataset.datasetId, ""),
                "softwares": self.softwares_count_by_dataset.get(dataset.datasetId, 0)
            }

        return datasets

    def _parse_softwares_list(self):
        """ extract the softwares: {id, count, command, working_directory, dataset, run, creation_date, last_edit}
         :returns softwares_by_task: a dict {task_name: [{software}, ], }
         :returns softwares_by_user: a dict {user_id: [{software}, ], }
         """

        def parse_software_file(path):
            s = Parse(open(path, "r").read(), modelpb.Softwares())
            return [{"id": software.id, "count": software.count,
                     "command": software.command, "working_directory": software.workingDirectory,
                     "dataset": software.dataset, "run": software.run, "creation_date": software.creationDate,
                     "last_edit": software.lastEditDate}
                    for software in s.softwares if not software.deleted]

        softwares_by_task = {}
        softwares_by_user = {}
        for dataset_dir in self.softwares_dir_path.glob("*"):
            for user_dir in dataset_dir.glob("*"):
                _sw = parse_software_file(user_dir / "softwares.prototext")
                _swbd = softwares_by_task.get(dataset_dir.stem, list())
                _swbd.extend(_sw)
                softwares_by_task[dataset_dir.stem] = _swbd
                _swbu = softwares_by_user.get(user_dir.stem, list())
                _swbu.extend(_sw)
                softwares_by_user[user_dir.stem] = _swbu

        return softwares_by_task, softwares_by_user

    def _load_review(self, dataset_id, user_id, run_id):
        review_path = self.RUNS_DIR_PATH / dataset_id / user_id / run_id / "run-review.bin"
        if not review_path.exists():
            return {"reviewer": None}
        review = modelpb.RunReview()
        review.ParseFromString(open(review_path, "rb").read())
        return {
            "reviewer": review.reviewerId, "noErrors": review.noErrors, "missingOutput": review.missingOutput,
            "extraneousOutput": review.extraneousOutput, "invalidOutput": review.invalidOutput,
            "hasErrorOutput": review.hasErrorOutput, "otherErrors": review.otherErrors,
            "comment": review.comment, "hasErrors": review.hasErrors, "hasWarnings": review.hasWarnings,
            "hasNoErrors": review.hasNoErrors, "published": review.published, "blinded": review.blinded
        }

    def _load_user_runs(self, dataset_id, user_id):
        """
        :return runs: {run_id: {}}
        """
        runs = {}
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / user_id).glob("*"):
            if not (run_id_dir / "run.bin").exists():
                runs[run_id_dir.stem] = {"software": "", "input_run_id": "", "run_id": run_id_dir.stem,
                                         "dataset": dataset_id, "size": 0, "lines": 0, "files": 0, "dirs": 0,
                                         "review": {"reviewer": "tira", "otherErrors": True, "hasErrors": True,
                                                    "blinded": False, "published": False,
                                                    "comment": "Software execution failed with NRFC-01. Please contact support."}}
                continue
            run = modelpb.Run()
            run.ParseFromString(open(run_id_dir / "run.bin", "rb").read())
            if not run.deleted:
                runs[run.runId] = {"software": run.softwareId,
                                   "run_id": run.runId, "input_run_id": run.inputRun,
                                   "dataset": dataset_id, "size": "", "lines": "", "files": "", "dirs": "",
                                   "downloadable": run.downloadable,
                                   "review": self._load_review(dataset_id, user_id, run_id_dir.stem)}
        return runs

    def _load_user_evaluations(self, dataset_id, user_id, runs, only_published=True):
        """ load all evaluations for a user on a given dataset

        :param dataset_id: id/name of the dataset
        :param user_id: id/name of the user
        :param runs: a run dict as loaded by _load_user_runs: {run_id: {software, run_id, input_run_id, size, lines, files, dirs, downloadable, review}}
        :return 1: keys of the measures
        :return 2: [{run_id, user_id, software, input_run_id, measures: {}, runtime}]
        """
        evaluations = []
        measure_keys = set()
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / user_id).glob("*"):
            if not runs[run_id_dir.stem]["review"].get("reviewer", False):
                continue
            if runs[run_id_dir.stem]["review"].get("published", False) is False and only_published is True:
                continue
            if not (run_id_dir / "output/evaluation.bin").exists():
                continue

            evaluation = modelpb.Evaluation()
            evaluation.ParseFromString(open(run_id_dir / "output/evaluation.bin", "rb").read())

            if not measure_keys:
                measure_keys.update({measure.key for measure in evaluation.measure})

            measures = {measure.key: measure.value for measure in evaluation.measure}
            evaluations.append({"run_id": run_id_dir.stem, "user_id": user_id,
                                "published": runs[run_id_dir.stem]["review"].get("published", False),
                                "software": runs[run_id_dir.stem]["software"],
                                "input_run_id": runs[run_id_dir.stem]["input_run_id"],
                                "measures": measures, "runtime": ""})

        return list(measure_keys), evaluations

    def get_tasks(self) -> list:
        return list(self.tasks.values())

    def get_datasets_by_task(self, task_id: str) -> list:
        """ return the list of datasets associated with this task_id
        :return datasets: [{ }]
        """
        return [dataset for dataset in self.datasets.values() if dataset["task"] == task_id]

    def get_dataset_runs(self, dataset_id, only_public_results=True) -> tuple:
        """ return for all users on a given dataset_id: runs, evaluations, user_stats
        Its equivalent to using the individual getters, but much faster

        :return ev_keys: keys of the measures used in this dataset
        :return user: dict of users and runs
        :return status: {user_id: {signed_in, softwares, deleted, now_running, runs, reviewed, unreviewed}}
        runs: {user_id: [{software, size, lines, files, dirs, review: {}}],
        evaluations: {user_id: [{software, run_id, input_run_id, measures: {}, runtime}]}
        """
        status = {}
        runs = {}
        evaluations = {}
        ev_keys = set()
        for user_run_dir in (self.RUNS_DIR_PATH / dataset_id).glob("*"):
            r = self._load_user_runs(dataset_id, user_run_dir.stem)
            keys, ev = self._load_user_evaluations(dataset_id, user_run_dir.stem, r, only_published=only_public_results)
            runs[user_run_dir.stem] = list(r.values())

            # as keys for the measures, we use the first non-empty set of keys we encounter
            if keys and not ev_keys:
                ev_keys = keys

            # update the measures evaluations to a list, following the order of the keys
            evaluations[user_run_dir.stem] = ev
            for eval in evaluations[user_run_dir.stem]:
                m = eval["measures"]
                eval["measures"] = [m[k] for k in keys]

            unreviewed_count = sum([1 for x in runs[user_run_dir.stem] if not x["review"].get("reviewer", None)])
            status[user_run_dir.stem] = {"user_id": user_run_dir.stem,
                                         "signed_in": "", "softwares": "", "deleted": "", "now_running": "",
                                         "runs": len(runs[user_run_dir.stem]),
                                         "reviewed": "", "unreviewed": unreviewed_count}  # TODO dummy

        return ev_keys, status, runs, evaluations

    def get_user_runs(self, user_id):
        """
        returns a list of all the runs of a user over all datasets: [{software, run_id, input_run_id, size, lines, files, dirs, review: {}}]
        """
        relevant_datasets = {software["dataset"] for software in self.softwares_by_user[user_id]}

        runs = []
        for dataset_id in relevant_datasets:
            user_runs = self._load_user_runs(dataset_id, user_id)
            runs.extend(list(user_runs.values()))

        return runs
