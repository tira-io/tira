"""
These methods are utilities to parse Tira's Model from the protobuf files into a database.
"""

import logging
from typing import TYPE_CHECKING

from google.protobuf.text_format import Parse
from tqdm import tqdm

from .. import model as modeldb
from ..proto import TiraClientWebMessages_pb2 as modelpb
from ..util import auto_reviewer, extract_year_from_dataset_id

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional

logger = logging.getLogger("tira")


def _parse_run(run_id: str, task_id: str, run_proto: modelpb.Run, vm: str, dataset: str) -> modeldb.Run:
    def __get_docker_software() -> "Optional[modeldb.DockerSoftware]":
        if "docker-software-" not in run_proto.softwareId:
            return None
        try:
            docker_software_id = str(int(run_proto.softwareId.split("docker-software-")[-1]))
            return modeldb.DockerSoftware.objects.get(docker_software_id=docker_software_id)
        except modeldb.DockerSoftware.DoesNotExist:
            logger.exception(f"Run {run_id} lists a docker-software {run_proto.softwareId}, but None exists.")
        return None

    def __get_upload() -> "Optional[modeldb.Upload]":
        if "upload" not in run_proto.softwareId:
            return None
        try:
            upload, _ = modeldb.Upload.objects.get_or_create(vm=vm, task=modeldb.Task.objects.get(task_id=task_id))
            return upload
        except modeldb.Upload.DoesNotExist:
            logger.exception(f"Run {run_id} lists an upload software {run_proto.softwareId}, but None exists.")
        except modeldb.Upload.MultipleObjectsReturned:
            logger.exception(
                f"Run {run_id} lists multiple upload softwares {run_proto.softwareId}, but multiple exists."
            )

        return None

    def __get_evaluator() -> "Optional[modeldb.Evaluator]":
        if "eval" not in run_proto.softwareId:
            return None
        try:
            return modeldb.Evaluator.objects.get(evaluator_id=run_proto.softwareId)
        except modeldb.Evaluator.DoesNotExist:
            logger.exception(f"Run {run_id} lists an evaluation software {run_proto.softwareId}, but None exists.")

        return None

    def __get_software() -> "Optional[modeldb.Software]":
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


def _parse_review(run_dir: "Path", run: modeldb.Run) -> None:
    review_file = run_dir / "run-review.bin"

    # AutoReviewer action here
    if not review_file.exists():
        review = auto_reviewer(run_dir, run_dir.stem)
        (run_dir / "run-review.prototext").write_text(str(review))
        (run_dir / "run-review.bin").write_bytes(review.SerializeToString())
    else:
        review = modelpb.RunReview()
        review.ParseFromString(review_file.read_bytes())

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


def _parse_evalutions(run_dir: "Path", run: modeldb.Run) -> None:
    if (run_dir / "output/evaluation.prototext").exists() and not (run_dir / "output/evaluation.bin").exists():
        evaluation = Parse((run_dir / "output/evaluation.prototext").read_bytes(), modelpb.Evaluation())
        (run_dir / "output" / "evaluation.bin").write_bytes(evaluation.SerializeToString())

    # parse the runs
    if (run_dir / "output/evaluation.bin").exists():
        evaluation = modelpb.Evaluation()
        evaluation.ParseFromString((run_dir / "output/evaluation.bin").read_bytes())
        for measure in evaluation.measure:
            modeldb.Evaluation.objects.update_or_create(measure_key=measure.key, run=run, measure_value=measure.value)


def parse_runs_for_vm(runs_dir_path: "Path", dataset_id: str, vm_id: str, verbose: bool = False) -> None:
    vm_dir = runs_dir_path / dataset_id / vm_id
    for run_dir in tqdm(vm_dir.glob("*"), desc=f"{vm_id}"):
        try:
            result = parse_run(runs_dir_path, dataset_id, vm_id, run_dir.stem)
            if verbose:
                print(result)
        except Exception as e:
            logger.exception(e)


def parse_run(runs_dir_path: "Path", dataset_id: str, vm_id: str, run_id: str) -> str:
    run_dir = runs_dir_path / dataset_id / vm_id / run_id
    return_message = ""

    # Error correction: normalize the proto files that are parsed
    # Skip this run if there is no run file
    if (run_dir / "run.prototext").exists():
        run_proto = Parse((run_dir / "run.prototext").read_bytes(), modelpb.Run())
        (run_dir / "run.bin").write_bytes(run_proto.SerializeToString())
    elif (run_dir / "run.bin").exists():
        run_proto = modelpb.Run()
        run_proto.ParseFromString((run_dir / "run.bin").read_bytes())
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
        logger.exception(msg, exc_info=e)
        return msg

    # Error Correction: Skip runs where Dataset no not exist anymore
    try:
        dataset = modeldb.Dataset.objects.get(dataset_id=run_proto.inputDataset)
    except modeldb.Dataset.DoesNotExist as e:
        # If the dataset was deleted, but there are still runs left.
        msg = f"Skip run {run_id}: Dataset {run_proto.inputDataset} does not exist {e}"
        logger.exception(msg, exc_info=e)
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
        logger.exception(msg, exc_info=e)
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
