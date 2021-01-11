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
        self.organizers = None  # dict of host objects host_id: modelpb.Host
        self.vms = None  # dict of vm_id: modelpb.User
        self.tasks = None  # dict of task_id: modelpb.Tasks.Task
        self.datasets = None  # dict of dataset_id: modelpb.Dataset
        self.software = None  # dict of task_id$vm_id: modelpb.Software
        self.default_tasks = None  # dataset_id: task_id
        self.task_organizers = None  # dataset_id: modelpb.Hosts.Host.name
        self.software_by_task = None  # task_id: [modelpb.Software]
        self.software_by_vm = None  # vm_id: [modelpb.Software]
        self.software_count_by_dataset = None  # dataset_id: int()

        self._parse_organizer_list()
        self._parse_vm_list()
        self._parse_task_list()
        self._parse_dataset_list()
        self._parse_software_list()

        self._build_task_relations()
        self._build_software_relations()
        self._build_software_counts()

    # _parse methods parse files once on startup
    def _parse_organizer_list(self):
        """ Parse the PB Database and extract all hosts.
        :return: a dict {hostId: {"name", "years"}
        """
        organizers = modelpb.Hosts()
        Parse(open(self.organizers_file_path, "r").read(), organizers)

        self.organizers = {org.hostId: org for org in organizers.hosts}

    def _parse_vm_list(self):
        users = modelpb.Users()
        Parse(open(self.users_file_path, "r").read(), users)
        self.vms = {user.userName: user for user in users.users}

    def _parse_task_list(self):
        """ Parse the PB Database and extract all tasks.
        :return:
        1. a dict with the tasks {"taskId": {"name", "description", "dataset_count", "organizer", "year", "web"}}
        2. a dict with default tasks of datasets {"dataset_id": "task_id"}
        """
        tasks = {}

        for task_path in self.tasks_dir_path.glob("*"):
            task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
            tasks[task.taskId] = task

        self.tasks = tasks

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

    # _build methods reconstruct the relations once per parse. This is a shortcut for frequent joins.
    def _build_task_relations(self):
        """ parse the relation dicts self.default_tasks and self.task_organizers from self.tasks
        """
        default_tasks = {}
        task_organizers = {}
        for task_id, task in self.tasks.items():
            for td in task.trainingDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers.get(task.hostId, modelpb.Hosts.Host()).name
            for td in task.testDataset:
                default_tasks[td] = task.taskId
                task_organizers[td] = self.organizers.get(task.hostId, modelpb.Hosts.Host()).name

        self.default_tasks = default_tasks
        self.task_organizers = task_organizers

    def _build_software_relations(self):
        software_by_task = {}
        software_by_vm = {}

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

    def _build_software_counts(self):
        counts = {}

        for software_list in self.software.values():
            for software in software_list:
                c = counts.get(software.dataset, 0)
                c += 1
                counts[software.dataset] = c

        self.software_count_by_dataset = counts

    # _load methods parse files on the fly when pages are called
    def _load_review(self, dataset_id, vm_id, run_id):
        review_path = self.RUNS_DIR_PATH / dataset_id / vm_id / run_id / "run-review.bin"
        if not review_path.exists():
            review = modelpb.RunReview()
            review.reviewerId = ""
            return review
        review = modelpb.RunReview()
        review.ParseFromString(open(review_path, "rb").read())
        return review

    def _load_user_reviews(self, dataset_id, vm_id):
        reviews = {}
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*"):
            if not (run_id_dir / "run.bin").exists():
                review = modelpb.RunReview()
                review.runId = run_id_dir.stem
                review.reviewerId = 'tira'
                review.reviewDate = ""
                review.comment = "Internal Error: No run definition recorded. Please contact the support."
                review.hasErrors = True
                review.hasWarnings = False
                review.hasNoErrors = False
                review.blinded = False

                reviews[run_id_dir.stem] = review
                continue

            reviews[run_id_dir.stem] = self._load_review(dataset_id, vm_id, run_id_dir.stem)

        return reviews

    def _get_review(self, review):
        return {"reviewer": review.reviewerId, "noErrors": review.noErrors, "missingOutput": review.missingOutput,
                "extraneousOutput": review.extraneousOutput, "invalidOutput": review.invalidOutput,
                "hasErrorOutput": review.hasErrorOutput, "otherErrors": review.otherErrors,
                "comment": review.comment, "hasErrors": review.hasErrors, "hasWarnings": review.hasWarnings,
                "hasNoErrors": review.hasNoErrors, "published": review.published, "blinded": review.blinded
                }

    def _load_vm_runs(self, dataset_id, vm_id, include_evaluations):
        """ load all run's data.
        @param include_evaluations: If True, also load evaluator runs (where an evaluation.bin exists)
        """
        runs = {}
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*"):
            if not (run_id_dir / "run.bin").exists():
                run = modelpb.Run()
                run.softwareId = ""
                run.runId = run_id_dir.stem
                run.inputDataset = dataset_id
                runs[run_id_dir.stem] = run
                continue

            run = modelpb.Run()
            run.ParseFromString(open(run_id_dir / "run.bin", "rb").read())
            if run.deleted:
                continue
            if include_evaluations is False and (run_id_dir / "output" / "evaluation.bin").exists():
                continue
            runs[run.runId] = self._get_run(run)
        return runs

    def _get_run(self, run):
        return {"software": run.softwareId,
                "run_id": run.runId, "input_run_id": run.inputRun,
                "dataset": run.inputDataset, "downloadable": run.downloadable}

    def _load_vm_evaluations(self, dataset_id, vm_id, only_published):
        """ load all evaluations for a user on a given dataset

        :param dataset_id: id/name of the dataset
        :param vm_id: id/name of the user
        :param runs: a run dict as loaded by _load_user_runs: {run_id: {software, run_id, input_run_id, size, lines, files, dirs, downloadable, review}}
        :return 1: keys of the measures
        :return 2: [{run_id, vm_id, software, input_run_id, measures: {}, runtime}]
        """
        evaluations = {}
        # measure_keys = set()
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*"):
            if not (run_id_dir / "output/evaluation.bin").exists():
                continue
            # if not runs[run_id_dir.stem]["review"].get("reviewer", False):
            #     continue
            if only_published is True and self._load_review(dataset_id, vm_id, run_id_dir.stem).published is False:
                continue

            evaluation = modelpb.Evaluation()
            evaluation.ParseFromString(open(run_id_dir / "output/evaluation.bin", "rb").read())

            # if not measure_keys:
            #     measure_keys.update({measure.key for measure in evaluation.measure})
            #
            # measures = {measure.key: measure.value for measure in evaluation.measure}
            evaluations[run_id_dir.stem] = evaluation

        return evaluations

    def _get_evaluation(self, evaluation):
        return {measure.key: measure.value for measure in evaluation.measure}

    # get methods are the public interface.
    def get_tasks(self) -> list:
        tasks = [self.get_task(task.taskId)
                 for task in self.tasks.values()]
        return tasks

    def get_task(self, task_id: str) -> dict:
        t = self.tasks[task_id]
        return {"task_name": t.taskName,
                "description": t.taskDescription,
                "task_id": t.taskId,
                "dataset_count": len(t.trainingDataset) + len(t.testDataset),
                "software_count": len(self.software_by_task.get(t.taskId, {0})),
                "web": t.web,
                "organizer": self.organizers.get(t.hostId, modelpb.Hosts.Host()).name,
                "year": self.organizers.get(t.hostId, modelpb.Hosts.Host()).years
                }

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
            "task": self.default_tasks.get(dataset.datasetId, "None"),
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

    # # TODO change accordingly with _load_runs
    # # TODO should actually give us a list of all runs done on this dataset (without grouping)
    # def get_dataset_runs(self, dataset_id, only_public_results=True) -> tuple:
    #     """ return all runs for all users on a given dataset_id """
    #     status = {}
    #     runs = {}
    #     evaluations = {}
    #     ev_keys = set()
    #     for user_run_dir in (self.RUNS_DIR_PATH / dataset_id).glob("*"):
    #         # all of these are dicts
    #         user_runs = self._load_vm_runs(dataset_id, user_run_dir.stem)
    #         user_evaluations = self._load_vm_evaluations(dataset_id, user_run_dir.stem,
    #                                                      only_published=only_public_results)
    #         user_reviews = self._load_user_reviews(dataset_id, user_run_dir.stem)
    #
    #         keys = set()
    #         for e in ev.values():
    #             keys.update(e.keys())
    #         keys = list(keys)
    #
    #         # runs[user_run_dir.stem] = list(r.values())
    #
    #         # update the measures evaluations to a list, following the order of the keys
    #         evaluations[user_run_dir.stem] = ev
    #         for eval in evaluations[user_run_dir.stem]:
    #             m = eval["measures"]
    #             eval["measures"] = [m[k] for k in keys]
    #
    #         unreviewed_count = sum([1 for x in runs[user_run_dir.stem] if not x["review"].get("reviewer", None)])
    #         status[user_run_dir.stem] = {"user_id": user_run_dir.stem,
    #                                      "signed_in": "", "softwares": "", "deleted": "", "now_running": "",
    #                                      "runs": len(runs[user_run_dir.stem]),
    #                                      "reviewed": "", "unreviewed": unreviewed_count}  # TODO dummy
    #
    #     return ev_keys, status, runs, evaluations

    def get_vms_by_dataset(self, dataset_id):
        """ return a list of vm_id's that have runs on this dataset """
        return [user_run_dir.stem
                for user_run_dir in (self.RUNS_DIR_PATH / dataset_id).glob("*")]

    def get_vm_runs_by_dataset(self, dataset_id, vm_id, include_evaluations=True):
        user_runs = self._load_vm_runs(dataset_id, vm_id, include_evaluations)
        return list(user_runs.values())

    def get_vm_runs_by_task(self, task_id, vm_id, include_evaluations=True):
        """ returns a list of all the runs of a user over all datasets in json (as returned by _load_user_runs) """
        relevant_datasets = {software["dataset"] for software in self.get_software(task_id, vm_id)}
        runs = []
        for dataset_id in relevant_datasets:
            runs.extend(self.get_vm_runs_by_dataset(dataset_id, vm_id, include_evaluations))
        return runs

    def get_vm_evaluations_by_dataset(self, dataset_id, vm_id, only_public_results=True):
        """ Return a dict of run_id: evaluation_results for the given vm on the given dataset
        @param only_public_results: only return the measures for published datasets.
        """
        return {run_id: self._get_evaluation(ev)
                for run_id, ev in self._load_vm_evaluations(dataset_id, vm_id, only_published=only_public_results).items()}

    def get_vm_run_reviews(self):
        pass

    def get_vm_reviews_by_dataset(self, dataset_id, vm_id):
        return {run_id: self._get_review(review)
                for run_id, review in self._load_user_reviews(dataset_id, vm_id).items()}

    def get_software(self, task_id, vm_id):
        """ Returns the software of a vm on a task in json """
        return [{"id": software.id, "count": software.count,
                 "task_id": task_id, "vm_id": vm_id,
                 "command": software.command, "working_directory": software.workingDirectory,
                 "dataset": software.dataset, "run": software.run, "creation_date": software.creationDate,
                 "last_edit": software.lastEditDate}
                for software in self.software[f"{task_id}${vm_id}"]]
