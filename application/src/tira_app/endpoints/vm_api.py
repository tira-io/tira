import html
import json
import logging
import shutil
import uuid
import zipfile
from functools import wraps
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from discourse_client_in_disraptor.discourse_api_client import get_disraptor_user
from django.conf import settings
from django.core.cache import cache
from django.db.utils import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from grpc import RpcError, StatusCode
from markdown import markdown
from tira.check_format import _fmt, check_format
from tira.third_party_integrations import temporary_directory

from .. import tira_model as model
from ..authentication import auth
from ..checks import check_conditional_permissions, check_permissions, check_resources_exist
from ..grpc_client import GrpcClient
from ..model import EvaluationLog, TransitionLog
from ..util import get_tira_id, link_to_discourse_team, reroute_host
from ..views import add_context

if TYPE_CHECKING:
    from typing import Any, Mapping, Optional

    from django.http import HttpRequest, HttpResponse

include_navigation = False

logger = logging.getLogger("tira")
logger.info("ajax_routes: Logger active")


def _host_call(func):
    """This is a decorator for methods that connect to a host. It handles all exceptions that can occur
    in the grpc communication. It also adds a reply consistent with the return status of the grpc call."""

    @wraps(func)
    def func_wrapper(request, *args, **kwargs):
        try:
            response = func(request, *args, **kwargs)
        except RpcError as e:
            ex_message = "FAILED"
            try:
                logger.exception(f"{request.get_full_path()}: connection failed with {e}")
                if e.code() == StatusCode.UNAVAILABLE:  # .code() is implemented by the _channel._InteractiveRpcError
                    logger.exception(f"Connection Unavailable: {e.debug_error_string()}")
                    ex_message = (  # This happens if the GRPC Server is not running
                        "The requested host is unavailable. If you think this is a mistake, please contact "
                        "your task organizer."
                    )
                if e.code() == StatusCode.INVALID_ARGUMENT:
                    logger.exception(f"Invalid Argument: {e.debug_error_string()}")
                    ex_message = f"Response returned with an invalid argument: {e.debug_error_string()}"  #
            except Exception as e2:  # There is a RpcError but not an Interactive one. This should not happen
                logger.exception(f"{request.get_full_path()}: Unexpected Exception occurred: {e2}")
                ex_message = f"An unexpected exception occurred: {e2}"
            return JsonResponse({"status": "2", "message": ex_message}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"{request.get_full_path()}: Server Error: {e}")
            return JsonResponse(
                {"status": "1", "message": f"An unexpected exception occurred: {e}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        if response.status == 0:
            return JsonResponse({"status": 0, "message": response.transactionId}, status=HTTPStatus.ACCEPTED)
        if response.status == 2:
            return JsonResponse(
                {"status": 2, "message": f"Virtual machine not found on host: {response.message}"},
                status=HTTPStatus.NOT_FOUND,
            )
        if response.status == 3:
            return JsonResponse(
                {"status": 1, "message": f"Virtual machine is in the wrong state for your request: {response.message}"},
                status=HTTPStatus.BAD_REQUEST,
            )
        if response.status == 4:
            return JsonResponse(
                {"status": 1, "message": f"VM is archived: {response.message}"}, status=HTTPStatus.NOT_FOUND
            )
        if response.status == 5:
            return JsonResponse(
                {"status": 2, "message": f"VM is not accessible: {response.message}"}, status=HTTPStatus.NOT_FOUND
            )
        if response.status == 6:
            return JsonResponse(
                {"status": 1, "message": f"Requested input run was not found: {response.message}"},
                status=HTTPStatus.NOT_FOUND,
            )
        if response.status == 7:
            return JsonResponse(
                {"status": 1, "message": f"Evaluation failed due to malformed run output: {response.message}"},
                status=HTTPStatus.BAD_REQUEST,
            )
        if response.status == 8:
            return JsonResponse(
                {"status": 1, "message": f"Input malformed: {response.message}"}, status=HTTPStatus.BAD_REQUEST
            )
        if response.status == 9:
            return JsonResponse(
                {"status": 2, "message": f"Host ist busy: {response.message}"}, status=HTTPStatus.SERVICE_UNAVAILABLE
            )

        return JsonResponse(
            {"status": 2, "message": f"{response.transactionId} was rejected by the host: {response.message}"},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    return func_wrapper


# ---------------------------------------------------------------------
#   VM actions
# ---------------------------------------------------------------------


@check_permissions
@check_resources_exist("json")
def vm_state(request: "HttpRequest", vm_id: str) -> HttpResponse:
    try:
        state = TransitionLog.objects.get_or_create(vm_id=vm_id, defaults={"vm_state": 0})[0].vm_state
    except IntegrityError as e:
        logger.warning(f"failed to read state for vm {vm_id} with {e}")
        state = 0
    return JsonResponse({"status": 0, "state": state})


@check_permissions
@check_resources_exist("json")
def vm_running_evaluations(request: "HttpRequest", vm_id: str) -> HttpResponse:
    results = EvaluationLog.objects.filter(vm_id=vm_id)
    return JsonResponse({"status": 0, "running_evaluations": True if results else False})


@check_permissions
@check_resources_exist("json")
def get_running_evaluations(request: "HttpRequest", vm_id: str) -> HttpResponse:
    results = EvaluationLog.objects.filter(vm_id=vm_id)
    return JsonResponse(
        {
            "status": 0,
            "running_evaluations": [
                {"vm_id": r.vm_id, "run_id": r.run_id, "running_on": r.running_on, "last_update": r.last_update}
                for r in results
            ],
        }
    )


@add_context
@check_permissions
def docker_software_details(request: "HttpRequest", context, vm_id: str, docker_software_id: str) -> HttpResponse:
    context["docker_software_details"] = model.get_docker_software(int(docker_software_id))

    if "mount_hf_model" in context["docker_software_details"] and context["docker_software_details"]["mount_hf_model"]:
        mount_hf_model = []
        for i in context["docker_software_details"]["mount_hf_model"].split():
            mount_hf_model += [{"href": f"https://huggingface.co/{i}", "display_name": i}]

        context["docker_software_details"]["mount_hf_model_display"] = mount_hf_model

    return JsonResponse({"status": 0, "context": context})


@check_permissions
def huggingface_model_mounts(request: "HttpRequest", vm_id: str, hf_model: str) -> HttpResponse:
    from ..huggingface_hub_integration import huggingface_model_mounts, snapshot_download_hf_model

    context = {"hf_model_available": False, "hf_model_for_vm": vm_id}

    try:
        context["hf_model_available"] = huggingface_model_mounts([hf_model.replace("--", "/")]) is not None
    except Exception:
        pass

    if not context["hf_model_available"]:
        try:
            snapshot_download_hf_model(hf_model)
            context["hf_model_available"] = True
        except Exception as e:
            logger.warning(e)
            return JsonResponse({"status": "1", "message": str(e)})

    return JsonResponse({"status": 0, "context": context})


@add_context
@check_permissions
def upload_group_details(request: "HttpRequest", context, task_id: str, vm_id: str, upload_id: str) -> HttpResponse:
    try:
        context["upload_group_details"] = model.get_upload(task_id, vm_id, upload_id)
    except Exception as e:
        return JsonResponse({"status": "1", "message": f"An unexpected exception occurred: {e}"})

    return JsonResponse({"status": 0, "context": context})


@check_conditional_permissions(restricted=True)
@_host_call
def vm_create(request: "HttpRequest", hostname: str, vm_id: str, ova_file: str) -> HttpResponse:
    uid = auth.get_user_id(request)
    host = reroute_host(hostname)
    return GrpcClient(host).vm_create(vm_id=vm_id, ova_file=ova_file, user_id=uid, hostname=host)


@check_permissions
@check_resources_exist("json")
@_host_call
def vm_start(request: "HttpRequest", vm_id: str) -> HttpResponse:
    vm = model.get_vm(vm_id)
    # NOTE vm_id is different from vm.vmName (latter one includes the 01-tira-ubuntu-...
    return GrpcClient(reroute_host(vm["host"])).vm_start(vm_id=vm_id)


@check_permissions
@check_resources_exist("json")
@_host_call
def vm_shutdown(request: "HttpRequest", vm_id: str) -> HttpResponse:
    vm = model.get_vm(vm_id)
    return GrpcClient(reroute_host(vm["host"])).vm_shutdown(vm_id=vm_id)


@check_permissions
@check_resources_exist("json")
@_host_call
def vm_stop(request: "HttpRequest", vm_id: str) -> HttpResponse:
    vm = model.get_vm(vm_id)
    return GrpcClient(reroute_host(vm["host"])).vm_stop(vm_id=vm_id)


@check_permissions
@check_resources_exist("json")
def vm_info(request: "HttpRequest", vm_id: str) -> HttpResponse:
    vm = model.get_vm(vm_id)
    host = reroute_host(vm["host"])
    if not host:
        logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed, because host is empty")
        return JsonResponse({"status": "Rejected", "message": "SERVER_ERROR"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    try:
        grpc_client = GrpcClient(host)
        response_vm_info = grpc_client.vm_info(vm_id=vm_id)
        _ = TransitionLog.objects.update_or_create(vm_id=vm_id, defaults={"vm_state": response_vm_info.state})
        del grpc_client
    except RpcError as e:
        ex_message = "FAILED"
        try:
            if e.code() == StatusCode.UNAVAILABLE:  # .code() is implemented by the _channel._InteractiveRpcError
                logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed with {e}")
                ex_message = "Host Unavailable"  # This happens if the GRPC Server is not running
            if e.code() == StatusCode.INVALID_ARGUMENT:  # .code() is implemented by the _channel._InteractiveRpcError
                ex_message = "VM is archived"  # If there is no VM with the requested name on the host.
                _ = TransitionLog.objects.update_or_create(vm_id=vm_id, defaults={"vm_state": 8})
        except Exception as e2:  # There is a RpcError but not an Interactive one. This should not happen
            logger.exception(f"/grpc/{vm_id}/vm-info: Unexpected Execption occured: {e2}")
        return JsonResponse({"status": 1, "message": ex_message}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception(f"/grpc/{vm_id}/vm-info: connection to {host} failed with {e}")
        return JsonResponse({"status": 1, "message": "SERVER_ERROR"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return JsonResponse(
        {
            "status": 0,
            "context": {
                "guestOs": response_vm_info.guestOs,
                "memorySize": response_vm_info.memorySize,
                "numberOfCpus": response_vm_info.numberOfCpus,
                "sshPort": response_vm_info.sshPort,
                "rdpPort": response_vm_info.rdpPort,
                "host": response_vm_info.host,
                "sshPortStatus": response_vm_info.sshPortStatus,
                "rdpPortStatus": response_vm_info.rdpPortStatus,
                "state": response_vm_info.state,
            },
        }
    )


# ---------------------------------------------------------------------
#   Software actions
# ---------------------------------------------------------------------
@check_permissions
@check_resources_exist("json")
def software_add(request: "HttpRequest", task_id: str, vm_id: str) -> HttpResponse:
    if request.method == "GET":
        if not task_id or task_id is None or task_id == "None":
            return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})

        software = model.add_software(task_id, vm_id)
        if not software:
            return JsonResponse(
                {"status": 1, "message": "Failed to create a new Software."}, status=HTTPStatus.INTERNAL_SERVER_ERROR
            )

        context = {
            "task": task_id,
            "vm_id": vm_id,
            "software": {
                "id": software["id"],
                "command": software["command"],
                "working_dir": software["working_directory"],
                "dataset": software["dataset"],
                "creation_date": software["creation_date"],
                "last_edit": software["last_edit"],
            },
        }
        return JsonResponse({"status": 0, "message": "ok", "context": context})
    else:
        return JsonResponse({"status": 1, "message": "POST is not allowed here."})


@check_permissions
@check_resources_exist("json")
def software_save(request: "HttpRequest", task_id: str, vm_id: str, software_id: str) -> HttpResponse:
    if request.method == "POST":
        data = json.loads(request.body)
        new_dataset = data.get("input_dataset")
        if not model.dataset_exists(new_dataset):
            return JsonResponse({"status": 1, "message": f"Cannot save, the dataset {new_dataset} does not exist."})

        software = model.update_software(
            task_id,
            vm_id,
            software_id,
            data.get("command"),
            data.get("working_dir"),
            data.get("input_dataset"),
            data.get("input_run"),
        )

        message = "failed to save software for an unknown reasons"
        try:
            if software:
                return JsonResponse(
                    {"status": 0, "message": f"Saved {software_id}", "last_edit": software.lastEditDate},
                    status=HTTPStatus.ACCEPTED,
                )
        except Exception as e:
            message = str(e)

        return JsonResponse({"status": 1, "message": message}, status=HTTPStatus.BAD_REQUEST)
    return JsonResponse({"status": 1, "message": "GET is not implemented for add dataset"})


@check_permissions
@check_resources_exist("json")
def software_delete(request: "HttpRequest", task_id: str, vm_id: str, software_id: str) -> HttpResponse:
    delete_ok = model.delete_software(task_id, vm_id, software_id)

    if delete_ok:
        return JsonResponse({"status": 0}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse(
            {
                "status": 1,
                "message": "Cannot delete software, because it has a valid evaluation assigned (or it does not exist.)",
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@check_permissions
@check_resources_exist("json")
@_host_call
def run_execute(request: "HttpRequest", task_id: str, vm_id: str, software_id: str) -> HttpResponse:
    vm = model.get_vm(vm_id)
    software = model.get_software(task_id, vm_id, software_id=software_id)
    if not model.dataset_exists(software["dataset"]):
        return JsonResponse({"status": 1, "message": f'The dataset {software["dataset"]} does not exist'})
    host = reroute_host(vm["host"])
    future_run_id = get_tira_id()
    grpc_client = GrpcClient(host)
    response = grpc_client.run_execute(
        vm_id=vm_id,
        dataset_id=software["dataset"],
        run_id=future_run_id,
        input_run_vm_id="",
        input_run_dataset_id="",
        input_run_run_id=software["run"],
        optional_parameters="",
        task_id=task_id,
        software_id=software_id,
    )
    del grpc_client
    return response


@_host_call
def _master_vm_eval_call(vm_id: str, dataset_id: str, run_id: str, evaluator: "dict[str, Any]") -> HttpResponse:
    """Called when the evaluation is done via master vm.
    This method calls the grpc client"""
    host = reroute_host(evaluator["host"])
    grpc_client = GrpcClient(host)
    response = grpc_client.run_eval(
        vm_id=evaluator["vm_id"],
        dataset_id=dataset_id,
        run_id=get_tira_id(),
        input_run_vm_id=vm_id,
        input_run_dataset_id=dataset_id,
        input_run_run_id=run_id,
        optional_parameters="",
    )
    del grpc_client
    return response


def _git_runner_vm_eval_call(vm_id, dataset_id, run_id, evaluator):
    """called when the evaluation is done via git runner.
    This method calls the git utilities in git_runner.py to start the git CI
    """
    try:
        transaction_id = model.get_git_integration(dataset_id=dataset_id).run_evaluate_with_git_workflow(
            evaluator["task_id"],
            dataset_id,
            vm_id,
            run_id,
            evaluator["git_runner_image"],
            evaluator["git_runner_command"],
            evaluator["git_repository_id"],
            evaluator["evaluator_id"],
        )
    except Exception as e:
        return JsonResponse({"status": 1, "message": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    return JsonResponse({"status": 0, "message": transaction_id}, status=HTTPStatus.ACCEPTED)


def run_unsandboxed_eval(vm_id: str, dataset_id: str, run_id: str) -> None:
    from tira.evaluators import evaluate
    from tira.io_utils import run_prototext

    dataset = model.get_dataset(dataset_id)
    task_id = dataset["task"]

    if dataset_id.endswith("-test"):
        dataset_prefix = "test-"
    elif dataset_id.endswith("-training"):
        dataset_prefix = "training-"
    else:
        raise ValueError("Unknown dataset_id.")

    truth_directory = model.model.data_path / (dataset_prefix + "datasets-truth") / task_id / dataset_id
    run_directory = model.model.runs_dir_path / dataset_id / vm_id / run_id / "output"

    eval_result = evaluate(run_directory, truth_directory, dataset, monitored=True)
    print(eval_result)
    eval_run_id = str(uuid4()) + "-evaluates-" + run_id

    run_prototext(eval_result, eval_run_id, run_id, dataset["evaluator_id"], dataset_id, task_id)
    shutil.move(src=eval_result, dst=model.model.runs_dir_path / dataset_id / vm_id / eval_run_id)
    print(model.model.runs_dir_path / dataset_id / vm_id / eval_run_id)

    model.add_run(dataset_id, vm_id, eval_run_id)


@check_conditional_permissions(private_run_ok=True)
@check_resources_exist("json")
def run_eval(request, vm_id, dataset_id, run_id):
    """Get the evaluator for dataset_id from the model.
    Then, send a GRPC-call to the host running the evaluator with the run data.
    Then, log vm_id and run_id to the evaluation log as ongoing.
    """
    # check if evaluation already exists
    existing_evaluations = EvaluationLog.objects.filter(run_id=run_id)
    if existing_evaluations and len(existing_evaluations) > 5:
        return JsonResponse(
            {"status": "1", "message": "An evaluation is already in progress."}, status=HTTPStatus.PRECONDITION_FAILED
        )

    evaluator = model.get_evaluator(dataset_id)
    if "is_git_runner" in evaluator and evaluator["is_git_runner"]:
        ret = _git_runner_vm_eval_call(vm_id, dataset_id, run_id, evaluator)
        git_runner = model.get_git_integration(dataset_id=dataset_id)
        git_runner.all_running_pipelines_for_repository(evaluator["git_repository_id"], cache, force_cache_refresh=True)

        return ret

    return _master_vm_eval_call(vm_id, dataset_id, run_id, evaluator)


@check_conditional_permissions(private_run_ok=True)
def run_delete(request, dataset_id, vm_id, run_id):
    delete_ok = model.delete_run(dataset_id, vm_id, run_id)
    if delete_ok:
        return JsonResponse({"status": 0}, status=HTTPStatus.ACCEPTED)
    return JsonResponse(
        {"status": 1, "message": f"Can not delete run {run_id} since it is used as an input run."},
        status=HTTPStatus.ACCEPTED,
    )


@check_permissions
@check_resources_exist("json")
@_host_call
def run_abort(request, vm_id):
    """ """
    vm = model.get_vm(vm_id)
    host = reroute_host(vm["host"])

    grpc_client = GrpcClient(host)
    response = grpc_client.run_abort(vm_id=vm_id)
    del grpc_client
    return response


@csrf_exempt
@check_permissions
@check_resources_exist("json")
def upload(request: "HttpRequest", task_id: str, vm_id: str, dataset_id: str, upload_id: str) -> "HttpResponse":
    if request.method == "POST":
        if not dataset_id or dataset_id is None or dataset_id == "None":
            return JsonResponse({"status": 1, "message": "Please specify the associated dataset."})

        uploaded_file = request.FILES["file"]
        new_run = model.add_uploaded_run(task_id, vm_id, dataset_id, upload_id, uploaded_file)
        if model.git_pipeline_is_enabled_for_task(task_id, cache):
            run_eval(request=request, vm_id=vm_id, dataset_id=dataset_id, run_id=new_run["run"]["run_id"])

            return JsonResponse({"status": 0, "message": "ok", "new_run": new_run, "started_evaluation": True})
        return JsonResponse({"status": 0, "message": "ok", "new_run": new_run, "started_evaluation": False})
    else:
        return JsonResponse({"status": 1, "message": "GET is not allowed here."})


def _parse_notebook_to_html(notebook_content: str) -> "Optional[str]":
    import nbformat
    from nbconvert import HTMLExporter

    try:
        notebook = nbformat.reads(notebook_content, as_version=4)  # type: ignore [no-untyped-call]
        html_exporter: HTMLExporter = HTMLExporter(template_name="classic")  # type: ignore [no-untyped-call]
        (body, _) = html_exporter.from_notebook_node(notebook)
        return body
    except Exception:
        pass
    return None


def load_notebook(upload_dir: Path) -> "Optional[dict[str, Optional[str]]]":
    if not (upload_dir / ".tirex-tracker" / "code.zip").exists():
        return {}

    try:
        archive = zipfile.ZipFile(upload_dir / ".tirex-tracker" / "code.zip", "r")
        files = [i.filename for i in archive.filelist]
        if "notebook.ipynb" not in files or "script.py" not in files:
            return {}

        with archive.open("notebook.ipynb") as file:
            notebook_content = file.read().decode("utf-8")

        with archive.open("script.py") as file:
            script_content = file.read().decode("utf-8")

        return {
            "notebook_html": _parse_notebook_to_html(json.dumps(json.loads(notebook_content))),
            "notebook": notebook_content,
            "script": script_content,
        }
    except Exception:
        pass
    return None


def _parse_metadata_from_upload(upload_dir: Path) -> "dict[str, Any]":
    has_metadata = False
    metadata_git_repo = None
    metadata_has_notebook = False
    from tira.check_format import lines_if_valid, report_valid_formats

    try:
        lines = lines_if_valid(upload_dir, "ir_metadata")
        has_metadata = len(lines) > 0
        metadata_git_repo = None

        for line in lines:
            try:
                content = line["content"]

                if (
                    "implementation" in content
                    and "source" in content["implementation"]
                    and "repository" in content["implementation"]["source"]
                    and "commit" in content["implementation"]["source"]
                    and "branch" in content["implementation"]["source"]
                ):
                    repo = content["implementation"]["source"]["repository"]
                    commit = content["implementation"]["source"]["commit"]
                    repo = repo.replace(".git", "")
                    if repo.startswith("git@"):
                        repo = repo.replace(":", "/")
                        repo = repo.replace("git@", "https://")

                    if commit:
                        repo = f"{repo}/tree/{commit}"

                    if (
                        "script" in content["implementation"]
                        and "path" in content["implementation"]["script"]
                        and not content["implementation"]["script"]["path"].startswith("/")
                    ):
                        repo += "/" + content["implementation"]["script"]["path"]

                    if not metadata_git_repo:
                        metadata_git_repo = repo
            except Exception:
                pass

    except Exception:
        pass

    notebook = load_notebook(Path(upload_dir))
    metadata_has_notebook = notebook is not None and ("notebook_html" in notebook)
    valid_formats: Optional[str] = json.dumps(report_valid_formats(Path(upload_dir)))
    if not valid_formats or len(valid_formats) <= 4:
        valid_formats = None
    return {
        "has_metadata": has_metadata,
        "metadata_git_repo": metadata_git_repo,
        "metadata_has_notebook": metadata_has_notebook,
        "valid_formats": valid_formats,
    }


@csrf_exempt
def anonymous_upload(request: "HttpRequest", dataset_id: str) -> HttpResponse:
    if request.method == "POST":
        if not dataset_id or dataset_id is None or dataset_id == "None":
            return HttpResponseServerError(
                json.dumps({"status": 1, "message": "Please specify the associated dataset."})
            )

        dataset = model.get_dataset(dataset_id)
        if (
            not dataset
            or "format" not in dataset
            or not dataset["format"]
            or "task" not in dataset
            or not dataset["task"]
        ):
            return HttpResponseServerError(
                json.dumps(
                    {"status": 1, "message": f"Uploads are not allowed for the dataset {html.escape(dataset_id)}."}
                )
            )

        if dataset["is_deprecated"]:
            return HttpResponseServerError(
                json.dumps(
                    {
                        "status": 1,
                        "message": f"The dataset {html.escape(dataset_id)} is deprecated and therefore allows no uploads.",
                    }
                )
            )

        task = model.get_task(dataset["task"], False)
        if not task or not task["featured"]:
            return HttpResponseServerError(
                json.dumps(
                    {
                        "status": 1,
                        "message": f"The dataset {html.escape(dataset_id)} is deprecated and therefore allows no uploads.",
                    }
                )
            )

        uploaded_file = request.FILES["file"]
        upload_id = str(uuid.uuid4())

        result_dir = temporary_directory()

        with open(result_dir / "upload.zip", "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        with zipfile.ZipFile(result_dir / "upload.zip", "r") as zip_ref:
            zip_ref.extractall(result_dir / "extracted")

        formats = dataset["format"]
        if len(formats) == 1:
            formats = formats[0]

        status_code, message = check_format(result_dir / "extracted", formats, dataset.get("format_configuration"))

        if status_code != _fmt.OK:
            return HttpResponseServerError(json.dumps({"status": 1, "message": message}))
        try:
            from .. import model as modeldb

            anon_uploads_dir = Path(settings.TIRA_ROOT) / "data" / "anonymous-uploads"
            (anon_uploads_dir).mkdir(exist_ok=True, parents=True)
            upload_dir = anon_uploads_dir / upload_id
            shutil.move(result_dir / "extracted", upload_dir)

            dataset = modeldb.Dataset.objects.get(dataset_id=dataset_id)
            metadata_from_upload = _parse_metadata_from_upload(upload_dir)
            modeldb.AnonymousUploads.objects.create(
                uuid=upload_id,
                dataset=dataset,
                has_metadata=metadata_from_upload["has_metadata"],
                metadata_git_repo=metadata_from_upload["metadata_git_repo"],
                metadata_has_notebook=metadata_from_upload["metadata_has_notebook"],
                valid_formats=metadata_from_upload["valid_formats"],
            )

            return JsonResponse({"status": 0, "message": "ok", "uuid": upload_id})
        except Exception as e:
            logger.warning("Could not create upload", e)
            return HttpResponseServerError(json.dumps({"status": 1, "message": "There was an error: {e}"}))
    else:
        return HttpResponseServerError(json.dumps({"status": 1, "message": "GET is not allowed here."}))


@check_permissions
@check_resources_exist("json")
def delete_upload(request: "HttpRequest", task_id: str, vm_id: str, upload_id: str) -> HttpResponse:
    try:
        model.delete_upload(task_id, vm_id, upload_id)
        return JsonResponse({"status": 0, "message": "ok"})
    except Exception as e:
        logger.warning("Failed to delete upload: " + str(e))
        logger.exception(e)
        return JsonResponse({"status": 0, "message": "Failed" + str(e)})


@check_permissions
@check_resources_exist("json")
def add_upload(request: "HttpRequest", task_id: str, vm_id: str) -> HttpResponse:
    if request.method == "GET":
        if not task_id or task_id is None or task_id == "None":
            return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})
        rename_to = request.GET.get("rename_to", None)
        rename_to = None if not rename_to or not rename_to.strip() else rename_to

        upload = model.add_upload(task_id, vm_id, rename_to)
        if not upload:
            return JsonResponse(
                {"status": 1, "message": "Failed to create a new Upload."}, status=HTTPStatus.INTERNAL_SERVER_ERROR
            )

        context = {"task": task_id, "vm_id": vm_id, "upload": upload}
        return JsonResponse({"status": 0, "message": "ok", "context": context})
    else:
        return JsonResponse({"status": 1, "message": "POST is not allowed here."})


@csrf_exempt
@check_permissions
@check_resources_exist("json")
def docker_software_add(request: "HttpRequest", task_id: str, vm_id: str) -> HttpResponse:
    if request.method == "POST":
        if not task_id or task_id is None or task_id == "None":
            return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})

        data = json.loads(request.body)
        if not data.get("image"):
            return JsonResponse({"status": 1, "message": "Please specify the associated docker image."})

        if not data.get("command"):
            return JsonResponse({"status": 1, "message": "Please specify the associated docker command."})

        source_code_remotes = data.get("source_code_remotes")
        commit = data.get("source_code_commit")
        active_branch = data.get("source_code_active_branch")

        if (source_code_remotes or commit or active_branch) and (
            not source_code_remotes or not commit or not active_branch
        ):
            return JsonResponse(
                {
                    "status": 1,
                    "message": "You must either specify always all three of source_code_remotes, "
                    + "commit, and active_branch or none of them. Got source_code_remotes="
                    + f"'{source_code_remotes}', commit='{commit}', active_branch='{active_branch}'.",
                }
            )

        if source_code_remotes:
            source_code_remotes = json.dumps(json.loads(source_code_remotes))

        submission_git_repo = None
        build_environment = None
        if data.get("code_repository_id"):
            submission_git_repo = model.model.get_submission_git_repo_or_none(
                data.get("code_repository_id"), vm_id, True
            )

            if not submission_git_repo:
                return JsonResponse(
                    {"status": 1, "message": f"The code repository '{data.get('code_repository_id'):}' does not exist."}
                )

            if not data.get("build_environment"):
                return JsonResponse(
                    {"status": 1, "message": "Please specify the build_environment for linking the code."}
                )

            build_environment = json.dumps(data.get("build_environment"))

        new_docker_software = model.add_docker_software(
            task_id,
            vm_id,
            data.get("image"),
            data.get("command"),
            data.get("inputJob", None),
            submission_git_repo,
            build_environment,
            source_code_remotes,
            commit,
            active_branch,
            data.get("try_run_metadata_uuid", None),
        )

        if data.get("mount_hf_model"):
            try:
                from ..huggingface_hub_integration import huggingface_model_mounts

                mounts = huggingface_model_mounts(data.get("mount_hf_model"))
                model.add_docker_software_mounts(new_docker_software, mounts)

            except Exception as e:
                return JsonResponse({"status": 1, "message": str(e)})

        return JsonResponse({"status": 0, "message": "ok", "context": new_docker_software})
    else:
        return JsonResponse({"status": 1, "message": "GET is not allowed here."})


@check_permissions
@check_resources_exist("json")
def docker_software_save(request: "HttpRequest", task_id: str, vm_id: str, docker_software_id: str) -> HttpResponse:
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            model.update_docker_software_metadata(
                docker_software_id,
                data.get("display_name"),
                data.get("description"),
                data.get("paper_link"),
                data.get("ir_re_ranker", False),
                data.get("ir_re_ranking_input", False),
            )
            return JsonResponse({"status": 0, "message": "Software edited successfully"})
        except Exception as e:
            return JsonResponse({"status": 1, "message": f"Error while editing software: {e}"})
    return JsonResponse({"status": 1, "message": "GET is not implemented for edit software"})


@check_permissions
def add_software_submission_git_repository(request: "HttpRequest", task_id: str, vm_id: str) -> HttpResponse:
    if request.method != "POST":
        return JsonResponse({"status": 1, "message": "GET is not implemented for edit upload"})

    try:
        data = json.loads(request.body)
        external_owner = data["external_owner"]
        private = not data.get("allow_public_repo", False)
        disraptor_user = get_disraptor_user(request, allow_unauthenticated_user=False)

        if not disraptor_user or not isinstance(disraptor_user, str):
            return JsonResponse({"status": 1, "message": "Please authenticate."})

        if not model.github_user_exists(external_owner):
            return JsonResponse(
                {"status": 1, "message": f"The user '{external_owner}' does not exist on Github, maybe a typo?"}
            )

        software_submission_git_repo = model.get_submission_git_repo(
            vm_id, task_id, disraptor_user, external_owner, private
        )

        return JsonResponse({"status": 0, "context": software_submission_git_repo})
    except Exception as e:
        logger.exception(e)
        logger.warning("Error while adding your git repository: " + str(e))
        return JsonResponse({"status": 1, "message": f"Error while adding your git repository: {e}"})


@check_permissions
def get_token(request: "HttpRequest", vm_id: str) -> HttpResponse:
    disraptor_user = get_disraptor_user(request, allow_unauthenticated_user=False)

    if not disraptor_user or not isinstance(disraptor_user, str):
        return JsonResponse({"status": 1, "message": "Please authenticate."})

    try:
        return JsonResponse(
            {"status": 0, "context": {"token": model.get_discourse_token_for_user(vm_id, disraptor_user)}}
        )
    except Exception:
        return JsonResponse(
            {"status": 1, "message": "Could not extract the discourse/disraptor user, please authenticate."}
        )


@check_permissions
def get_software_submission_git_repository(request: "HttpRequest", task_id: str, vm_id: str) -> HttpResponse:
    try:
        if task_id not in settings.CODE_SUBMISSION_REFERENCE_REPOSITORIES or not model.load_docker_data(
            task_id, vm_id, cache, force_cache_refresh=False
        ):
            return JsonResponse({"status": 0, "context": {"disabled": True}})

        return JsonResponse({"status": 0, "context": model.get_submission_git_repo(vm_id, task_id)})
    except Exception as e:
        logger.exception(e)
        logger.warning("Error while getting your git repository: " + str(e))
        return JsonResponse({"status": 1, "message": f"Error while getting your git repository: {e}"})


@check_permissions
@check_resources_exist("json")
def upload_save(request: "HttpRequest", task_id: str, vm_id: str, upload_id: str) -> HttpResponse:
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            model.update_upload_metadata(
                task_id, vm_id, upload_id, data.get("display_name"), data.get("description"), data.get("paper_link")
            )
            return JsonResponse({"status": 0, "message": "Software edited successfully"})
        except Exception as e:
            logger.exception(e)
            logger.warning("Error while editing upload: " + str(e))
            return JsonResponse({"status": 1, "message": f"Error while editing upload: {e}"})
    return JsonResponse({"status": 1, "message": "GET is not implemented for edit upload"})


@check_permissions
@check_resources_exist("json")
def docker_software_delete(request: "HttpRequest", task_id: str, vm_id: str, docker_software_id: str) -> HttpResponse:
    delete_ok = model.delete_docker_software(task_id, vm_id, docker_software_id)

    if delete_ok:
        return JsonResponse({"status": 0}, status=HTTPStatus.ACCEPTED)
    else:
        return JsonResponse(
            {
                "status": 1,
                "message": (
                    "Cannot delete docker software, because it has a valid evaluation assigned (or it does not exist.)"
                ),
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )


def __normalize_command(cmd: str, evaluator: str) -> str:
    to_normalize = {
        "inputRun": "/tira-data/input-run",
        "outputDir": "/tira-data/output",
        "inputDataset": "/tira-data/input",
    }

    if "inputRun" in cmd and evaluator:
        to_normalize["outputDir"] = "/tira-data/eval_output"
        to_normalize["inputDataset"] = "/tira-data/input_truth"

    for k, v in to_normalize.items():
        cmd = cmd.replace("$" + k, v).replace("${" + k + "}", v)

    return cmd


def __construct_verbosity_output(image: str, command: str, approach: str, task: str, dataset: str) -> dict[str, str]:
    command = __normalize_command(command, "")
    return {
        "tira_run_export": f"tira-run --export-dataset {task}/{dataset} --output-directory tira-dataset",
        "cli_command": "tira-run \\\n  --input-directory tira-dataset \\\n  --output-directory tira-output \\\n  "
        + "--approach '"
        + approach
        + "'",
        "python_command": f'tira.run("{approach}", "tira-dataset")',
        "docker_command": (
            "docker run --rm -ti \\\n  -v ${PWD}/tira-dataset:/tira-data/input:ro \\\n  -v "
            "${PWD}/tira-output:/tira-data/output:rw -\\\n  -entrypoint sh "
        )
        + f"\\\n  t{image} \\\n  -c '{command}'",
        "image": image,
        "command": command,
    }


def __rendered_references(task_id: str, vm_id: str, run: dict[str, str]) -> tuple[str, str]:
    task = model.get_task(task_id)
    bib_references = {
        "run": "@Comment {No bib entry specified for the run, please contact the team/organizers for clarification.}",
        "task": "@Comment {No bib entry specified for the task, please contact the organizers for clarification.}",
        "dataset": (
            "@Comment {No bib entry specified for the dataset, please contact the organizers for clarification.}"
        ),
    }
    markdown_references: dict[str, Optional[str]] = {"run": None, "task": None, "dataset": None}

    if run["dataset"] == "antique-test-20230107-training":
        markdown_references["dataset"] = (
            "[ANTIQUE](https://ir.webis.de/anthology/2020.ecir_conference-20202.21/) "
            + "is a  non-factoid quesiton answering dataset based on the questions and "
            + "answers of Yahoo! Webscope L6."
        )
        bib_references[
            "dataset"
        ] = """@inproceedings{Hashemi2020Antique,
  title        = {ANTIQUE: A Non-Factoid Question Answering Benchmark},
  author       = {Helia Hashemi and Mohammad Aliannejadi and Hamed Zamani and Bruce Croft},
  booktitle    = {ECIR},
  year         = {2020}
}"""

    if task_id == "ir-benchmarks":
        markdown_references["task"] = (
            "[TIRA](https://webis.de/publications?q=TIRA#froebe_2023b) "
            + "respectively [TIREx](https://webis.de/publications#froebe_2023e) "
            + "is used to enable reprodicible and blinded experiments."
        )
        bib_references[
            "task"
        ] = """@InProceedings{froebe:2023b,
  address =                  {Berlin Heidelberg New York},
  author =                   {Maik Fr{\"o}be and Matti Wiegmann and Nikolay Kolyada and Bastian Grahm and Theresa Elstner and Frank Loebe and Matthias Hagen and Benno Stein and Martin Potthast},
  booktitle =                {Advances in Information Retrieval. 45th European Conference on {IR} Research ({ECIR} 2023)},
  doi =                      {10.1007/978-3-031-28241-6_20},
  editor =                   {Jaap Kamps and Lorraine Goeuriot and Fabio Crestani and Maria Maistro and Hideo Joho and Brian Davis and Cathal Gurrin and Udo Kruschwitz and Annalina Caputo},
  month =                    apr,
  pages =                    {236--241},
  publisher =                {Springer},
  series =                   {Lecture Notes in Computer Science},
  site =                     {Dublin, Irland},
  title =                    {{Continuous Integration for Reproducible Shared Tasks with TIRA.io}},
  todo =                     {pages, code},
  url =                      {https://doi.org/10.1007/978-3-031-28241-6_20},
  year =                     2023
}

@InProceedings{froebe:2023e,
  author =                   {Maik Fr{\"o}be and {Jan Heinrich} Reimer and Sean MacAvaney and Niklas Deckers and Simon Reich and Janek Bevendorff and Benno Stein and Matthias Hagen and Martin Potthast},
  booktitle =                {46th International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR 2023)},
  month =                    jul,
  publisher =                {ACM},
  site =                     {Taipei, Taiwan},
  title =                    {{The Information Retrieval Experiment Platform}},
  todo =                     {annote, doi, editor, pages, url, videourl},
  year =                     2023
}"""

    if run["software"] == "MonoT5 3b (tira-ir-starter-gygaggle)":
        markdown_references["run"] = (
            "The implementation of [MonoT5](https://arxiv.org/abs/2101.05667) in"
            " [PyGaggle](https://ir.webis.de/anthology/2021.sigirconf_conference-2021.304/)."
        )
        bib_references[
            "run"
        ] = """@article{DBLP:journals/corr/abs-2101-05667,
  author       = {Ronak Pradeep and Rodrigo Frassetto Nogueira and Jimmy Lin},
  title        = {The Expando-Mono-Duo Design Pattern for Text Ranking with Pretrained Sequence-to-Sequence Models},
  journal      = {CoRR},
  volume       = {abs/2101.05667},
  year         = {2021},
  url          = {https://arxiv.org/abs/2101.05667},
  eprinttype    = {arXiv},
  eprint       = {2101.05667},
  timestamp    = {Mon, 20 Mar 2023 15:35:34 +0100},
  biburl       = {https://dblp.org/rec/journals/corr/abs-2101-05667.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}

@inproceedings{lin-2021-pyserini,
  author    = {Jimmy Lin and Xueguang Ma and Sheng{-}Chieh Lin and Jheng{-}Hong Yang and Ronak Pradeep and Rodrigo Frassetto Nogueira},
  editor    = {Fernando Diaz and Chirag Shah and Torsten Suel and Pablo Castells and Rosie Jones and Tetsuya Sakai},
  title     = {Pyserini: {A} Python Toolkit for Reproducible Information Retrieval Research with Sparse and Dense Representations},
  booktitle = {{SIGIR} '21: The 44th International {ACM} {SIGIR} Conference on Research and Development in Information Retrieval, Virtual Event, Canada, July 11-15, 2021},
  pages     = {2356--2362},
  publisher = {{ACM}},
  year      = {2021},
  url       = {https://doi.org/10.1145/3404835.3463238},
  doi       = {10.1145/3404835.3463238},
  timestamp = {Mon, 20 Mar 2023 15:35:34 +0100},
  biburl    = {https://dblp.org/rec/conf/sigir/LinMLYPN21.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}"""

    if run["software"] == "DLH (tira-ir-starter-pyterrier)":
        markdown_references["run"] = (
            "The implementation of [DLH](https://ir.webis.de/anthology/2006.ecir_conference-2006.3/) in"
            " [PyTerrier](https://ir.webis.de/anthology/2021.cikm_conference-2021.533/)."
        )
        bib_references[
            "run"
        ] = """@inproceedings{amati-2006-frequentist,
  author    = {Giambattista Amati},
  editor    = {Mounia Lalmas and Andy MacFarlane and Stefan M. R{\"{u}}ger and Anastasios Tombros and Theodora Tsikrika and Alexei Yavlinsky},
  title     = {Frequentist and Bayesian Approach to Information Retrieval},
  booktitle = {Advances in Information Retrieval, 28th European Conference on {IR} Research, {ECIR} 2006, London, UK, April 10-12, 2006, Proceedings},
  series    = {Lecture Notes in Computer Science},
  volume    = {3936},
  pages     = {13--24},
  publisher = {Springer},
  year      = {2006},
  url       = {https://doi.org/10.1007/11735106\\_3},
  doi       = {10.1007/11735106\\_3},
  timestamp = {Tue, 14 May 2019 10:00:37 +0200},
  biburl    = {https://dblp.org/rec/conf/ecir/Amati06.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}

@inproceedings{macdonald-2021-pyterrier,
  author    = {Craig Macdonald and Nicola Tonellotto and Sean MacAvaney and Iadh Ounis},
  editor    = {Gianluca Demartini and Guido Zuccon and J. Shane Culpepper and Zi Huang and Hanghang Tong},
  title     = {PyTerrier: Declarative Experimentation in Python from {BM25} to Dense
               Retrieval},
  booktitle = {{CIKM} '21: The 30th {ACM} International Conference on Information and Knowledge Management, Virtual Event, Queensland, Australia, November 1 - 5, 2021},
  pages     = {4526--4533},
  publisher = {{ACM}},
  year      = {2021},
  url       = {https://doi.org/10.1145/3459637.3482013},
  doi       = {10.1145/3459637.3482013},
  timestamp = {Tue, 02 Nov 2021 12:01:17 +0100},
  biburl    = {https://dblp.org/rec/conf/cikm/MacdonaldTMO21.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}"""

    print(run)
    ret_bib = ""
    ret_markdown: list[str] = ["Please cite the approach / resources if you use them. Potential candidates are:"]
    missing_references: list[str] = []
    for t in ["run", "dataset", "task"]:
        ret_bib += bib_references[t] + "\n\n"
        if (ref := markdown_references[t]) is not None:
            ret_markdown.append(ref)
        else:
            missing_references.append(t)

    if missing_references:
        ret_markdown += [
            "There are missing references for "
            + ", ".join(missing_references)
            + ". "
            + "Please contact the organizers "
            + f'[{task["organizer"]}](https://www.tira.io/g/tira_org_{task["organizer_id"]}) or the team '
            + f"[{vm_id}]({link_to_discourse_team(vm_id)}) for clarification."
        ]

    return ret_bib.strip(), markdown("<br>".join(ret_markdown).strip())


@check_permissions
@check_resources_exist("json")
def run_details(request: "HttpRequest", task_id: str, vm_id: str, run_id: str) -> HttpResponse:
    run = model.get_run(dataset_id=None, vm_id=vm_id, run_id=run_id)
    software: Optional[dict[str, Any]] = None
    docker_software: Optional[dict[str, Any]] = None
    run_upload = None
    vm_id_from_run = None

    repro_details: Mapping[str, Optional[str]] = {
        "tira-run-export": None,
        "tira-run-cli": None,
        "tira-run-python": None,
        "docker": None,
    }

    if "software_id" in run and run["software_id"]:
        software = model.get_software(task_id, vm_id, run["software_id"])
        vm_id_from_run = software["vm"]
    elif "docker_software_id" in run and run["docker_software_id"]:
        docker_software = model.get_docker_software(run["docker_software_id"])
        print(docker_software)
        vm_id_from_run = docker_software["vm_id"]

        if docker_software["public_image_name"]:
            repro_details = __construct_verbosity_output(
                docker_software["public_image_name"],
                docker_software["command"],
                task_id + "/" + vm_id + "/" + docker_software["display_name"],
                task_id,
                run["dataset"],
            )

    elif "upload_id" in run and run["upload_id"]:
        from .. import model as modeldb

        run_upload = modeldb.Upload.objects.filter(vm__vm_id=vm_id, id=run["upload_id"]).get()
        vm_id_from_run = run_upload.vm.vm_id

    if not vm_id_from_run or vm_id != vm_id_from_run:
        return HttpResponseNotAllowed("Access forbidden.")

    ret = {
        "description": "No description is available.",
        "previous_stage": None,
        "cli_command": None,
        "docker_command": None,
        "python_command": None,
    }

    ret["references_bibtex"], ret["references_markdown"] = __rendered_references(task_id, vm_id, run)

    for k, v in repro_details.items():
        ret[k] = v

    return JsonResponse({"status": 0, "context": ret})


@check_permissions
@check_resources_exist("json")
def software_details(request: "HttpRequest", task_id: str, vm_id: str, software_name: str) -> HttpResponse:
    docker_software = model.get_docker_software_by_name(software_name, vm_id, task_id)

    if not docker_software:
        return JsonResponse({"status": 0, "message": f'Could not find a software with name "{software_name}"'})

    repro_details: Mapping[str, Optional[str]] = {
        "tira-run-export": None,
        "tira-run-cli": None,
        "tira-run-python": None,
        "docker": None,
        "image": None,
        "command": None,
    }
    if docker_software["public_image_name"]:
        repro_details = __construct_verbosity_output(
            docker_software["public_image_name"],
            docker_software["command"],
            task_id + "/" + vm_id + "/" + docker_software["display_name"],
            task_id,
            "<dataset>",
        )

    ret = {
        "description": "No description is available.",
        "previous_stage": None,
        "cli_command": "TBD cli.",
        "docker_command": "TBD docker.",
        "python_command": "TBD python.",
    }

    for k, v in repro_details.items():
        ret[k] = v

    return JsonResponse({"status": 0, "context": ret})


@check_permissions
@check_resources_exist("json")
def run_execute_docker_software(
    request: "HttpRequest",
    task_id: "Optional[str]",
    vm_id: "Optional[str]",
    dataset_id: str,
    docker_software_id: "Optional[str]",
    docker_resources: str,
    rerank_dataset: "Optional[str]" = None,
) -> HttpResponse:
    if not task_id or task_id is None or task_id == "None":
        return JsonResponse({"status": 1, "message": "Please specify the associated task_id."})

    if not vm_id or vm_id is None or vm_id == "None":
        return JsonResponse({"status": 1, "message": "Please specify the associated vm_id."})

    if not docker_software_id or docker_software_id is None or docker_software_id == "None":
        return JsonResponse({"status": 1, "message": "Please specify the associated docker_software_id."})

    docker_software = model.get_docker_software(int(docker_software_id))

    if not docker_software:
        return JsonResponse({"status": 1, "message": f"There is no docker image with id {docker_software_id}"})

    input_run = None
    if (
        "ir_re_ranker" in docker_software
        and docker_software.get("ir_re_ranker", False)
        and rerank_dataset
        and rerank_dataset.lower() != "none"
    ):
        reranking_datasets = model.get_all_reranking_datasets()

        if rerank_dataset not in reranking_datasets:
            background_process = None
            try:
                background_process = model.create_re_rank_output_on_dataset(
                    task_id, vm_id, software_id=None, docker_software_id=int(docker_software_id), dataset_id=dataset_id
                )
            except Exception as e:
                logger.warning(e)

            visit_job_message = "Failed to start job."

            # TODO: what is a new URL for that?
            if background_process:
                visit_job_message = (
                    f"Please visit https://tira.io/background_jobs/{task_id}/{background_process} "
                    + " to view the progress of the job that creates the rerank output."
                )

            return JsonResponse(
                {
                    "status": 1,
                    "message": (
                        f"The execution of your software depends on the reranking dataset {rerank_dataset}"
                        f", but {rerank_dataset} was never executed on the dataset {dataset_id}. "
                        "Please execute first the software on the specified dataset so that you can re-rank it. "
                        f"{visit_job_message}"
                    ),
                }
            )

        input_run = reranking_datasets[rerank_dataset]
        input_run["replace_original_dataset"] = True

        if dataset_id != input_run["dataset_id"]:
            return JsonResponse(
                {
                    "status": 1,
                    "message": "There seems to be a configuration error:"
                    + f" The reranking dataset {input_run['dataset_id']} is not"
                    + f" the specified dataset {dataset_id}.",
                }
            )

        assert dataset_id == input_run["dataset_id"]

    if not dataset_id or dataset_id is None or dataset_id == "None":
        return JsonResponse({"status": 1, "message": "Please specify the associated dataset_id."})

    evaluator = model.get_evaluator(dataset_id)

    if (
        not evaluator
        or "is_git_runner" not in evaluator
        or not evaluator["is_git_runner"]
        or "git_runner_image" not in evaluator
        or not evaluator["git_runner_image"]
        or "git_runner_command" not in evaluator
        or not evaluator["git_runner_command"]
        or "git_repository_id" not in evaluator
        or not evaluator["git_repository_id"]
    ):
        return JsonResponse(
            {"status": 1, "message": "The dataset is misconfigured. Docker-execute only available for git-evaluators"}
        )

    input_runs, errors = model.get_ordered_input_runs_of_software(docker_software, task_id, dataset_id, vm_id)

    if errors:
        return JsonResponse({"status": 1, "message": errors[0]})

    git_runner = model.get_git_integration(task_id=task_id)
    git_runner.run_docker_software_with_git_workflow(
        task_id,
        dataset_id,
        vm_id,
        get_tira_id(),
        evaluator["git_runner_image"],
        evaluator["git_runner_command"],
        evaluator["git_repository_id"],
        evaluator["evaluator_id"],
        docker_software["tira_image_name"],
        docker_software["command"],
        "docker-software-" + docker_software_id,
        docker_resources,
        input_run if input_run else input_runs,
        docker_software.get("mount_hf_model", None),
        docker_software.get("tira_image_workdir", None),
    )

    running_pipelines = git_runner.all_running_pipelines_for_repository(
        evaluator["git_repository_id"], cache, force_cache_refresh=True
    )
    print(
        "Refreshed Cache for repo "
        + str(evaluator["git_repository_id"])
        + " with "
        + str(len(running_pipelines))
        + " jobs."
    )

    return JsonResponse({"status": 0}, status=HTTPStatus.ACCEPTED)


@check_permissions
def stop_docker_software(request: "HttpRequest", task_id: str, user_id: str, run_id: str) -> HttpResponse:
    if not request.method == "GET":
        return JsonResponse({"status": 1, "message": "Only GET is allowed here"})
    else:
        datasets = model.get_datasets_by_task(task_id)
        git_runner = model.get_git_integration(task_id=task_id)

        if not git_runner:
            return JsonResponse({"status": 1, "message": f"No git integration found for task {task_id}"})

        for dataset in datasets:
            git_runner.stop_job_and_clean_up(
                model.get_evaluator(dataset["dataset_id"])["git_repository_id"], user_id, run_id, cache
            )

        return JsonResponse({"status": 0, "message": "Run successfully stopped"})
