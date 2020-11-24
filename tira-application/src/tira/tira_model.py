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
    RUNS_DIR_PATH = Path("/mnt/ceph/tira/data/runs")

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
                runs[run_id_dir.stem] = {"software": "", "input_run_id": "",
                                         "size": 0, "lines": 0, "files": 0, "dirs": 0,
                                         "review": {"reviewer": "system", "otherErrors": True, "hasErrors": True,
                                                    "blinded": False, "published": False,
                                                    "comment": "Software execution failed with NRFC-01. Please contact support."}}
                continue
            run = modelpb.Run()
            run.ParseFromString(open(run_id_dir / "run.bin", "rb").read())
            if not run.deleted:
                runs[run.runId] = {"software": run.softwareId, "run_id": run.runId, "input_run_id": run.inputRun,
                                   "size": "", "lines": "", "files": "", "dirs": "", "downloadable": run.downloadable,
                                   "review": self._load_review(dataset_id, user_id, run_id_dir.stem)}
        return runs

    def _load_user_evaluations(self, dataset_id, user_id, runs, only_published=True):
        """ load all evaluation dicts for a user on a given dataset
        :return: {run_id: {software, input_run_id, measures: {}, runtime}
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

    def get_runs(self, dataset_id, only_public_results=True) -> tuple:
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

            status[user_run_dir.stem] = {"user_id": user_run_dir.stem,
                                         "signed_in": "", "softwares": "", "deleted": "", "now_running": "",
                                         "runs": len(runs[user_run_dir.stem]),
                                         "reviewed": "", "unreviewed": sum([1 for x in runs[user_run_dir.stem] if not x["review"].get("reviewer", None)])
                                         }  # TODO dummy

        return ev_keys, status, runs, evaluations
