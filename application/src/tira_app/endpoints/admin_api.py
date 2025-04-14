import datetime as dt
import hashlib
import json
import logging
import os
import tempfile
import traceback
import zipfile
from http import HTTPStatus
from os import PathLike
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseNotAllowed, JsonResponse
from slugify import slugify

from .. import model as modeldb
from .. import tira_model as model
from ..authentication import auth
from ..checks import check_conditional_permissions, check_permissions, check_resources_exist
from ..git_runner import check_that_git_integration_is_valid
from ..ir_datasets_loader import run_irds_command
from .v1._datasets import download_mirrored_resource

if TYPE_CHECKING:
    from typing import Any, Optional, Union

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("tira")

logger.info("ajax_routes: Logger active")


def _handle_get_model_exceptions(func):
    def decorate(request, *args, **kwargs):
        if request.method == "GET":
            try:
                msg = func(*args, **kwargs)
                return JsonResponse({"status": 0, "message": msg}, status=HTTPStatus.OK)
            except Exception as e:
                logger.exception(f"{func.__name__} failed with {e}", exc_info=e)
                return JsonResponse(
                    {"status": 1, "message": f"{func.__name__} failed with {e}"},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

        return JsonResponse({"status": 1, "message": f"{request.method} is not allowed."}, status=HTTPStatus.FORBIDDEN)

    return decorate


@check_permissions
@_handle_get_model_exceptions
def admin_reload_vms() -> str:
    model.reload_vms()
    return "VM data was reloaded successfully"


@check_permissions
@_handle_get_model_exceptions
def admin_reload_datasets() -> str:
    model.reload_datasets()
    return "Dataset data was reloaded successfully"


@check_permissions
@_handle_get_model_exceptions
def admin_reload_tasks() -> str:
    model.reload_tasks()
    return "Task data was reloaded successfully"


@check_permissions
def admin_create_vm(request: "HttpRequest") -> "HttpResponse":  # TODO implement
    """Hook for create_vm posts. Responds with json objects indicating the state of the create process."""

    if request.method == "POST":
        data = json.loads(request.body)

        return JsonResponse({"status": 0, "message": f"Not implemented yet, received: {data}"})

    return JsonResponse({"status": 1, "message": "GET is not implemented for vm create"})


@check_permissions
def admin_archive_vm(request: "HttpRequest") -> "HttpResponse":
    return JsonResponse({"status": 1, "message": "Not implemented"}, status=HTTPStatus.NOT_IMPLEMENTED)


@check_permissions
def admin_modify_vm(request: "HttpRequest") -> "HttpResponse":
    if request.method == "POST":
        data = json.loads(request.body)

        return JsonResponse({"status": 0, "message": f"Not implemented yet, received: {data}"})

    return JsonResponse({"status": 1, "message": "GET is not implemented for modify vm"})


@check_permissions
def admin_create_task(request: "HttpRequest", organizer_id: str) -> "HttpResponse":
    """Create an entry in the model for the task. Use data supplied by a model.
    Return a json status message."""

    if request.method == "POST":
        data = json.loads(request.body)

        task_id = data["task_id"]
        featured = data["featured"]
        master_vm_id = data.get("master_vm_id", "princess-knight")  # dummy default VM
        master_vm_id = master_vm_id if master_vm_id else "princess-knight"  # default dummy vm
        require_registration = data["require_registration"]
        require_groups = data["require_groups"]
        restrict_groups = data["restrict_groups"]

        if not model.organizer_exists(organizer_id):
            return JsonResponse({"status": 1, "message": f"Organizer with ID {organizer_id} does not exist"})
        if model.task_exists(task_id):
            return JsonResponse({"status": 1, "message": f"Task with ID {task_id} already exist"})
        if not model.vm_exists(master_vm_id):
            return JsonResponse({"status": 1, "message": f"VM with ID {master_vm_id} does not exist"})

        new_task = model.create_task(
            task_id,
            data["name"],
            data["description"],
            featured,
            master_vm_id,
            organizer_id,
            data["website"],
            require_registration,
            require_groups,
            restrict_groups,
            help_command=data["help_command"],
            help_text=data["help_text"],
            allowed_task_teams=data["task_teams"],
        )

        new_task_str = json.dumps(new_task, cls=DjangoJSONEncoder)
        return JsonResponse(
            {"status": 0, "context": new_task_str, "message": f"Created Task with Id: {data['task_id']}"}
        )

    return JsonResponse(
        {"status": 1, "message": "GET is not implemented for admin_create_task"}, status=HTTPStatus.NOT_IMPLEMENTED
    )


@check_permissions
@check_resources_exist("json")
def admin_edit_task(request: "HttpRequest", task_id: str) -> "HttpResponse":
    """Edit a task. Expects a POST message with all task data."""
    if request.method == "POST":
        data = json.loads(request.body)
        organizer = data["organizer"]
        featured = data["featured"]
        master_vm_id = data.get("master_vm_id", "princess-knight")  # default dummy vm
        master_vm_id = master_vm_id if master_vm_id else "princess-knight"  # default dummy vm
        require_registration = data["require_registration"]
        require_groups = data["require_groups"]
        restrict_groups = data["restrict_groups"]

        if not model.organizer_exists(organizer):
            return JsonResponse({"status": 1, "message": f"Organizer with ID {organizer} does not exist"})
        if not model.vm_exists(master_vm_id):
            return JsonResponse({"status": 1, "message": f"VM with ID {master_vm_id} does not exist"})

        task = model.edit_task(
            task_id,
            data["name"],
            data["description"],
            featured,
            master_vm_id,
            organizer,
            data["website"],
            require_registration,
            require_groups,
            restrict_groups,
            help_command=data["help_command"],
            help_text=data["help_text"],
            allowed_task_teams=data["task_teams"],
            is_ir_task=data.get("is_information_retrieval_task", False),
            irds_re_ranking_image=data.get("irds_re_ranking_image", ""),
            irds_re_ranking_command=data.get("irds_re_ranking_command", ""),
            irds_re_ranking_resource=data.get("irds_re_ranking_resource", ""),
        )

        return JsonResponse(
            {
                "status": 0,
                "context": json.dumps(task, cls=DjangoJSONEncoder),
                "message": f"Edited Task with Id: {task_id}",
            }
        )

    return JsonResponse({"status": 1, "message": "GET is not implemented for edit task"})


@check_permissions
@check_resources_exist("json")
def admin_delete_task(request: "HttpRequest", task_id: str) -> "HttpResponse":
    model.delete_task(task_id)
    return JsonResponse({"status": 0, "message": f"Deleted task {task_id}"})


def _file_listing(path: PathLike, title: str) -> "dict[str, Union[str, int, dict, list]]":
    path = Path(path)
    children: list[dict[str, Union[str, int, dict, list]]] = []
    if path and path.is_dir():
        for f in os.listdir(path):
            if len(children) > 5:
                children.append({"title": "..."})
                break

            if (path / f).is_dir():
                c = _file_listing(path / f, str(f))["children"]
                children.append({"title": f, "children": c})
            else:
                md5 = hashlib.md5((path / f).read_bytes()).hexdigest()
                size = os.path.getsize(path / f)
                children.append({"title": f"{f} (size: {size}; md5sum: {md5})", "size": size, "md5sum": md5})

    current_item: dict[str, Union[str, int, dict, list]] = {"title": title}
    if len(children) > 0:
        current_item["children"] = children

    return current_item


def update_file_listing_for_dataset(dataset_id: str) -> None:
    dataset = modeldb.Dataset.objects.get(dataset_id=dataset_id)
    dataset_type = "test" if dataset.is_confidential else "training"
    task_id = model.get_dataset(dataset_id)["task"]
    listing = []

    for k, v in [("", "$inputDir"), ("-truth", "$inputDataset")]:
        path = model.model.data_path / f"{dataset_type}-datasets{k}" / task_id / dataset_id
        listing.append(_file_listing(path, v))

    dataset.file_listing = json.dumps(listing)
    dataset.save()


@check_permissions
def admin_add_dataset(request: "HttpRequest", task_id: str) -> "HttpResponse":
    """Create an entry in the model for the task. Use data supplied by a model.
    Return a json status message."""
    if request.method == "POST":
        data = json.loads(request.body)

        if not all(k in data.keys() for k in ["dataset_id", "name", "task"]):
            return JsonResponse({"status": 1, "message": "Error: Task, dataset name, and dataset ID must be set."})

        dataset_id_prefix = data["dataset_id"]
        dataset_name = data["name"]
        task_id_from_data = data["task"]

        if task_id_from_data != task_id:
            from django.http import HttpResponseNotAllowed

            return HttpResponseNotAllowed("Access forbidden.")

        upload_name = data.get("upload_name", "predictions.jsonl")
        command = data.get("evaluator_command", "")
        working_directory = data.get("evaluator_working_directory", "")
        measures = data.get("evaluation_measures", "")

        is_git_runner = data.get("is_git_runner", False)
        git_runner_image = data.get("git_runner_image", "")
        git_runner_command = data.get("git_runner_command", "")
        git_repository_id = data.get("git_repository_id", "")

        irds_docker_image = data.get("irds_docker_image", None)
        irds_docker_image = None if not irds_docker_image else irds_docker_image
        irds_import_command = data.get("irds_import_command", None)
        irds_import_command = None if not irds_import_command else irds_import_command
        irds_import_truth_command = data.get("irds_import_truth_command", None)
        irds_import_truth_command = None if not irds_import_truth_command else irds_import_truth_command

        try:
            dataset_format, dataset_format_configuration = _format_and_configuration(data, "format")
        except Exception as e:
            logger.info(e)
            return JsonResponse(
                {"status": 1, "message": "The configuration of the dataset format is invalid:" + str(e.args[0])}
            )

        try:
            truth_format, truth_format_configuration = _format_and_configuration(data, "truth_format")
        except Exception as e:
            logger.info(e)
            return JsonResponse(
                {"status": 1, "message": "The configuration of the truth format is invalid:" + str(e.args[0])}
            )

        try:
            trusted_evaluation = _evaluator_config(data)
        except Exception as e:
            return JsonResponse({"status": 1, "message": e.args[0]})

        description = data.get("description", None)
        chatnoir_id = data.get("chatnoir_id", None)
        ir_datasets_id = data.get("ir_datasets_id", None)

        systemUrlHandle = data.get("systemUrlHandle")
        truthUrlHandle = data.get("truthUrlHandle")
        system_inputs = None
        truth_data = None
        if systemUrlHandle is not None or truthUrlHandle is not None:
            if systemUrlHandle is None or truthUrlHandle is None:
                return JsonResponse(
                    {
                        "status": 1,
                        "message": "If the dataset is to be downloaded, you must provide both,"
                        + "a URL for the system inputs and for the ground truth data, but one is missing. "
                        + f"I got systemUrlHandle: '{systemUrlHandle}' and truthUrlHandle: '{truthUrlHandle}'.",
                    }
                )

            for url in [systemUrlHandle, truthUrlHandle]:
                if url and "://zenodo.org" not in url:
                    return JsonResponse(
                        {
                            "status": 1,
                            "message": "Only Zenodo is currently enabled as source for data imports, "
                            + f"but I got '{url}' as import url.",
                        }
                    )

            system_inputs = download_mirrored_resource(systemUrlHandle, "Zenodo")

            if truthUrlHandle:
                truth_data = download_mirrored_resource(truthUrlHandle, "Zenodo")
            else:
                truth_data = None

        if not data.get("use_existing_repository", True):
            git_repository_id = model.get_git_integration(task_id=task_id).create_task_repository(task_id)

        master_vm_id = model.get_task(task_id)["master_vm_id"]

        if not model.task_exists(task_id):
            return JsonResponse({"status": 1, "message": f"Task with ID {task_id} does not exist"})
        if data["type"] not in {"test", "training"}:
            return JsonResponse({"status": 1, "message": "Dataset type must be 'test' or 'training'"})

        try:
            if data["type"] == "training":
                ds, paths = model.add_dataset(
                    task_id,
                    dataset_id_prefix,
                    "training",
                    dataset_name,
                    upload_name,
                    irds_docker_image,
                    irds_import_command,
                    irds_import_truth_command,
                    dataset_format,
                    description,
                    chatnoir_id,
                    ir_datasets_id,
                    truth_format,
                    dataset_format_configuration,
                    truth_format_configuration,
                )
            elif data["type"] == "test":
                ds, paths = model.add_dataset(
                    task_id,
                    dataset_id_prefix,
                    "test",
                    dataset_name,
                    upload_name,
                    irds_docker_image,
                    irds_import_command,
                    irds_import_truth_command,
                    dataset_format,
                    description,
                    chatnoir_id,
                    ir_datasets_id,
                    truth_format,
                    dataset_format_configuration,
                    truth_format_configuration,
                )

            model.add_evaluator(
                master_vm_id,
                task_id,
                ds["dataset_id"],
                command,
                working_directory,
                not measures,
                is_git_runner,
                git_runner_image,
                git_runner_command,
                git_repository_id,
                trusted_evaluation,
            )

            if system_inputs or truth_data:
                dataset = modeldb.Dataset.objects.get(dataset_id=ds["dataset_id"])
                input_path, truth_path = [Path(i) for i in paths]

                for target_path, mirror in [(input_path, system_inputs), (truth_path, truth_data)]:
                    if not mirror:
                        continue

                    url = list(json.loads(mirror.mirrors).values())[0]
                    resource_type = "inputs" if target_path == input_path else "truths"

                    if resource_type == "inputs":
                        zipDirectory = data.get("systemUrlDirectory")
                        rename_to = data.get("systemFileRename")
                    else:
                        zipDirectory = data.get("truthUrlDirectory")
                        rename_to = data.get("truthFileRename")

                    if ".zip" in url:
                        rename_to = None
                        imported_files = 0
                        with zipfile.ZipFile(mirror.get_path_in_file_system(), "r") as zip_ref:
                            directories = []
                            for file_info in zip_ref.infolist():
                                target_file = target_path / Path(file_info.filename)

                                if file_info.filename.endswith("/"):
                                    directories += [file_info.filename]
                                    continue

                                if zipDirectory:
                                    zipDirectory = [i for i in zipDirectory.split("/") if i]
                                    zipDirectory = "/".join(zipDirectory)
                                    target_file = target_path / Path(file_info.filename[len(zipDirectory) + 1 :])
                                    if not file_info.filename.startswith(zipDirectory + "/"):
                                        continue

                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                with zip_ref.open(file_info) as source_file:
                                    with open(target_file, "wb") as t:
                                        t.write(source_file.read())
                                        imported_files += 1
                        if imported_files == 0:
                            return JsonResponse(
                                {
                                    "status": 1,
                                    "message": f"No files were extracted from the subdirectory '{zipDirectory}' "
                                    f" of the zip file at '{url}'. "
                                    + f"The following directories exist in the zip file: {directories}.",
                                }
                            )
                    else:
                        zipDirectory = None
                        if not rename_to:
                            rename_to = url

                        rename_to = rename_to.split("/")[-1].split("#")[0].split("?")[0].split("&")[0]
                        target_path = target_path / rename_to

                        copyfile(mirror.get_path_in_file_system(), target_path)

                    print(target_path)

                    modeldb.DatasetHasMirroredResource.objects.create(
                        dataset=dataset,
                        mirrored_resource=mirror,
                        resource_type=resource_type,
                        subdirectory=zipDirectory,
                        rename_to=rename_to,
                    )

            path_string = "\n ".join(paths)
            update_file_listing_for_dataset(ds["dataset_id"])
            return JsonResponse(
                {
                    "status": 0,
                    "context": ds,
                    "message": (
                        f"Created new dataset with id {ds['dataset_id']}. "
                        "Store your datasets in the following Paths:\n"
                        f"{path_string}"
                    ),
                }
            )
        except FileExistsError as e:
            logger.exception(e)
            return JsonResponse({"status": 1, "message": "A Dataset with this id already exists."})

    return JsonResponse({"status": 1, "message": "GET is not implemented for add dataset"})


def _evaluator_config(data: dict) -> "Optional[Any]":
    if "trusted_measures" not in data:
        return None

    from tira.evaluators import get_evaluators_if_valid

    ret = {"measures": data["trusted_measures"]}

    json_args = ["additional_args", "format_configuration", "truth_format_configuration"]
    for json_arg in json_args:
        if json_arg in data and data[json_arg]:
            try:
                ret[json_arg] = json.loads(data[json_arg])
            except Exception:
                raise ValueError(
                    f"I expected that the argument {json_arg} is valid json. But I got '{data[json_arg]}'."
                )

    ret_serialized = json.dumps(ret)
    try:
        ret["run_format"] = data.get("format", None)
        ret["run_format_configuration"] = ret.get("format_configuration", None)
        ret["truth_format"] = data.get("truth_format", None)
        ret["truth_format_configuration"] = data.get("truth_format_configuration", None)
        get_evaluators_if_valid(ret)
    except Exception as e:
        logger.warning(e)
        raise ValueError(f"The configuration of the evaluator is wrong: {e.args[0]}")

    return ret_serialized


def _format_and_configuration(data: "dict[str, str]", field: str) -> "tuple[Optional[str], Optional[Any]]":
    if field not in data or not data.get(field):
        return None, None

    ret_name = data[field]
    ret_config = None
    if f"{field}_configuration" in data and data[f"{field}_configuration"]:
        try:
            ret_config = json.loads(data[f"{field}_configuration"])
        except Exception:
            raise ValueError(
                f"I expected that the configuration is valid json, but I got: {data[f'{field}_configuration']}"
            )

    from tira.check_format import check_format_configuration_if_valid

    check_format_configuration_if_valid(ret_name, ret_config)
    return ret_name, ret_config


@check_permissions
@check_resources_exist("json")
def admin_edit_dataset(request: "HttpRequest", dataset_id: str) -> "HttpResponse":
    """Edit a dataset with the given dataset_id
    Send the new data of the dataset via POST. All these keys must be given and will be set:

    - name: New display name of the dataset
    - task: The associated task
    - master_id: ID of the vm that runs the evaluator for this dataset
    - type: 'training' or 'test'
    - evaluator_working_directory: working directory of the evaluator on the master vm
    - evaluator_command: command to be run on the master vm to evaluate the output of runs on the dataset
    - evaluation_measures: (str) the measures output by the evaluator. Sent as a string with:
        `
        Display Name of Measure1,key_of_measure_1\n
        Display Name of Measure2,key_of_measure_2\n
        ...
        `
    - is_git_runner
    - git_runner_image
    - git_runner_command
    - git_repository_id
    """
    if request.method == "POST":

        data = json.loads(request.body)

        dataset_name = data["name"]
        task_id = data["task"]
        is_confidential = not data["publish"]

        command = data["evaluator_command"]
        working_directory = data["evaluator_working_directory"]
        measures = ""  # here for legacy reasons. TIRA uses the measures provided by the evaluator

        is_git_runner = data["is_git_runner"]
        git_runner_image = data["git_runner_image"]
        git_runner_command = data["git_runner_command"]
        git_repository_id = data["git_repository_id"]

        try:
            dataset_format, dataset_format_configuration = _format_and_configuration(data, "format")
        except Exception as e:
            logger.info(e)
            return JsonResponse(
                {"status": 1, "message": "The configuration of the dataset format is invalid:" + str(e.args[0])}
            )

        try:
            truth_format, truth_format_configuration = _format_and_configuration(data, "truth_format")
        except Exception as e:
            logger.info(e)
            return JsonResponse(
                {"status": 1, "message": "The configuration of the truth format is invalid:" + str(e.args[0])}
            )

        description = data.get("description", "")
        chatnoir_id = data.get("chatnoir_id", None)
        ir_datasets_id = data.get("ir_datasets_id", None)
        try:
            trusted_evaluation = _evaluator_config(data)
        except Exception as e:
            logger.info(e)
            return JsonResponse({"status": 1, "message": e.args[0]})

        if not data["use_existing_repository"]:
            git_repository_id = model.get_git_integration(task_id=task_id).create_task_repository(task_id)

        upload_name = data["upload_name"]

        if not model.task_exists(task_id):
            return JsonResponse({"status": 1, "message": f"Task with ID {task_id} does not exist"})

        ds = model.edit_dataset(
            task_id,
            dataset_id,
            dataset_name,
            command,
            working_directory,
            measures,
            upload_name,
            is_confidential,
            is_git_runner,
            git_runner_image,
            git_runner_command,
            git_repository_id,
            dataset_format,
            description,
            chatnoir_id,
            ir_datasets_id,
            truth_format,
            trusted_evaluation,
            dataset_format_configuration,
            truth_format_configuration,
        )

        from django.core.cache import cache

        model.git_pipeline_is_enabled_for_task(task_id, cache, force_cache_refresh=True)

        update_file_listing_for_dataset(dataset_id)
        return JsonResponse({"status": 0, "context": ds, "message": f"Updated Dataset {ds['dataset_id']}."})

    return JsonResponse({"status": 1, "message": "GET is not implemented for add dataset"})


def call_django_command_failsave(cmd: str, args: list[str]) -> "dict[str, Optional[str]]":
    import sys
    from io import StringIO

    from django.core.management import call_command

    captured_stdout = StringIO()
    captured_stderr = StringIO()

    error = None

    sys.stdout = captured_stdout
    sys.stderr = captured_stderr

    try:
        call_command(cmd, **args)
    except Exception as e:
        error = str(e)
        error += "\n\n" + traceback.format_exc()

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    return {"stdout": str(captured_stdout.getvalue()), "stderr": str(captured_stderr.getvalue()), "error": error}


@check_permissions
def admin_import_ir_dataset(request: "HttpRequest", task_id: str) -> "HttpResponse":
    """Create multiple datasets for the pased ir-dataset.
    Return a json status message."""
    if request.method == "POST":
        data = json.loads(request.body)

        if not all(k in data.keys() for k in ["dataset_id", "name", "image"]):
            return JsonResponse({"status": 1, "message": "Error: dataset_id, name, and image must be set."})

        dataset_id_prefix = data["dataset_id"]
        dataset_name = data["name"]

        upload_name = data.get("upload_name", "run.txt")
        evaluator_command = data.get("evaluator_command", "")
        working_directory = data.get("evaluator_working_directory", "")
        measures = data.get("evaluation_measures", "")

        is_git_runner = data.get("is_git_runner", True)
        git_runner_image = data.get("git_runner_image", data.get("image"))
        git_runner_command = data.get("git_runner_command", settings.IR_MEASURES_COMMAND)
        git_repository_id = model.get_git_integration(task_id=task_id).create_task_repository(task_id)
        irds_import_command = (
            f'/irds_cli.sh --skip_qrels true --ir_datasets_id {data["dataset_id"]} --output_dataset_path $outputDir'
        )
        irds_import_truth_command = (
            f'/irds_cli.sh --skip_documents true --ir_datasets_id {data["dataset_id"]} --output_dataset_truth_path'
            " $outputDir"
        )

        master_vm_id = None

        try:
            if data["type"] == "training":
                ds, (dataset_path, dataset_truth_path) = model.add_dataset(
                    task_id,
                    dataset_id_prefix,
                    "training",
                    dataset_name,
                    upload_name,
                    irds_docker_image=git_runner_image,
                    irds_import_command=irds_import_command,
                    irds_import_truth_command=irds_import_truth_command,
                )
            elif data["type"] == "test":
                ds, (dataset_path, dataset_truth_path) = model.add_dataset(
                    task_id,
                    dataset_id_prefix,
                    "test",
                    dataset_name,
                    upload_name,
                    irds_docker_image=git_runner_image,
                    irds_import_command=irds_import_command,
                    irds_import_truth_command=irds_import_truth_command,
                )
            else:
                return JsonResponse(
                    {"status": 1, "message": "Invalid data type. Expected training or test, got : " + data["type"]}
                )
        except FileExistsError as e:
            logger.exception(e)
            return JsonResponse({"status": 1, "message": "A Dataset with this id already exists. Error: " + str(e)})

        model.add_evaluator(
            master_vm_id,
            task_id,
            ds["dataset_id"],
            evaluator_command,
            working_directory,
            not measures,
            is_git_runner,
            git_runner_image,
            git_runner_command,
            git_repository_id,
        )

        # TODO: what is the up-to-date href for background_jobs?
        try:
            process_id = run_irds_command(
                ds["task"],
                ds["dataset_id"],
                ds["irds_docker_image"],
                ds["irds_import_command"],
                dataset_path,
                ds["irds_import_truth_command"],
                dataset_truth_path,
            )
            return JsonResponse(
                {
                    "status": 0,
                    "context": ds,
                    "message": "Imported dataset successfull.",
                    "href": f"/background_jobs/{task_id}/{process_id}",
                }
            )
        except Exception as e:
            return JsonResponse({"status": 1, "context": {}, "message": f"Import of dataset failed with: {e}."})

    return JsonResponse({"status": 1, "message": "GET is not implemented for add dataset"})


@check_permissions
@check_resources_exist("json")
def admin_delete_dataset(request: "HttpRequest", dataset_id: str) -> "HttpResponse":
    try:
        model.delete_dataset(dataset_id)
        return JsonResponse({"status": 0, "message": f"Deleted dataset {dataset_id}"})
    except Exception as e:
        return JsonResponse({"status": 1, "message": f"Could not delete dataset {dataset_id}: {e}"})


@check_permissions
def admin_add_organizer(request: "HttpRequest", organizer_id: str) -> "HttpResponse":
    if request.method == "POST":
        data = json.loads(request.body)
        add_default_git_integrations = False

        if data["gitUrlToNamespace"]:
            assert isinstance(data["gitUrlToNamespace"], str) and isinstance(data["gitPrivateToken"], str)
            git_integration_is_valid, error_message = check_that_git_integration_is_valid(
                data["gitUrlToNamespace"], data["gitPrivateToken"]
            )

            if not git_integration_is_valid:
                return JsonResponse({"status": 1, "message": error_message})
        else:
            add_default_git_integrations = True

        model.edit_organizer(
            organizer_id, data["name"], data["years"], data["web"], data["gitUrlToNamespace"], data["gitPrivateToken"]
        )

        if add_default_git_integrations:
            git_integration = model.model.get_git_integration(settings.DEFAULT_GIT_INTEGRATION_URL, "<OMMITTED>")
            assert git_integration is not None
            model.model.edit_organizer(
                organizer_id, data["name"], data["years"], data["web"], git_integrations=[git_integration]
            )

        userid = auth.get_user_id(request)
        assert userid is not None
        auth.create_organizer_group(organizer_id, userid)
        return JsonResponse({"status": 0, "message": f"Added Organizer {organizer_id}"})

    return JsonResponse({"status": 1, "message": "GET is not implemented for add organizer"})


@check_permissions
@check_resources_exist("json")
def admin_edit_organizer(request: "HttpRequest", organizer_id: str) -> "HttpResponse":
    if request.method == "POST":
        data = json.loads(request.body)

        if data["gitUrlToNamespace"]:
            git_integration_is_valid, error_message = check_that_git_integration_is_valid(
                data["gitUrlToNamespace"], data["gitPrivateToken"]
            )

            if not git_integration_is_valid:
                return JsonResponse({"status": 1, "message": error_message})

        model.edit_organizer(
            organizer_id, data["name"], data["years"], data["web"], data["gitUrlToNamespace"], data["gitPrivateToken"]
        )
        return JsonResponse({"status": 0, "message": f"Updated Organizer {organizer_id}"})

    return JsonResponse({"status": 1, "message": "GET is not implemented for edit organizer"})


@check_conditional_permissions(restricted=True)
def admin_create_group(request: "HttpRequest", vm_id: str) -> "HttpResponse":
    """this is a rest endpoint to grant a user permissions on a vm"""
    if auth.get_role(request=request) != "admin":
        return HttpResponseNotAllowed("Access forbidden.", status_code=403)

    try:
        vm_id = slugify(vm_id)
        modeldb.VirtualMachine.objects.create(vm_id=vm_id, user_password="no-password", roles="user")
        context = auth.create_group(vm_id)

        return JsonResponse({"status": 0, "context": context})
    except Exception as e:
        logger.exception(e)
        return JsonResponse({"status": 1, "message": repr(e)})


@check_conditional_permissions(restricted=True)
@check_resources_exist("json")
def admin_edit_review(request: "HttpRequest", dataset_id: str, vm_id: str, run_id: str) -> "HttpResponse":
    if request.method == "POST":
        data = json.loads(request.body)
        no_errors = data.get("no_errors", True)
        output_error = data.get("output_error", False)
        software_error = data.get("software_error", False)
        comment = data["comment"]

        # sanity checks
        if no_errors and (output_error or software_error):
            JsonResponse({"status": 1, "message": "Error type is not clearly selected."})

        username = auth.get_user_id(request)
        has_errors = output_error or software_error
        has_no_errors = not has_errors

        model.update_review(
            dataset_id,
            vm_id,
            run_id,
            username,
            str(dt.datetime.now(dt.timezone.utc)),
            has_errors,
            has_no_errors,
            no_errors=no_errors,
            invalid_output=output_error,
            has_error_output=output_error,
            other_errors=software_error,
            comment=comment,
        )
        return JsonResponse({"status": 0, "message": f"Updated review for run {run_id}"})

    return JsonResponse({"status": 1, "message": "GET is not implemented for edit organizer"})


@check_permissions
def admin_upload_dataset(request: "HttpRequest", task_id: str, dataset_id: str, dataset_type: str) -> "HttpResponse":
    if request.method != "POST":
        return JsonResponse({"status": 1, "message": "GET is not allowed here."})

    if not dataset_id or dataset_id is None or dataset_id == "None":
        return JsonResponse({"status": 1, "message": "Please specify the associated dataset."})

    if dataset_type not in ["input", "truth"]:
        return JsonResponse(
            {"status": 1, "message": f"Invalid dataset_type. Expected 'input' or 'truth', but got: '{dataset_type}'"}
        )

    dataset_suffix = "" if dataset_type == "input" else "-truth"

    uploaded_file = request.FILES["file"]

    if not uploaded_file.name.endswith(".zip"):
        return JsonResponse(
            {"status": 1, "message": f"Invalid Upload. I expect a zip file, but got '{uploaded_file.name}'."}
        )

    dataset = model.get_dataset(dataset_id)

    if "dataset_id" not in dataset or dataset_id != dataset["dataset_id"]:
        return JsonResponse({"status": 1, "message": "Unknown dataset_id."})

    if dataset_id.endswith("-test"):
        dataset_prefix = "test-"
    elif dataset_id.endswith("-training"):
        dataset_prefix = "training-"
    else:
        return JsonResponse({"status": 1, "message": "Unknown dataset_id."})

    target_directory: Path = (
        model.model.data_path / (dataset_prefix + "datasets" + dataset_suffix) / task_id / dataset_id
    )

    if not target_directory.is_dir():
        return JsonResponse({"status": 1, "message": "Dataset directory 'target_directory' does not exist."})

    if len(os.listdir(target_directory)) > 0:
        return JsonResponse(
            {
                "status": 1,
                "message": (
                    "There is already some dataset uploaded. We prevent to overwrite data. Please create a new dataset"
                    " (i.e., a new version) if you want to update the dataset. Please reach out to us if creating a"
                    " new dataset would not solve your problem."
                ),
            }
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        with open(tmp_dir + "/tmp.zip", "wb+") as fp_destination:
            for chunk in uploaded_file.chunks():
                fp_destination.write(chunk)

        with zipfile.ZipFile(tmp_dir + "/tmp.zip", "r") as zip_ref:
            zip_ref.extractall(target_directory)

        return JsonResponse(
            {"status": 0, "message": f"Uploaded files '{os.listdir(target_directory)}' to '{target_directory}'."}
        )
