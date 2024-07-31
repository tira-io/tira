"""
These methods are utilities to parse Tira's Model from the protobuf files into a database.
"""

import logging
from pathlib import Path

from google.protobuf.text_format import Parse
from tqdm import tqdm

import tira.model as modeldb
from tira.proto import TiraClientWebMessages_pb2 as modelpb
from tira.util import auto_reviewer, extract_year_from_dataset_id

logger = logging.getLogger("tira")


def index(
    organizers_file_path,
    users_file_path,
    vm_dir_path,
    tasks_dir_path,
    datasets_dir_path,
    softwares_dir_path,
    runs_dir_path,
):
    _parse_organizer_list(organizers_file_path)
    _parse_vm_list(users_file_path, vm_dir_path)
    _parse_dataset_list(datasets_dir_path)
    _parse_task_list(tasks_dir_path)
    _parse_software_list(softwares_dir_path)
    _parse_runs_evaluations(runs_dir_path)
    pass


def reload_vms(users_file_path, vm_dir_path):
    _parse_vm_list(users_file_path, vm_dir_path)


def reload_datasets(datasets_dir_path):
    _parse_dataset_list(datasets_dir_path)


def reload_tasks(tasks_dir_path):
    _parse_task_list(tasks_dir_path)


def reload_runs(runs_dir_path, vm_id):
    parse_runs_for_vm(runs_dir_path, vm_id)

    for dataset_dir in runs_dir_path.glob("*"):
        dataset_id = dataset_dir.stem
        for vm_dir in dataset_dir.glob("*"):
            if vm_dir.stem != vm_id:
                continue
            parse_runs_for_vm(runs_dir_path, dataset_id, vm_id)


def _parse_organizer_list(organizers_file_path):
    """Parse the PB Database and extract all hosts.
    :return: a dict {hostId: {"name", "years"}
    """
    organizers = modelpb.Hosts()
    Parse(open(organizers_file_path, "r").read(), organizers)
    for org in organizers.hosts:
        _, _ = modeldb.Organizer.objects.update_or_create(
            organizer_id=org.hostId, defaults={"name": org.name, "years": org.years, "web": org.web}
        )


def _parse_vm_list(users_file_path, vm_dir_path):
    users = Parse(open(users_file_path, "r").read(), modelpb.Users())

    for user in users.users:
        try:
            vm = Parse(open(vm_dir_path / f"{user.userName}.prototext").read(), modelpb.VirtualMachine())
            vm2, _ = modeldb.VirtualMachine.objects.update_or_create(
                vm_id=user.userName,
                defaults={
                    "user_password": user.userPw,
                    "roles": user.roles,
                    "host": vm.host,
                    "admin_name": vm.adminName,
                    "admin_pw": vm.adminPw,
                    "ip": vm.ip,
                    "ssh": vm.portSsh,
                    "rdp": vm.portRdp,
                },
            )

            for evaluator in vm.evaluators:
                ev, _ = modeldb.Evaluator.objects.update_or_create(
                    evaluator_id=evaluator.evaluatorId,
                    defaults={
                        "command": evaluator.command,
                        "working_directory": evaluator.workingDirectory,
                        "measures": evaluator.measures,
                        "is_deprecated": evaluator.isDeprecated,
                    },
                )
                modeldb.VirtualMachineHasEvaluator.objects.update_or_create(evaluator=ev, vm=vm2)

        except FileNotFoundError:
            logger.exception(f"Could not find VM file for vm_id {user.userName}")
            _, _ = modeldb.VirtualMachine.objects.update_or_create(
                vm_id=user.userName, defaults={"user_password": user.userPw, "roles": user.roles}
            )


def _parse_task_list(tasks_dir_path):
    """Parse the PB Database and extract all tasks.
    :return:
    1. a dict with the tasks {"taskId": {"name", "description", "dataset_count", "organizer", "year", "web"}}
    2. a dict with default tasks of datasets {"dataset_id": "task_id"}
    """
    logger.info("loading tasks")
    for task_path in tasks_dir_path.glob("*"):
        task = Parse(open(task_path, "r").read(), modelpb.Tasks.Task())
        vm, _ = modeldb.VirtualMachine.objects.get_or_create(vm_id=task.virtualMachineId)
        organizer, _ = modeldb.Organizer.objects.get_or_create(organizer_id=task.hostId)
        t, _ = modeldb.Task.objects.update_or_create(
            task_id=task.taskId,
            defaults={
                "task_name": task.taskName,
                "task_description": task.taskDescription,
                "vm": vm,
                "organizer": organizer,
                "web": task.web,
                "max_std_out_chars_on_test_data": task.maxStdOutCharsOnTestData,
                "max_std_err_chars_on_test_data": task.maxStdErrCharsOnTestData,
                "max_file_list_chars_on_test_data": task.maxFileListCharsOnTestData,
                "command_placeholder": task.commandPlaceholder,
                "command_description": task.commandDescription,
                "dataset_label": task.datasetLabel,
                "max_std_out_chars_on_test_data_eval": task.maxStdOutCharsOnTestDataEval,
                "max_std_err_chars_on_test_data_eval": task.maxStdErrCharsOnTestDataEval,
                "max_file_list_chars_on_test_data_eval": task.maxFileListCharsOnTestDataEval,
            },
        )

        # allowed_servers
        for allowed_server in task.allowedServers:
            modeldb.AllowedServer.objects.update_or_create(task=t, server_address=allowed_server)
        # datasets
        for train_dataset in task.trainingDataset:
            dataset, _ = modeldb.Dataset.objects.update_or_create(
                dataset_id=train_dataset, defaults={"default_task": t}
            )
            # dataset.default_task = t
            # dataset.save()
            modeldb.TaskHasDataset.objects.update_or_create(task=t, dataset=dataset, defaults={"is_test": False})

        for test_dataset in task.testDataset:
            dataset, _ = modeldb.Dataset.objects.update_or_create(dataset_id=test_dataset, defaults={"default_task": t})
            modeldb.TaskHasDataset.objects.update_or_create(task=t, dataset=dataset, defaults={"is_test": True})


def _parse_dataset_list(datasets_dir_path):
    """Load all the datasets from the Filedatabase.
    :return: a dict {dataset_id: dataset protobuf object}
    """
    logger.info("loading datasets")
    for dataset_file in datasets_dir_path.rglob("*.prototext"):
        logger.info("Process dataset: " + str(dataset_file))
        dataset = Parse(open(dataset_file, "r").read(), modelpb.Dataset())
        evaluator, _ = modeldb.Evaluator.objects.get_or_create(evaluator_id=dataset.evaluatorId)
        modeldb.Dataset.objects.update_or_create(
            dataset_id=dataset.datasetId,
            defaults={
                "display_name": dataset.displayName,
                "evaluator": evaluator,
                "is_confidential": dataset.isConfidential,
                "is_deprecated": dataset.isDeprecated,
                "data_server": dataset.dataServer,
                "released": extract_year_from_dataset_id(dataset.datasetId),
            },
        )


def _parse_software_list(softwares_dir_path):
    """extract the software files. We invent a new id for the lookup since software has none:
      - <task_name>$<user_name>
    Afterwards sets self.software: a dict with the new key and a list of software objects as value
    """
    # software = {}
    logger.info("loading softwares")
    for task_dir in softwares_dir_path.glob("*"):
        for user_dir in task_dir.glob("*"):
            s = Parse(open(user_dir / "softwares.prototext", "r").read(), modelpb.Softwares())
            for software in s.softwares:
                vm, _ = modeldb.VirtualMachine.objects.get_or_create(vm_id=user_dir.stem)
                task, _ = modeldb.Task.objects.get_or_create(task_id=task_dir.stem)
                dataset, _ = modeldb.Dataset.objects.get_or_create(dataset_id=software.dataset)
                modeldb.Software.objects.update_or_create(
                    software_id=software.id,
                    vm=vm,
                    task=task,
                    defaults={
                        "count": software.count,
                        "command": software.command,
                        "working_directory": software.workingDirectory,
                        "dataset": dataset,
                        "creation_date": software.creationDate,
                        "last_edit_date": software.lastEditDate,
                        "deleted": software.deleted,
                    },
                )
            # software_list = [user_software for user_software in s.softwares if not user_software.deleted]
            # software[f"{task_dir.stem}${user_dir.stem}"] = software_list


def _parse_runs_evaluations(runs_dir_path):
    for dataset_dir in tqdm(runs_dir_path.glob("*")):
        dataset_id = dataset_dir.stem
        for vm_dir in tqdm(dataset_dir.glob("*"), desc=f"{dataset_id}"):
            vm_id = vm_dir.stem
            parse_runs_for_vm(runs_dir_path, dataset_id, vm_id)


def _parse_run(run_id, task_id, run_proto, vm, dataset):
    def __get_docker_software():
        if "docker-software-" not in run_proto.softwareId:
            return None
        try:
            docker_software_id = str(int(run_proto.softwareId.split("docker-software-")[-1]))
            return modeldb.DockerSoftware.objects.get(docker_software_id=docker_software_id)
        except modeldb.DockerSoftware.DoesNotExist:
            logger.exception(f"Run {run_id} lists a docker-software {run_proto.softwareId}, but None exists.")
        return None

    def __get_upload():
        if "upload" not in run_proto.softwareId:
            return None
        try:
            upload, _ = modeldb.Upload.objects.get_or_create(vm=vm, task=modeldb.Task.objects.get(task_id=task_id))
            return upload
        except modeldb.Upload.DoesNotExist:
            logger.exception(f"Run {run_id} lists an upload software {run_proto.softwareId}, but None exists.")

        return None

    def __get_evaluator():
        if "eval" not in run_proto.softwareId:
            return None
        try:
            return modeldb.Evaluator.objects.get(evaluator_id=run_proto.softwareId)
        except modeldb.Evaluator.DoesNotExist:
            logger.exception(f"Run {run_id} lists an evaluation software {run_proto.softwareId}, but None exists.")

        return None

    def __get_software():
        try:
            return modeldb.Software.objects.get(software_id=run_proto.softwareId, vm=vm, task__task_id=task_id)
        except modeldb.Software.DoesNotExist:
            logger.exception(f"Software {run_proto.softwareId} not found. Will not add this run.")

        return None

    docker_software = __get_docker_software()
    upload = __get_upload() if not docker_software else None
    evaluator = __get_evaluator() if not docker_software and not upload else None
    software = __get_software() if not docker_software and not upload and not evaluator else None

    if not docker_software and not upload and not evaluator and not software:
        logger.exception(f"Run {run_id} is dangling:{run_proto}")

    r, _ = modeldb.Run.objects.update_or_create(
        run_id=run_proto.runId,
        defaults={
            "software": software,
            "docker_software": docker_software,
            "evaluator": evaluator,
            "upload": upload,
            "input_dataset": dataset,
            "task": modeldb.Task.objects.get(task_id=task_id),
            "downloadable": run_proto.downloadable,
            "deleted": run_proto.deleted,
            "access_token": run_proto.accessToken,
        },
    )

    return r


def _parse_review(run_dir, run):
    review_file = run_dir / "run-review.bin"

    # AutoReviewer action here
    if not review_file.exists():
        review = auto_reviewer(run_dir, run_dir.stem)
        open(run_dir / "run-review.prototext", "w").write(str(review))
        open(run_dir / "run-review.bin", "wb").write(review.SerializeToString())
    else:
        review = modelpb.RunReview()
        review.ParseFromString(open(review_file, "rb").read())

    modeldb.Review.objects.update_or_create(
        run=run,
        defaults={
            "reviewer_id": review.reviewerId,
            "review_date": review.reviewDate,
            "no_errors": review.noErrors,
            "missing_output": review.missingOutput,
            "extraneous_output": review.extraneousOutput,
            "invalid_output": review.invalidOutput,
            "has_error_output": review.hasErrorOutput,
            "other_errors": review.otherErrors,
            "comment": review.comment,
            "has_errors": review.hasErrors,
            "has_warnings": review.hasWarnings,
            "has_no_errors": review.hasNoErrors,
            "published": review.published,
            "blinded": review.blinded,
        },
    )


def _parse_evalutions(run_dir, run):
    if (run_dir / "output/evaluation.prototext").exists() and not (run_dir / "output/evaluation.bin").exists():
        evaluation = Parse(open(run_dir / "output/evaluation.prototext", "r").read(), modelpb.Evaluation())
        open(run_dir / "output" / "evaluation.bin", "wb").write(evaluation.SerializeToString())

    # parse the runs
    if (run_dir / "output/evaluation.bin").exists():
        evaluation = modelpb.Evaluation()
        evaluation.ParseFromString(open(run_dir / "output/evaluation.bin", "rb").read())
        for measure in evaluation.measure:
            modeldb.Evaluation.objects.update_or_create(measure_key=measure.key, run=run, measure_value=measure.value)


def parse_runs_for_vm(runs_dir_path, dataset_id, vm_id, verbose=False):
    vm_dir = runs_dir_path / dataset_id / vm_id
    for run_dir in tqdm(vm_dir.glob("*"), desc=f"{vm_id}"):
        try:
            result = parse_run(runs_dir_path, dataset_id, vm_id, run_dir.stem)
            if verbose:
                print(result)
        except Exception as e:
            logger.exception(e)


def parse_run(runs_dir_path, dataset_id, vm_id, run_id):
    run_dir = runs_dir_path / dataset_id / vm_id / run_id
    return_message = ""

    # Error correction: normalize the proto files that are parsed
    # Skip this run if there is no run file
    if (run_dir / "run.prototext").exists():
        run_proto = Parse(open(run_dir / "run.prototext", "r").read(), modelpb.Run())
        open(run_dir / "run.bin", "wb").write(run_proto.SerializeToString())
    elif (run_dir / "run.bin").exists():
        run_proto = modelpb.Run()
        run_proto.ParseFromString(open(run_dir / "run.bin", "rb").read())
    else:
        msg = f'Skip run {run_id}: No "run.prototext" or "run.bin" exists in {run_dir}'
        logger.exception(msg)
        return msg

    # Error Correction: Skip runs where VMs no not exist anymore
    try:
        vm = modeldb.VirtualMachine.objects.get(vm_id=vm_id)
    except modeldb.VirtualMachine.DoesNotExist as e:
        # If the vm was deleted but runs still exist, we land here. We skip indexing these runs.
        msg = f"Skip run {run_id}: VM {vm_id} does not exist"
        logger.exception(msg, e)
        return msg

    # Error Correction: Skip runs where Dataset no not exist anymore
    try:
        dataset = modeldb.Dataset.objects.get(dataset_id=run_proto.inputDataset)
    except modeldb.Dataset.DoesNotExist as e:
        # If the dataset was deleted, but there are still runs left.
        msg = f"Skip run {run_id}: Dataset {run_proto.inputDataset} does not exist {e}"
        logger.exception(msg, e)
        return msg

    # Error Correction. If run files dont add a task_id (which is optional), we use the default task of the dataset
    task_id = run_proto.taskId
    if not task_id or task_id == "None":
        task_id = dataset.default_task.task_id

    # here we create the run
    run = None
    try:
        run = _parse_run(run_id, task_id, run_proto, vm, dataset)
        return_message += f"|Run added: {run}|"

    except Exception as e:
        msg = f"Skip run {run_id}: Creation of run had an unexpected ErrorRun: {run_proto}"
        logger.exception(msg, e)
        return msg

    # If this run has an input run (i.e. it's an evaluation) we set the reference here.
    # The input_run may be parsed later
    if run_proto.inputRun:
        input_run, _ = modeldb.Run.objects.update_or_create(run_id=run_proto.inputRun)
        run.input_run = input_run
        run.save()
        return_message += "|Updated input_run of run |"

    # parse the reviews
    _parse_review(run_dir, run)
    return_message += "|Run updated during parsing of reviews|"

    _parse_evalutions(run_dir, run)

    return return_message
