"""
p.stat().st_mtime - change time
"""
from google.protobuf.text_format import Parse
from google.protobuf.json_format import MessageToDict
from pathlib import Path
import logging
from django.conf import settings
import socket
from datetime import datetime

from .proto import TiraClientWebMessages_pb2 as modelpb
from .proto import tira_host_pb2 as model_host

logger = logging.getLogger("tira")


def auto_reviewer(review_path, run_id):
    """ Do standard checks for reviews so we do not need to wait for a reviewer to check for:
     - failed runs (
     """
    review_file = review_path / "run-review.bin"
    review = modelpb.RunReview()

    if review_file.exists():  # TODO this will throw if the file is corrupt. Let it throw to not overwrite files.
        try:
            review.ParseFromString(open(review_path, "rb").read())
            return review
        except Exception as e:
            logger.exception(f"review file: {review_file} exists but is corrupted with {e}")
            raise FileExistsError(f"review file: {review_file} exists but is corrupted with {e}")

    review.reviewerId = 'tira'
    review.reviewDate = str(datetime.utcnow())
    review.hasWarnings = False
    review.hasErrors = False
    review.hasNoErrors = False
    review.blinded = True
    review.runId = run_id

    try:
        if not (review_path / "run.bin").exists():  # No Run file
            review.comment = "Internal Error: No run definition recorded. Please contact the support."
            review.hasErrors = True
            review.hasNoErrors = False
            review.blinded = False

        if not (review_path / "output").exists():  # No Output directory
            review.comment = "No Output was produced"
            review.hasErrors = True
            review.hasNoErrors = False
            review.blinded = True
            review.missing_output = True

    except Exception as e:
        review_path.mkdir(parents=True, exist_ok=True)
        review.reviewerId = 'tira'
        review.comment = f"Internal Error: {e}. Please contact the support."
        review.hasErrors = True
        review.hasNoErrors = False
        review.blinded = False

    return review


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
    tira_root = settings.TIRA_ROOT
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
    commands_dir_path = tira_root / Path("state/commands/")
    command_logs_path = tira_root / Path(f"log/virtual-machine-hosts/{socket.gethostname()}/")
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
        self.commandState = None
        self.command_logs_path.mkdir(exist_ok=True, parents=True)

        self.build_model()

    def build_model(self):
        self._parse_organizer_list()
        self._parse_vm_list()
        self._parse_task_list()
        self._parse_dataset_list()
        self._parse_software_list()
        self._parse_command_state()

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
        logger.info('loading tasks')
        for task_path in self.tasks_dir_path.glob("*"):
            task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
            tasks[task.taskId] = task

        self.tasks = tasks

    def _parse_dataset_list(self):
        """ Load all the datasets from the Filedatabase.
        :return: a dict {dataset_id: dataset protobuf object}
        """
        datasets = {}
        logger.info('loading datasets')
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
        logger.info('loading softwares')
        for task_dir in self.softwares_dir_path.glob("*"):
            for user_dir in task_dir.glob("*"):
                s = Parse(open(user_dir / "softwares.prototext", "r").read(), modelpb.Softwares())
                software_list = [user_software for user_software in s.softwares if not user_software.deleted]
                software[f"{task_dir.stem}${user_dir.stem}"] = software_list

        self.software = software

    def _parse_command_state(self):
        """ Parse the command state file. """
        command_states_path = self.commands_dir_path / f"{socket.gethostname()}.prototext"
        if command_states_path.exists():
            self.commandState = Parse(open(command_states_path, "r").read(), model_host.CommandState())
        else:
            self.commandState = model_host.CommandState()
            self.commands_dir_path.mkdir(exist_ok=True, parents=True)
            open(command_states_path, 'w').write(str(self.commandState))

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
    def _load_review(self, dataset_id, vm_id, run_id, as_json=False):
        """ This method loads a review or toggles auto reviewer if it does not exist. """

        def _as_json(r):
            if as_json:
                return {"reviewer": review.reviewerId, "noErrors": review.noErrors,
                        "missingOutput": review.missingOutput,
                        "extraneousOutput": review.extraneousOutput, "invalidOutput": review.invalidOutput,
                        "hasErrorOutput": review.hasErrorOutput, "otherErrors": review.otherErrors,
                        "comment": review.comment, "hasErrors": review.hasErrors, "hasWarnings": review.hasWarnings,
                        "hasNoErrors": review.hasNoErrors, "published": review.published, "blinded": review.blinded
                        }
            return review

        review_path = self.RUNS_DIR_PATH / dataset_id / vm_id / run_id
        review_file = review_path / "run-review.bin"
        if not review_file.exists():
            review = auto_reviewer(review_path, run_id)
            self._save_review(dataset_id, vm_id, run_id, review)
            return _as_json(review)

        review = modelpb.RunReview()
        review.ParseFromString(open(review_file, "rb").read())
        return _as_json(review)

    def _load_user_reviews(self, dataset_id, vm_id, as_json=False):
        return {run_id_dir.stem: self._load_review(dataset_id, vm_id, run_id_dir.stem, as_json)
                for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*")}

    def _load_vm(self, vm_id):
        """ load a vm object from vm_dir_path """
        return Parse(open(self.vm_dir_path / f"{vm_id}.prototext").read(), modelpb.VirtualMachine())

    def _load_run(self, dataset_id, vm_id, run_id, return_deleted=False, as_json=False):
        run_dir = (self.RUNS_DIR_PATH / dataset_id / vm_id / run_id)
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

    def _load_vm_runs(self, dataset_id, vm_id, return_deleted=False, include_evaluations=False, as_json=False):
        """ load all run's data.
        @param include_evaluations: If True, also load evaluator runs (where an evaluation.bin exists)
        """
        runs = {}
        for run_id_dir in (self.RUNS_DIR_PATH / dataset_id / vm_id).glob("*"):
            run_id = run_id_dir.stem
            run = self._load_run(dataset_id, vm_id, run_id, return_deleted=return_deleted, as_json=as_json)

            if run is not None:
                runs[run_id] = run

        return runs

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

    # ---------------------------------------------------------------------
    # ---- save methods to update protos
    # ---------------------------------------------------------------------

    def _save_task(self, task_proto, overwrite=False):
        """ makes persistant changes to task: store in memory and to file.
         Returns false if task exists and overwrite is false. """
        # open(f'/home/tira/{task_id}.prototext', 'wb').write(new_task.SerializeToString())
        new_task_file_path = self.tasks_dir_path / f'{task_proto.taskId}.prototext'
        if not overwrite and new_task_file_path.exists():
            return False
        self.tasks[task_proto.taskId] = task_proto
        open(new_task_file_path, 'w').write(str(task_proto))
        self._build_task_relations()
        return True

    def _save_vm(self, vm_proto, overwrite=False):
        new_vm_file_path = self.vm_dir_path / f'{vm_proto.virtualMachineId}.prototext'
        if not overwrite and new_vm_file_path.exists():
            return False
        # self.vms[vm_proto.virtualMachineId] = vm_proto  # TODO see issue:30
        open(new_vm_file_path, 'w').write(str(vm_proto))
        return True

    def _save_dataset(self, dataset_proto, task_id, overwrite=False):
        """ dataset_dir_path/task_id/dataset_id.prototext """
        new_dataset_file_path = self.datasets_dir_path / task_id / f'{dataset_proto.datasetId}.prototext'
        if not overwrite and new_dataset_file_path.exists():
            return False
        (self.datasets_dir_path / task_id).mkdir(exist_ok=True, parents=True)
        open(new_dataset_file_path, 'w').write(str(dataset_proto))
        self.datasets[dataset_proto.datasetId] = dataset_proto
        return True

    def _save_review(self, dataset_id, vm_id, run_id, review):
        review_path = self.RUNS_DIR_PATH / dataset_id / vm_id / run_id
        open(review_path / "run-review.prototext", 'w').write(str(review))
        open(review_path / "run-review.bin", 'wb').write(review.SerializeToString())
        return True

    # get methods are the public interface.
    def get_vm(self, vm_id: str):
        # TODO should return as dict
        return self.vms.get(vm_id, None)

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

    def get_organizer(self, organizer_id: str):
        # TODO should return as dict
        return self.organizers[organizer_id]

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

    def get_host_list(self) -> list:
        return list(open(self.host_list_file, "r").readlines())

    def get_ova_list(self) -> list:
        return [f"{ova_file.stem}.ova" for ova_file in self.ova_dir.glob("*.ova")]

    def get_vm_list(self):
        """ load the vm-info file which stores all active vms as such:
        <hostname>\t<vm_id>[\t<state>]\n
        ...

        returns a list of tuples (hostname, vm_id, state)
        """
        vm_list = []
        for line in open(self.vm_list_file, 'r'):
            l = line.split("\t")
            try:
                vm_list.append([l[0], l[1].strip(), l[2].strip() if len(l) > 2 else ''])
            except IndexError as e:
                logger.error(e, line)
        return vm_list

    def get_vms_by_dataset(self, dataset_id):
        """ return a list of vm_id's that have runs on this dataset """
        return [user_run_dir.stem
                for user_run_dir in (self.RUNS_DIR_PATH / dataset_id).glob("*")]

    def get_vm_runs_by_dataset(self, dataset_id, vm_id, include_evaluations=True):
        user_runs = self._load_vm_runs(dataset_id, vm_id, include_evaluations, as_json=True)
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
                for run_id, ev in
                self._load_vm_evaluations(dataset_id, vm_id, only_published=only_public_results).items()}

    def get_run(self, dataset_id, vm_id, run_id):
        return self._load_run(dataset_id, vm_id, run_id, as_json=True)

    def get_run_review(self, dataset_id, vm_id, run_id):
        return self._load_review(dataset_id, vm_id, run_id, as_json=True)

    def get_vm_reviews_by_dataset(self, dataset_id, vm_id):
        return self._load_user_reviews(dataset_id, vm_id, as_json=True)

    def get_software(self, task_id, vm_id):
        """ Returns the software of a vm on a task in json """
        logger.debug(f"get_software({task_id}, {vm_id})")
        return [{"id": software.id, "count": software.count,
                 "task_id": task_id, "vm_id": vm_id,
                 "command": software.command, "working_directory": software.workingDirectory,
                 "dataset": software.dataset, "run": software.run, "creation_date": software.creationDate,
                 "last_edit": software.lastEditDate}
                for software in self.software.get(f"{task_id}${vm_id}", [])]

    def get_users_vms(self):
        """ Return the users list. """
        return self.vms

    # ------------------------------------------------------------
    # add methods to add new data to the model
    # ------------------------------------------------------------

    def create_task(self, task_id, task_name, task_description, master_vm_id, organizer, website):
        """ Add a new task to the database.
         CAUTION: This function does not do any sanity checks and will OVERWRITE existing tasks """
        new_task = modelpb.Tasks.Task()
        new_task.taskId = task_id
        new_task.taskName = task_name
        new_task.taskDescription = task_description
        new_task.virtualMachineId = master_vm_id
        new_task.hostId = organizer
        new_task.web = website
        return self._save_task(new_task)

    def add_dataset(self, task_id, dataset_id, dataset_type, dataset_name):
        """ TODO documentation
        """

        # update task_dir_path/task_id.prototext:
        dataset_id = f"{dataset_id}-{dataset_type}"
        for_task = self.tasks.get(task_id, None)
        if not for_task:
            raise KeyError(f"No task with id {task_id}")

        if dataset_type == 'test' and dataset_id not in for_task.testDataset:
            for_task.testDataset.append(dataset_id)
        elif dataset_type in {'training', 'dev'} and dataset_id not in for_task.trainingDataset:
            for_task.trainingDataset.append(dataset_id)
        elif dataset_type not in {'training', 'dev', 'test'}:
            raise KeyError("dataset type must be test, training, or dev")
        task_ok = self._save_task(for_task, overwrite=True)

        # create new dataset_dir_path/task_id/dataset_id.prototext
        ds = modelpb.Dataset()
        ds.datasetId = dataset_id
        ds.displayName = dataset_name
        ds.isDeprecated = False
        ds.isConfidential = True if dataset_type == 'test' else False
        dataset_ok = self._save_dataset(ds, task_id)

        # create dirs data_path/dataset/test-dataset[-truth]/task_id/dataset-id-type
        new_dirs = []
        if dataset_type == 'test':
            new_dirs.append((self.data_path / f'test-datasets' / task_id / dataset_id))
            new_dirs.append((self.data_path / f'test-datasets-truth' / task_id / dataset_id))
        else:
            new_dirs.append((self.data_path / f'training-datasets' / task_id / dataset_id))
            new_dirs.append((self.data_path / f'training-datasets-truth' / task_id / dataset_id))
        for d in new_dirs:
            d.mkdir(parents=True, exist_ok=True)

        return [str(nd) for nd in new_dirs]

    def add_evaluator(self, vm_id, task_id, dataset_id, dataset_type, command, working_directory, measures):
        """ TODO documentation
        """
        evaluator_id = f"{dataset_id}-evaluator"
        dataset_id = f"{dataset_id}-{dataset_type}"

        # update dataset_id.prototext
        dataset = self.datasets.get(dataset_id)
        dataset.evaluatorId = evaluator_id
        dataset_ok = self._save_dataset(dataset, task_id, overwrite=True)

        # add evaluators to vm
        vm = self._load_vm(vm_id)
        if evaluator_id not in {ev.evaluatorId for ev in vm.evaluators}:
            ev = modelpb.Evaluator()
            ev.evaluatorId = evaluator_id
            ev.command = command
            ev.workingDirectory = working_directory
            ev.measures = ",".join([x[0].strip('\r') for x in measures])
            ev.measureKeys.extend([x[1].strip('\r') for x in measures])
            vm.evaluators.append(ev)
            vm_ok = self._save_vm(vm, overwrite=True)
        else:
            vm_ok = True

        return vm_ok and dataset_ok

    def update_review(self, dataset_id, vm_id, run_id,
                      reviewer_id: str = None, review_date: str = None, has_errors: bool = None,
                      has_no_errors: bool = None, no_errors: bool = None, missing_output: bool = None,
                      extraneous_output: bool = None, invalid_output: bool = None, has_error_output: bool = None,
                      other_errors: bool = None, comment: str = None, published: bool = None, blinded: bool = None,
                      has_warnings: bool = False):
        """ updates the review specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """
        review = self._load_review(dataset_id, vm_id, run_id)

        if reviewer_id is not None:
            review.reviewerId = reviewer_id
        if review_date is not None:
            review.reviewDate = review_date
        if has_errors is not None:
            review.hasErrors = has_errors
        if has_warnings is not None:
            review.hasWarnings = has_warnings
        if has_no_errors is not None:
            review.hasNoErrors = has_no_errors
        if no_errors is not None:
            review.noErrors = no_errors
        if missing_output is not None:
            review.missingOutput = missing_output
        if extraneous_output is not None:
            review.extraneousOutput = extraneous_output
        if invalid_output is not None:
            review.invalidOutput = invalid_output
        if has_error_output is not None:
            review.hasErrorOutput = has_error_output
        if other_errors is not None:
            review.otherErrors = other_errors
        if comment is not None:
            review.comment = comment
        if published is not None:
            review.published = published
        if blinded is not None:
            review.blinded = blinded
        try:
            self._save_review(dataset_id, vm_id, run_id, review)
            return True
        except Exception as e:
            logger.exception(f"Exception while saving review ({dataset_id}, {vm_id}, {run_id}): {e}")
            return False

    def add_ongoing_execution(self, hostname, vm_id, ova):
        """ add this create to the stack, so we know it's in progress. """
        print('model', hostname, vm_id, ova)
        pass

    def complete_execution(self):
        # TODO implement
        pass

    def get_commands_bulk(self, bulk_id):
        """
        Get commands list by bulk command id
        :param bulk_id:
        """
        self._parse_command_state()
        return [MessageToDict(command) for command in self.commandState.commands if command.bulkCommandId == bulk_id]

    def get_command(self, command_id):
        """
        Get command object
        :param command_id:
        """
        self._parse_command_state()
        for command in self.commandState.commands:
            if command.id == command_id:
                return MessageToDict(command)
        return None
