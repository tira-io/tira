from google.protobuf.text_format import Parse
from pathlib import Path
import logging
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Count, Q
from shutil import rmtree
from datetime import datetime as dt
import randomname

from tira.util import TiraModelWriteError, TiraModelIntegrityError
from tira.proto import TiraClientWebMessages_pb2 as modelpb
from tira.util import auto_reviewer, now
import tira.model as modeldb
import tira.data.data as dbops

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
    runs_dir_path = tira_root / Path("data/runs")

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
        self.evaluators = {}  # dataset_id: [modelpb.Evaluator] used as cache
        # dbops.index(self.organizers_file_path, self.users_file_path, self.vm_dir_path, self.tasks_dir_path,
        #             self.datasets_dir_path, self.softwares_dir_path, self.runs_dir_path)

    def build_model(self):
        dbops.index(self.organizers_file_path, self.users_file_path, self.vm_dir_path, self.tasks_dir_path,
                    self.datasets_dir_path, self.softwares_dir_path, self.runs_dir_path)

    def reload_vms(self):
        """ reload VM and user data from the export format of the model """
        dbops.reload_vms(self.users_file_path, self.vm_dir_path)

    def reload_datasets(self):
        """ reload dataset data from the export format of the model """
        dbops.reload_datasets(self.tasks_dir_path)

    def reload_tasks(self):
        """ reload task data from the export format of the model """
        dbops.reload_tasks(self.tasks_dir_path)

    def reload_runs(self, vm_id):
        """ reload run data for a VM from the export format of the model """
        dbops.reload_runs(self.runs_dir_path, vm_id)

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
    def load_review(self, dataset_id, vm_id, run_id):
        """ This method loads a review or toggles auto reviewer if it does not exist. """

        review_path = self.runs_dir_path / dataset_id / vm_id / run_id
        review_file = review_path / "run-review.bin"
        if not review_file.exists():
            review = auto_reviewer(review_path, run_id)
            self._save_review(dataset_id, vm_id, run_id, review)
            return review

        review = modelpb.RunReview()
        review.ParseFromString(open(review_file, "rb").read())
        return review

    def _load_vm(self, vm_id):
        """ load a vm object from vm_dir_path """
        return Parse(open(self.vm_dir_path / f"{vm_id}.prototext").read(), modelpb.VirtualMachine())

    def _load_softwares(self, task_id, vm_id):
        # Leave this
        softwares_dir = self.softwares_dir_path / task_id / vm_id
        softwares_dir.mkdir(parents=True, exist_ok=True)
        software_file = softwares_dir / "softwares.prototext"
        if not software_file.exists():
            software_file.touch()

        return Parse(open(self.softwares_dir_path / task_id / vm_id / "softwares.prototext", "r").read(),
                     modelpb.Softwares())

    def _load_run(self, dataset_id, vm_id, run_id, return_deleted=False):
        """ Load a protobuf run file with some edge-case checks. """
        run_dir = self.runs_dir_path / dataset_id / vm_id / run_id
        if not (run_dir / "run.bin").exists():
            if (run_dir / "run.prototext").exists():
                r = Parse(open(run_dir / "run.prototext", "r").read(), modelpb.Run())
                open(run_dir / "run.bin", 'wb').write(r.SerializeToString())
            else:
                logger.error(f"Try to read a run without a run.bin: {dataset_id}-{vm_id}-{run_id}")
                run = modelpb.Run()
                run.softwareId = "This run is corrupted. Please contact the support."
                run.runId = run_id
                run.inputDataset = dataset_id
                return run

        run = modelpb.Run()
        run.ParseFromString(open(run_dir / "run.bin", "rb").read())
        if return_deleted is False and run.deleted:
            run.softwareId = "This run was deleted"
            run.runId = run_id
            run.inputDataset = dataset_id

        return run

    # ---------------------------------------------------------------------
    # ---- save methods to update protos
    # ---------------------------------------------------------------------

    def _save_task(self, task_id, task_name, task_description, master_vm_id, organizer, website,
                   append_training_datasets: list = None, append_test_datasets: list = None, overwrite=False):
        """ makes persistant changes to task: store in memory and to file.
         Returns false if task exists and overwrite is false. """
        task_file_path = self.tasks_dir_path / f'{task_id}.prototext'
        if not overwrite and task_file_path.exists():
            raise TiraModelWriteError(f"Failed to write task, task exists and overwrite is not allowed here")
        elif overwrite and task_file_path.exists():
            task = Parse(open(task_file_path, "r").read(), modelpb.Tasks.Task())
        else:
            task = modelpb.Tasks.Task()

        task.taskId = task_id if task_id else task.taskId
        task.taskName = task_name if task_name else task.taskName
        task.taskDescription = task_description if task_description else task.taskDescription
        task.virtualMachineId = master_vm_id if master_vm_id else task.virtualMachineId
        task.hostId = organizer if organizer else task.hostId
        task.web = website if website else task.web

        for append in append_training_datasets:
            task.trainingDataset.append(append)
        for append in append_test_datasets:
            task.testDataset.append(append)

        # self.tasks[task_id] = new_task TODO
        open(task_file_path, 'w').write(str(task))
        # self._build_task_relations() TODO
        return True

    def _save_vm(self, vm_id=None, user_name=None, initial_user_password=None, ip=None, host=None, ssh=None, rdp=None,
                 overwrite=False):
        new_vm_file_path = self.vm_dir_path / f'{vm_id}.prototext'
        if not overwrite and new_vm_file_path.exists():
            raise TiraModelWriteError(f"Failed to write vm, vm exists and overwrite is not allowed here")
        elif overwrite and new_vm_file_path.exists():
            vm = Parse(open(new_vm_file_path).read(), modelpb.VirtualMachine())
        else:
            vm = modelpb.VirtualMachine()
        vm.virtualMachineId = vm_id if vm_id else vm.virtualMachineId
        vm.vmId = vm_id if vm_id else vm.vmId
        vm.vmName = vm_id if vm_id else vm.vmName
        vm.host = host if host else vm.host
        vm.adminName = vm.adminName if vm.adminName else 'admin'  # Note these are required but deprecated
        vm.adminPw = vm.adminPw if vm.adminPw else 'admin'  # Note these are required but deprecated
        vm.userName = user_name if user_name else vm.userName
        vm.userPw = initial_user_password if initial_user_password else vm.userPw
        vm.ip = ip if ip else vm.ip
        vm.portSsh = rdp if rdp else vm.portSsh
        vm.portRdp = ssh if ssh else vm.portRdp

        # self.vms[vm_proto.virtualMachineId] = vm_proto  # TODO see issue:30
        open(new_vm_file_path, 'w').write(str(vm))

    def _save_dataset(self, task_id, dataset_id=None, display_name=None, is_deprecated=None, is_confidential=None,
                      evaluator_id=None, overwrite=False):
        """ dataset_dir_path/task_id/dataset_id.prototext """
        new_dataset_file_path = self.datasets_dir_path / task_id / f'{dataset_id}.prototext'
        if not overwrite and new_dataset_file_path.exists():
            raise TiraModelWriteError(f"Failed to write dataset, dataset exists and overwrite is not allowed here")
        elif overwrite and new_dataset_file_path.exists():
            ds = Parse(open(new_dataset_file_path, "r").read(), modelpb.Dataset())
        else:
            ds = modelpb.Dataset()

        ds.datasetId = dataset_id if dataset_id else ds.datasetId
        ds.displayName = display_name if display_name else ds.displayName
        ds.evaluatorId = evaluator_id if evaluator_id else ds.evaluatorId
        ds.isDeprecated = is_deprecated if is_deprecated else ds.isDeprecated
        ds.isConfidential = is_confidential if is_confidential else ds.isConfidential

        (self.datasets_dir_path / task_id).mkdir(exist_ok=True, parents=True)
        open(new_dataset_file_path, 'w').write(str(ds))
        # self.datasets[dataset_proto.datasetId] = dataset_proto TODO

    def _save_review(self, dataset_id, vm_id, run_id, review):
        review_path = self.runs_dir_path / dataset_id / vm_id / run_id
        open(review_path / "run-review.prototext", 'w').write(str(review))
        open(review_path / "run-review.bin", 'wb').write(review.SerializeToString())

    def _save_softwares(self, task_id, vm_id, softwares):
        open(self.softwares_dir_path / task_id / vm_id / "softwares.prototext", "w+").write(str(softwares))

    def _save_run(self, dataset_id, vm_id, run_id, run):
        run_dir = (self.runs_dir_path / dataset_id / vm_id / run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        open(run_dir / "run.prototext", 'w').write(str(run))
        open(run_dir / "run.bin", 'wb').write(run.SerializeToString())

    # ------------------------------------------------------------
    # add methods to add new data to the model
    # ------------------------------------------------------------

    def _add_software(self, task_id, vm_id):
        # TODO crashes if software prototext does not exist.
        software = modelpb.Softwares.Software()
        s = self._load_softwares(task_id, vm_id)
        date = now()

        new_software_id = randomname.get_name()
        software.id = new_software_id
        software.count = ""
        software.command = ""
        software.workingDirectory = ""
        software.dataset = "None"
        software.run = ""
        software.creationDate = date
        software.lastEditDate = date
        software.deleted = False

        s.softwares.append(software)
        self._save_softwares(task_id, vm_id, s)
        modeldb.Software.objects.create(software_id=new_software_id,
                                        vm=modeldb.VirtualMachine.objects.get(vm_id=vm_id),
                                        task=modeldb.Task.objects.get(task_id=task_id),
                                        count="", command="", working_directory="",
                                        dataset="None", creation_date=date, last_edit_date=date)

    def _update_review(self, dataset_id, vm_id, run_id,
                       reviewer_id: str = None, review_date: str = None, has_errors: bool = None,
                       has_no_errors: bool = None, no_errors: bool = None, missing_output: bool = None,
                       extraneous_output: bool = None, invalid_output: bool = None, has_error_output: bool = None,
                       other_errors: bool = None, comment: str = None, published: bool = None, blinded: bool = None,
                       has_warnings: bool = False):
        """ updates the review specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """
        review = self.load_review(dataset_id, vm_id, run_id)

        def update(x, y):
            return y if y is not None else x

        review.reviewerId = update(review.reviewerId, reviewer_id)
        review.reviewDate = update(review.reviewDate, review_date)
        review.hasErrors = update(review.hasErrors, has_errors)
        review.hasWarnings = update(review.hasWarnings, has_warnings)
        review.hasNoErrors = update(review.hasNoErrors, has_no_errors)
        review.noErrors = update(review.noErrors, no_errors)
        review.missingOutput = update(review.missingOutput, missing_output)
        review.extraneousOutput = update(review.extraneousOutput, extraneous_output)
        review.invalidOutput = update(review.invalidOutput, invalid_output)
        review.hasErrorOutput = update(review.hasErrorOutput, has_error_output)
        review.otherErrors = update(review.otherErrors, other_errors)
        review.comment = update(review.comment, comment)
        review.published = update(review.published, published)
        review.blinded = update(review.blinded, blinded)

        self._save_review(dataset_id, vm_id, run_id, review)

    #########################################
    # Public Interface Methods
    ###################################

    @staticmethod
    def _vm_as_dict(vm):
        return {"vm_id": vm.vm_id, "user_password": vm.user_password, "roles": vm.roles,
                "host": vm.host, "admin_name": vm.admin_name, "admin_pw": vm.admin_pw,
                "ip": vm.ip, "ssh": vm.ssh, "rdp": vm.rdp, "archived": vm.archived}

    def get_vm(self, vm_id: str):
        vm = modeldb.VirtualMachine.objects.get(vm_id=vm_id)
        return self._vm_as_dict(vm)

    def get_users_vms(self):
        """ Return the users list. """
        return [self._vm_as_dict(vm) for vm in modeldb.VirtualMachine.objects.all()]

    def _task_to_dict(self, task):
        if task.organizer:
            org_name = task.organizer.name
            org_year = task.organizer.years
        else:
            org_name = ""
            org_year = ""

        return {"task_id": task.task_id, "task_name": task.task_name, "task_description": task.task_description,
                "organizer": org_name,
                "web": task.web,
                "year": org_year,
                "dataset_count": task.dataset_set.count(),
                "software_count": task.software_set.count(),
                "max_std_out_chars_on_test_data": task.max_std_out_chars_on_test_data,
                "max_std_err_chars_on_test_data": task.max_std_err_chars_on_test_data,
                "max_file_list_chars_on_test_data": task.max_file_list_chars_on_test_data,
                "command_placeholder": task.command_placeholder, "command_description": task.command_description,
                "dataset_label": task.dataset_label,
                "max_std_out_chars_on_test_data_eval": task.max_std_out_chars_on_test_data_eval,
                "max_std_err_chars_on_test_data_eval": task.max_std_err_chars_on_test_data_eval,
                "max_file_list_chars_on_test_data_eval": task.max_file_list_chars_on_test_data_eval}

    def _tasks_to_dict(self, tasks):
        for task in tasks:
            if not task.organizer:
                continue

            yield self._task_to_dict(task)

    def get_tasks(self) -> list:
        return list(self._tasks_to_dict(modeldb.Task.objects.select_related('organizer').all()))

    def get_task(self, task_id: str) -> dict:
        return self._task_to_dict(modeldb.Task.objects.select_related('organizer').get(task_id=task_id))

    def _dataset_to_dict(self, dataset):
        return {
            "display_name": dataset.display_name,
            "evaluator_id": dataset.evaluator.evaluator_id,
            "dataset_id": dataset.dataset_id,
            "is_confidential": dataset.is_confidential, "is_deprecated": dataset.is_deprecated,
            "year": dataset.released,
            "task": dataset.default_task.task_id,
            'organizer': dataset.default_task.organizer.name,
            "software_count": modeldb.Software.objects.filter(dataset__dataset_id=dataset.dataset_id).count(),
        }

    def get_dataset(self, dataset_id: str) -> dict:
        return self._dataset_to_dict(modeldb.Dataset.objects.select_related('default_task', 'evaluator')
                                     .get(dataset_id=dataset_id))

    def get_datasets(self) -> dict:
        """ Get a dict of dataset_id: dataset_json_descriptor """
        return {dataset.dataset_id: self._dataset_to_dict(dataset)
                for dataset in modeldb.Dataset.objects.select_related('default_task', 'evaluator').all()}

    def get_datasets_by_task(self, task_id: str, include_deprecated=False) -> list:
        """ return the list of datasets associated with this task_id
        @param task_id: id string of the task the dataset belongs to
        @param include_deprecated: Default False. If True, also returns datasets marked as deprecated.
        @return: a list of json-formatted datasets, as returned by get_dataset
        """
        return [self._dataset_to_dict(d.dataset)
                for d in modeldb.TaskHasDataset.objects.filter(task=task_id)
                if not (d.dataset.is_deprecated and not include_deprecated)]

    def get_organizer(self, organizer_id: str):
        organizer = modeldb.Organizers.objects.get(organizer_id=organizer_id)
        return {
            "organizer_id": organizer.organizer_id,
            "name": organizer.name,
            "years": organizer.years,
            "web": organizer.web,
        }

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

        def parse_vm_list(vm_list):
            for list_entry in vm_list:
                try:
                    list_entry = list_entry.split("\t")
                    yield [list_entry[0], list_entry[1].strip(), list_entry[2].strip() if len(list_entry) > 2 else '']
                except IndexError as e:
                    logger.error(e, list_entry)

        return list(parse_vm_list(open(self.vm_list_file, 'r')))

    @staticmethod
    def get_vms_by_dataset(dataset_id: str) -> list:
        """ return a list of vm_id's that have runs on this dataset """
        return [run.software.vm.vm_id for run in modeldb.Run.objects.select_related('input_dataset', 'software')
                .exclude(input_dataset=None)
                .filter(input_dataset__dataset_id=dataset_id)
                .exclude(software=None)
                .all()]

    @staticmethod
    def _run_as_dict(run):
        software = None
        if run.software:
            software = run.software.software_id
        elif run.evaluator:
            software = run.evaluator.evaluator_id

        return {"software": software,
                "run_id": run.run_id,
                "input_run_id": "" if not run.input_run else run.input_run.run_id,
                "dataset": run.input_dataset.dataset_id,
                "downloadable": run.downloadable}

    def get_run(self, dataset_id: str, vm_id: str, run_id: str, return_deleted: bool = False) -> dict:
        run = modeldb.Run.objects.select_related('software', 'input_dataset').get(run_id=run_id)

        if run.deleted and not return_deleted:
            return {}
        return self._run_as_dict(run)

    def get_vm_runs_by_dataset(self, dataset_id: str, vm_id: str, return_deleted: bool = False) -> list:
        return [self._run_as_dict(run) for run in
                modeldb.Run.objects.select_related('software', 'input_dataset')
                    .filter(input_dataset__dataset_id=dataset_id, software__vm__vm_id=vm_id)
                if (run.deleted or not return_deleted)]

    def _get_ordered_runs_from_reviews(self, reviews, vm_id, preloaded=True):
        """ yields all runs with reviews and their evaluation runs with reviews produced by software from a given vm
            evaluation runs (which have a run as input run) are yielded directly after the runs they use.

        @param reviews: a querySet of modeldb.Review objects to
        @param vm_id: the vm_id of the software
        @param preloaded: If False, do a new database request to get the evaluation runs.
            Otherwise assume they were preloaded
        """
        reviews_qs = reviews.filter(run__software__vm__vm_id=vm_id).all()
        for review in reviews_qs:
            yield {"run": self._run_as_dict(review.run),
                   "review": self._review_as_dict(review),
                   "reviewed": True if not review.has_errors and not review.has_no_errors
                                       and not review.has_warnings else False,
                   'published': review.published,
                   'blinded': review.blinded}
            r2 = reviews.filter(run__input_run__run_id=review.run.run_id).all() if preloaded \
                else modeldb.Review.objects.select_related('run').filter(run__input_run__run_id=review.run.run_id).all()

            for review2 in r2:
                yield {"run": self._run_as_dict(review2.run),
                       "review": self._review_as_dict(review2),
                       "reviewed": True if not review2.has_errors and not review2.has_no_errors
                                           and not review2.has_warnings else False,
                       'published': review2.published,
                       'blinded': review2.blinded}

    def get_vms_with_reviews(self, dataset_id: str):
        """ returns a list of dicts with:
         {"vm_id": vm_id,
         "runs": [{run, review}, ...],
         "unreviewed_count": unreviewed_count,
         "blinded_count": blinded_count,
         "published_count": published_count}
         """
        results = []
        reviews = modeldb.Review.objects.select_related('run', 'run__software', 'run__evaluator',
                                                        'run__input_run').filter(
            run__input_dataset__dataset_id=dataset_id).all()

        for vm_id in {values['run__software__vm__vm_id'] for values in reviews.values('run__software__vm__vm_id')}:
            if not vm_id:
                continue
            r = list(self._get_ordered_runs_from_reviews(reviews, vm_id))
            results.append({"vm_id": vm_id,
                            "runs": r,
                            "unreviewed_count": len([_['reviewed'] for _ in r if _['reviewed'] is True]),
                            "blinded_count": len([_['blinded'] for _ in r if _['blinded'] is True]),
                            "published_count": len([_['published'] for _ in r if _['published'] is True]),
                            })
        return results

    def get_vm_runs_by_task(self, task_id: str, vm_id: str, return_deleted: bool = False) -> list:
        """ returns a list of all the runs of a user over all datasets in json (as returned by _load_user_runs) """
        # TODO remove this line after the grpc callback (confirm_run_execute) updates the runs in the database
        # for thd in modeldb.TaskHasDataset.objects.select_related('dataset').filter(task__task_id=task_id):
        # dbops.parse_runs_for_vm(self.runs_dir_path, thd.dataset.dataset_id, vm_id)
        return [self._run_as_dict(run) for run in
                modeldb.Run.objects.select_related('software', 'input_dataset')
                    .filter(software__vm__vm_id=vm_id, input_dataset__default_task__task_id=task_id,
                            software__task__task_id=task_id)
                if (run.deleted or not return_deleted)]

    def get_evaluator(self, dataset_id, task_id=None):
        """ returns a dict containing the evaluator parameters:

        vm_id: id of the master vm running the evaluator
        host: ip or hostname of the host
        command: command to execute to run the evaluator. NOTE: contains variables the host needs to resolve
        working_dir: where to execute the command
        """
        evaluator = modeldb.Dataset.objects.get(dataset_id=dataset_id)
        master_vm = modeldb.VirtualMachineHasEvaluator.objects.filter(evaluator=evaluator)[0].vm

        return {"vm_id": master_vm.vm_id, "host": master_vm.host, "command": evaluator.evauator.command,
                "working_dir": evaluator.evauator.working_directory}

    @staticmethod
    def get_vm_evaluations_by_dataset(dataset_id, vm_id, only_public_results=True):
        """ Return a dict of run_id: evaluation_results for the given vm on the given dataset
            {run_id: {measure.key: measure.value for measure in evaluation.measure}}

        @param only_public_results: only return the measures for published datasets.
        """
        result = {}
        for run in modeldb.Run.objects.filter(software__vm__vm_id=vm_id, input_dataset__dataset_id=dataset_id,
                                              deleted=False):
            if only_public_results and modeldb.Review.objects.filter(run=run).exists():
                if not modeldb.Review.objects.get(run=run).published:
                    continue
            result[run.run_id] = {evaluation.measure_key: evaluation.measure_value
                                  for evaluation in run.evaluation_set.all()}
        return result

    def get_evaluations_with_keys_by_dataset(self, dataset_id, include_unpublished=False, round_floats=True):
        """
        :returns: a tuple (ev_keys, evaluation),
            ev-keys is a list of keys of the evaluation measure
            evaluation is a list of evaluations, each evaluation is a dict with
                {vm_id: str, run_id: str, measures: list}
        """

        def round_if_float(fl):
            if not round_floats:
                return fl
            try:
                return round(float(fl), 3)
            except ValueError:
                return fl

        def format_evalutation(r, ks, rev):
            for run in r:
                if run.run_id in exclude:
                    continue
                values = evaluations.filter(run__run_id=run.run_id).all()
                if not values.exists():
                    continue

                yield {"vm_id": run.input_run.software.vm.vm_id,
                       "run_id": run.run_id, 'published': rev.get(run__run_id=run.run_id).published,
                       'blinded': rev.get(run__run_id=run.run_id).blinded,
                       "measures": [
                           round_if_float(evaluations.filter(run__run_id=run.run_id, measure_key=k)[0].measure_value)
                           for k in ks]}

        runs = modeldb.Run.objects.filter(input_dataset=dataset_id).all()
        evaluations = modeldb.Evaluation.objects.select_related('run', 'run__software__vm').filter(
            run__input_dataset__dataset_id=dataset_id).all()
        keys = [k['measure_key'] for k in evaluations.values('measure_key').distinct()]
        reviews = modeldb.Review.objects.select_related('run').all()
        exclude = {review.run.run_id for review in reviews.filter(
            run__input_dataset__dataset_id=dataset_id, published=False, run__software=None).all()
                   if not include_unpublished}

        return keys, list(format_evalutation(runs, keys, reviews))

    def get_software_with_runs(self, task_id, vm_id):
        def _runs_by_software(software):
            reviews = modeldb.Review.objects.select_related("run", "run__software", "run__evaluator", "run__input_run",
                                                            "run__input_dataset").filter(run__software=software).all()
            for r in self._get_ordered_runs_from_reviews(reviews, vm_id, preloaded=False):
                run = r['run']
                run['review'] = r["review"]
                yield run

        return [{"software": self._software_to_dict(s),
                 "runs": list(_runs_by_software(s))
                 } for s in modeldb.Software.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, deleted=False)]

    @staticmethod
    def _review_as_dict(review):
        return {"reviewer": review.reviewer_id, "noErrors": review.no_errors,
                "missingOutput": review.missing_output,
                "extraneousOutput": review.extraneous_output, "invalidOutput": review.invalid_output,
                "hasErrorOutput": review.has_error_output, "otherErrors": review.other_errors,
                "comment": review.comment, "hasErrors": review.has_errors, "hasWarnings": review.has_warnings,
                "hasNoErrors": review.has_no_errors, "published": review.published, "blinded": review.blinded}

    def get_run_review(self, dataset_id: str, vm_id: str, run_id: str) -> dict:
        review = modeldb.Review.objects.get(run__run_id=run_id)
        return self._review_as_dict(review)

    def get_vm_reviews_by_dataset(self, dataset_id: str, vm_id: str) -> dict:
        return {review.run.run_id: self._review_as_dict(review)
                for review in modeldb.Review.objects.select_related('run').
                    filter(run__input_dataset__dataset_id=dataset_id, run__software__vm__vm_id=vm_id)}

    @staticmethod
    def _software_to_dict(software):
        return {"id": software.software_id, "count": software.count,
                "task_id": software.task.task_id, "vm_id": software.vm.vm_id,
                "command": software.command, "working_directory": software.working_directory,
                "dataset": software.dataset.dataset_id, "run": 0, "creation_date": software.creation_date,
                "last_edit": software.last_edit_date}

    def get_software(self, task_id, vm_id, software_id):
        """ Returns the software with the given name of a vm on a task """
        return self._software_to_dict(
            modeldb.Software.objects.get(vm__vm_id=vm_id, task__task_id=task_id, software_id=software_id))

    def get_software_by_task(self, task_id, vm_id):
        return [self._software_to_dict(sw)
                for sw in modeldb.Software.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, deleted=False)]

    def get_software_by_vm(self, task_id, vm_id):
        """ Returns the software of a vm on a task in json """
        return [self._software_to_dict(software)
                for software in modeldb.Software.objects.filter(vm__vm_id=vm_id, task__task_id=task_id, deleted=False)]

    def add_vm(self, vm_id, user_name, initial_user_password, ip, host, ssh, rdp):
        """ Add a new task to the database.
        This will not overwrite existing files and instead do nothing and return false
        """
        if self._save_vm(vm_id, user_name, initial_user_password, ip, host, ssh, rdp):
            try:
                modeldb.VirtualMachine.objects.create(vm_id=vm_id, user_password=initial_user_password,
                                                      roles='user', host=host, ip=ip, ssh=ssh, rdp=rdp)
            except IntegrityError as e:
                logger.exception(f"Failed to add new vm {vm_id} with ", e)
                raise TiraModelIntegrityError(e)

        raise TiraModelWriteError(f"Failed to write VM {vm_id}")

    def create_task(self, task_id, task_name, task_description, master_vm_id, organizer, website):
        """ Add a new task to the database.
         CAUTION: This function does not do any sanity checks and will OVERWRITE existing tasks
         TODO add max_std_out_chars_on_test_data, max_std_err_chars_on_test_data, max_file_list_chars_on_test_data, command_placeholder, command_description, dataset_label, max_std_out_chars_on_test_data_eval, max_std_err_chars_on_test_data_eval, max_file_list_chars_on_test_data_eval,          """
        if self._save_task(task_id, task_name, task_description, master_vm_id, organizer, website):
            try:
                vm, _ = modeldb.VirtualMachine.objects.get_or_create(vm_id=master_vm_id)
                modeldb.Task.objects.create(
                    task_id=task_id, task_name=task_name, task_description=task_description,
                    vm=vm, organizer=modeldb.Organizers.objects.get(organizer_id=organizer), web=website)
                return True
            except IntegrityError as e:
                logger.exception(f"Failed to add new task {task_id} with ", e)
                raise TiraModelIntegrityError(e)

        raise TiraModelWriteError(f"Failed to write task {task_id}")

    def add_dataset(self, task_id, dataset_id, dataset_type, dataset_name):
        """ TODO documentation
        """
        # update task_dir_path/task_id.prototext:
        dataset_id = f"{dataset_id}-{dataset_type}"

        try:
            for_task = modeldb.Task.objects.get(task_id=task_id)
        except modeldb.Task.DoesNotExist:
            raise KeyError(f"No task with id {task_id}")

        # create new dataset_dir_path/task_id/dataset_id.prototext
        self._save_dataset(task_id, dataset_id, dataset_name, False, True if dataset_type == 'test' else False)

        ds, _ = modeldb.Dataset.objects.update_or_create(dataset_id=dataset_id, defaults={
            'default_task': for_task,
            'display_name': dataset_name,
            'is_confidential': True if dataset_type == 'test' else False,
            'released': str(dt.now())
        })

        thds = modeldb.TaskHasDataset.objects.select_related('dataset').filter(task__task_id=task_id)
        append_training = []
        append_test = []
        if dataset_type == 'test' and dataset_id not in {thd.dataset.dataset_id for thd in thds if thd.is_test}:
            append_test.append(dataset_id)
            modeldb.TaskHasDataset.objects.create(task=for_task, dataset=ds, is_test=True)
        elif dataset_type in {'training', 'dev'} and dataset_id not in {thd.dataset.dataset_id for thd in thds if
                                                                        not thd.is_test}:
            append_training = [dataset_id]
            modeldb.TaskHasDataset.objects.create(task=for_task, dataset=ds, is_test=False)
        elif dataset_type not in {'training', 'dev', 'test'}:
            raise KeyError("dataset type must be test, training, or dev")
        self._save_task(task_id, None, None, None, None, None, append_training_datasets=append_training,
                        append_test_datasets=append_test, overwrite=True)

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

    def _append_evaluator(self, vm_id, evaluator_id, command, working_directory, measures):
        vm_file_path = self.vm_dir_path / f'{vm_id}.prototext'
        if not vm_file_path.exists():
            raise TiraModelWriteError(f"Failed to _append_evaluator, vm file does not exist")
        vm = Parse(open(vm_file_path).read(), modelpb.VirtualMachine())

        ev = modelpb.Evaluator()
        ev.evaluatorId = evaluator_id
        ev.command = command
        ev.workingDirectory = working_directory
        ev.measures = ",".join([x[0].strip('\r') for x in measures])
        ev.measureKeys.extend([x[1].strip('\r') for x in measures])
        vm.evaluators.append(ev)

        # self.vms[vm_proto.virtualMachineId] = vm_proto  # TODO see issue:30
        open(vm_file_path, 'w').write(str(vm))

    def add_evaluator(self, vm_id, task_id, dataset_id, dataset_type, command, working_directory, measures):
        """ TODO documentation """
        evaluator_id = f"{dataset_id}-evaluator"
        dataset_id = f"{dataset_id}-{dataset_type}"

        # get_or_create
        ev = modeldb.Evaluator.objects.update_or_create(evaluator_id=evaluator_id, defaults={
            'command': command,
            'working_directory': working_directory,
            'measures': ", ".join(measures)
        })

        if not modeldb.VirtualMachineHasEvaluator.objects.filter(evaluator_evaluator_id=evaluator_id,
                                                                 vm__vm_id=vm_id).exists():
            self._append_evaluator(vm_id, evaluator_id, command, working_directory, measures)

        # update dataset_id.prototext
        modeldb.Dataset.objects.filter(dataset_id).update(evaluator=ev)
        self._save_dataset(task_id, evaluator_id=evaluator_id, overwrite=True)

    def add_software(self, task_id: str, vm_id: str):
        self._add_software(task_id, vm_id)

    def update_software(self, task_id, vm_id, software_id, command: str = None, working_directory: str = None,
                        dataset: str = None, run: str = None, deleted: bool = False):
        def update(x, y):
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
                    command=software.command, working_directory=software.workingDirectory,
                    deleted=software.deleted,
                    dataset=modeldb.Dataset.objects.get(dataset_id=software.dataset),
                    last_edit_date=date)
                if run:
                    modeldb.SoftwareHasInputRun.objects.filter(
                        software=modeldb.Software.objects.get(software_id=software_id, vm__vm_id=vm_id),
                        input_run=modeldb.Run.objects.get(run_id=run))

                # software_list = [user_software for user_software in s.softwares if not user_software.deleted]
                # self.software[f"{task_id}${vm_id}"] = software_list
                return software

        return False

    def update_review(self, dataset_id, vm_id, run_id,
                      reviewer_id: str = None, review_date: str = None, has_errors: bool = None,
                      has_no_errors: bool = None, no_errors: bool = None, missing_output: bool = None,
                      extraneous_output: bool = None, invalid_output: bool = None, has_error_output: bool = None,
                      other_errors: bool = None, comment: str = None, published: bool = None, blinded: bool = None,
                      has_warnings: bool = False) -> bool:
        """ updates the review specified by dataset_id, vm_id, and run_id with the values given in the parameters.
        Required Parameters are also required in the function
        """
        try:
            self._update_review(dataset_id, vm_id, run_id, reviewer_id, review_date, has_errors, has_no_errors,
                                no_errors,
                                missing_output, extraneous_output, invalid_output, has_error_output,
                                other_errors, comment, published, blinded, has_warnings)
            return True
        except Exception as e:
            logger.exception(f"Exception while saving review ({dataset_id}, {vm_id}, {run_id}): {e}")
            return False

    def add_run(self, dataset_id, vm_id, run_id):
        """ Parses the specified run and adds it to the model. Does nothing if the run does not exist in the
        FileDB.
        Runs the auto reviewer to generate an initial review.
        Also loads evaluations if present
         """
        dbops.parse_run(self.runs_dir_path, dataset_id, vm_id, run_id)

    def update_run(self, dataset_id, vm_id, run_id, deleted: bool = None):
        """ updates the run specified by dataset_id, vm_id, and run_id with the values given in the parameters.
            Required Parameters are also required in the function
        """
        try:
            run = self._load_run(dataset_id, vm_id, run_id)

            def update(x, y):
                return y if y is not None else x

            run.deleted = update(run.deleted, deleted)
            modeldb.Run.objects.filter(run_id=run_id).update(deleted=run.deleted)

            self._save_run(dataset_id, vm_id, run_id, run)
        except Exception as e:
            raise TiraModelWriteError(f"Exception while saving run ({dataset_id}, {vm_id}, {run_id})", e)

    # TODO add option to truly delete the software.
    def delete_software(self, task_id, vm_id, software_id):
        s = self._load_softwares(task_id, vm_id)
        found = False
        for software in s.softwares:
            if software.id == software_id:
                software.deleted = True
                found = True
        # software_list = [software for software in s.softwares if not software.deleted]
        # self.software[f"{task_id}${vm_id}"] = software_list
        self._save_softwares(task_id, vm_id, s)
        modeldb.Software.objects.filter(software_id=software_id, vm__vm_id=vm_id).delete()

        return found

    def delete_run(self, dataset_id, vm_id, run_id):
        run_dir = Path(self.runs_dir_path / dataset_id / vm_id / run_id)
        rmtree(run_dir)
        modeldb.Run.objects.filter(run_id=run_id).delete()

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
