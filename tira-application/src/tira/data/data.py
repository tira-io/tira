"""
p.stat().st_mtime - change time
"""
from tira.proto import TiraClientWebMessages_pb2 as modelpb
from tira.proto import tira_host_pb2 as model_host
from google.protobuf.text_format import Parse
from tira.util import extract_year_from_dataset_id
from pathlib import Path
import tira.model as modeldb
import logging

MODEL_ROOT = Path("/mnt/ceph/tira/model")
TASKS_DIR_PATH = MODEL_ROOT / Path("tasks")
ORGANIZERS_FILE_PATH = MODEL_ROOT / Path("organizers/organizers.prototext")


logger = logging.getLogger("tira")


def index(organizers_file_path, users_file_path, vm_dir_path, tasks_dir_path,
          datasets_dir_path, softwares_dir_path, runs_dir_path):
    _parse_organizer_list(organizers_file_path)
    _parse_vm_list(users_file_path, vm_dir_path)
    _parse_dataset_list(datasets_dir_path)
    _parse_task_list(tasks_dir_path)
    _parse_software_list(softwares_dir_path)
    _parse_runs_evaluations(runs_dir_path)
    _parse_reviews(runs_dir_path)


def _parse_organizer_list(organizers_file_path):
    """ Parse the PB Database and extract all hosts.
    :return: a dict {hostId: {"name", "years"}
    """
    organizers = modelpb.Hosts()
    Parse(open(organizers_file_path, "r").read(), organizers)
    for org in organizers.hosts:
        _, _ = modeldb.Organizer.objects.update_or_create(organizer_id=org.hostId,
                                                          name=org.name,
                                                          years=org.years,
                                                          web=org.web)


def _parse_vm_list(users_file_path, vm_dir_path):
    users = Parse(open(users_file_path, "r").read(), modelpb.Users())

    for user in users.users:
        try:
            vm = Parse(open(vm_dir_path / f"{user.userName}.prototext").read(), modelpb.VirtualMachine())
            vm2, _ = modeldb.VirtualMachine.objects.update_or_create(vm_id=user.userName, user_password=user.userPw,
                                                                   roles=user.roles, host=vm.host,
                                                                   admin_name=vm.adminName, admin_pw=vm.adminPw,
                                                                   ip=vm.ip, ssh=vm.portSsh, rdp=vm.portRdp)

            for evaluator in vm.evaluators:
                ev, _ = modeldb.Evaluator.objects.update_or_create(
                    evaluator_id=evaluator.evaluatorId,
                    command=evaluator.command,
                    working_directory=evaluator.workingDirectory,
                    measures=evaluator.measures,
                    is_deprecated=evaluator.is_deprecated)
                modeldb.VirtualMachineHasEvaluator.objects.update_or_create(evaluator=ev, vm=vm2)

        except FileNotFoundError as e:
            logger.exception(f"Could not find VM file for vm_id {user.userName}", e)
            _, _ = modeldb.VirtualMachine.objects.update_or_create(vm_id=user.userName, user_password=user.userPw,
                                                                   roles=user.roles)


def _parse_task_list(tasks_dir_path):
    """ Parse the PB Database and extract all tasks.
    :return:
    1. a dict with the tasks {"taskId": {"name", "description", "dataset_count", "organizer", "year", "web"}}
    2. a dict with default tasks of datasets {"dataset_id": "task_id"}
    """
    logger.info('loading tasks')
    for task_path in tasks_dir_path.glob("*"):
        task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
        vm, _ = modeldb.VirtualMachine.objects.get_or_create(vm_id=task.virtualMachineId)
        organizer, _ = modeldb.Organizer.objects.get_or_create(organizer_id=task.hostId)
        t, _ = modeldb.Task.objects.update_or_create(
            task_id=task.taskId,
            task_name=task.taskName,
            task_description=task.taskDescription,
            vm=vm,
            organizer=organizer,
            web=task.web,
            max_std_out_chars_on_test_data=task.maxStdOutCharsOnTestData,
            max_std_err_chars_on_test_data=task.maxStdErrCharsOnTestData,
            max_file_list_chars_on_test_data=task.maxFileListCharsOnTestData,
            command_placeholder=task.commandPlaceholder,
            command_description=task.commandDescription,
            dataset_label=task.datasetLabel,
            max_std_out_chars_on_test_data_eval=task.maxStdOutCharsOnTestDataEval,
            max_std_err_chars_on_test_data_eval=task.maxStdErrCharsOnTestDataEval,
            max_file_list_chars_on_test_data_eval=task.maxFileListCharsOnTestDataEval)

        # allowed_servers
        for allowed_server in task.allowedServers:
            modeldb.AllowedServer.objects.update_or_create(
                task=t,
                server_address=allowed_server)
        # datasets
        for train_dataset in task.trainingDataset:
            dataset, _ = modeldb.Dataset.objects.get_or_create(dataset_id=train_dataset)
            dataset.default_task = t
            dataset.save()
            modeldb.TaskHasDataset.objects.update_or_create(
                task=t,
                dataset=dataset,
                is_test=False)

        for test_dataset in task.testDataset:
            dataset, _ = modeldb.Datasets.objects.get_or_create(dataset_id=test_dataset)
            dataset.default_task = t
            dataset.save()
            modeldb.TaskHasDataset.objects.update_or_create(
                task=t,
                dataset=dataset,
                is_test=True)


def _parse_dataset_list(datasets_dir_path):
    """ Load all the datasets from the Filedatabase.
    :return: a dict {dataset_id: dataset protobuf object}
    """
    logger.info('loading datasets')
    for dataset_file in datasets_dir_path.rglob("*.prototext"):
        dataset = Parse(open(dataset_file, "r").read(), modelpb.Dataset())
        evaluator, _ = modeldb.Evaluator.objects.get_or_create(evaluator_id=dataset.evaluatorId)
        modeldb.Dataset.objects.update_or_create(
            dataset_id=dataset.datasetId,
            display_name=dataset.displayName,
            evaluator=evaluator,
            is_confidential=dataset.isConfidential,
            is_deprecated=dataset.isDeprecated,
            data_server=dataset.dataServer,
            released=extract_year_from_dataset_id(dataset.datasetId)
        )


def _parse_software_list(softwares_dir_path):
    """ extract the software files. We invent a new id for the lookup since software has none:
      - <task_name>$<user_name>
    Afterwards sets self.software: a dict with the new key and a list of software objects as value
    """
    software = {}
    logger.info('loading softwares')
    for task_dir in softwares_dir_path.glob("*"):
        for user_dir in task_dir.glob("*"):
            s = Parse(open(user_dir / "softwares.prototext", "r").read(), modelpb.Softwares())
            for software in s.softwares:
                vm, _ = modeldb.VirtualMachine.get_or_create(vm_id=user_dir.stem)
                task, _ = modeldb.Task.get_or_create(task_id=task_dir.stem)
                modeldb.Software.objects.update_or_create(
                    software_id=software.id,
                    vm=vm,
                    task=task,
                    count=software.count,
                    command=software.command,
                    working_directory=software.workingDirectory,
                    dataset=software.dataset,
                    creation_date=software.creationDate,
                    last_edit_date=software.lastEditDate,
                    deleted=software.deleted,
                )
            software_list = [user_software for user_software in s.softwares if not user_software.deleted]
            software[f"{task_dir.stem}${user_dir.stem}"] = software_list


def _parse_runs_evaluations(runs_dir_path):
    for dataset_dir in runs_dir_path.glob("*"):
        for vm_dir in dataset_dir.glob("*"):
            for run_dir in vm_dir.glob('*'):
                if (run_dir / "run.prototext").exists():
                    run = Parse(open(run_dir / "run.prototext", "r").read(), modelpb.Run())
                    open(run_dir / "run.bin", 'wb').write(run.SerializeToString())
                elif (run_dir / "run.bin").exists():
                    run = modelpb.Run()
                    run.ParseFromString(open(run_dir / "run.bin", "rb").read())
                else:
                    continue
                vm = modeldb.VirtualMachine.objects.get(vm_id=vm_dir.stem)
                software = modeldb.Software.objects.get(software_id=run.softwareId, vm=vm)
                r, _ = modeldb.Run.objects.update_or_create(
                    run_id=run.runId,
                    software=software,
                    input_dataset=modeldb.Dataset.objects.get(dataset_id=run.inputDataset),
                    task=software.task,
                    downloadable=run.downloadable,
                    deleted=run.deleted,
                    access_token=run.accessToken)

                if not (run_dir / "output/evaluation.bin").exists():
                    continue

                evaluation = modelpb.Evaluation()
                evaluation.ParseFromString(open(run_dir / "output/evaluation.bin", "rb").read())
                for measure in evaluation.measure:
                    modeldb.Evaluation.objects.update_or_create(
                        measure_key=measure.key,
                        measure_value=measure.value,
                        run=r)


def _parse_reviews(runs_dir_path):
    for review_file in runs_dir_path.rglob('*run-review.bin'):
        review = modelpb.RunReview()
        review.ParseFromString(open(review_file, "rb").read())
        modeldb.Review.objects.update_or_create(
            run=modelpb.Run.objects.get_or_create(run_id=review.runId),
            reviewer_id=review.reviewerId,
            review_date=review.reviewDate,
            no_errors=review.noErrors,
            missing_output=review.missingOutput,
            extraneous_output=review.extraneousOutput,
            invalid_output=review.invalidOutput,
            has_error_output=review.hasErrorOutput,
            other_errors=review.otherErrors,
            comment=review.comment,
            has_errors=review.hasErrors,
            has_warnings=review.hasWarnings,
            has_no_errors=review.hasNoErrors,
            published=review.published,
            blinded=review.blinded)

        return review