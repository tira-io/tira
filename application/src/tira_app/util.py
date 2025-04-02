import logging
from datetime import datetime as dt
from datetime import timezone
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings

from .proto import TiraClientWebMessages_pb2 as modelpb

if TYPE_CHECKING:
    from typing import Any, Callable, Optional

    from google.protobuf.message import Message

logger = logging.getLogger("tira")


class TiraModelWriteError(Exception):
    pass


class TiraModelIntegrityError(Exception):
    pass


def get_tira_id() -> str:
    return dt.now().strftime("%Y-%m-%d-%H-%M-%S")


def get_today_timestamp() -> str:
    return dt.now().strftime("%Y%m%d")


def now() -> str:
    return dt.now(timezone.utc).strftime("%a %b %d %X %Z %Y")


def extract_year_from_dataset_id(dataset_id: str) -> str:
    try:
        splits = dataset_id.split("-")
        return splits[-3] if len(splits) > 3 and (1990 <= int(splits[-3])) else ""
    except IndexError:
        return ""
    except ValueError:
        return ""


def reroute_host(hostname: str) -> str:
    """If we use a local deployment and use a local (mock) host, we need to change all hostnames to localhost.
    Otherwise we may contact the real vm-hosts while developing.
    """
    return "localhost" if settings.GRPC_HOST == "local" else hostname


def auto_reviewer(review_path: Path, run_id: str) -> "Message":
    """Do standard checks for reviews so we do not need to wait for a reviewer to check for:
    - failed runs (
    """
    review_file = review_path / "run-review.bin"
    review = modelpb.RunReview()

    if review_file.exists():  # TODO this will throw if the file is corrupt. Let it throw to not overwrite files.
        try:
            review.ParseFromString(open(review_file, "rb").read())
            return review
        except Exception as e:
            logger.exception(f"review file: {review_file} exists but is corrupted with {e}")
            raise FileExistsError(f"review file: {review_file} exists but is corrupted with {e}")

    review.runId = run_id
    review.reviewerId = "tira"
    review.reviewDate = str(dt.utcnow())
    review.hasWarnings = False
    review.hasErrors = False
    review.hasNoErrors = False
    review.blinded = True

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
            review.missingOutput = True
            review.hasErrorOutput = True

    except Exception as e:
        review_path.mkdir(parents=True, exist_ok=True)
        review.reviewerId = "tira"
        review.comment = f"Internal Error: {e}. Please contact the support."
        review.hasErrors = True
        review.hasNoErrors = False
        review.blinded = False

    return review


def run_cmd(cmd: str, ignore_failure: bool = False) -> None:
    import subprocess

    exit_code = subprocess.call(cmd)

    if not ignore_failure and exit_code != 0:
        raise ValueError(f"Command {cmd} did exit with return code {exit_code}.")


def link_to_discourse_team(vm_id: str) -> str:
    if not vm_id.endswith("-default"):
        return "https://www.tira.io/g/tira_vm_" + vm_id
    else:
        return "https://www.tira.io/u/" + vm_id.split("-default")[0]


def register_run(dataset_id: str, vm_id: str, run_id: str, software_id: str) -> None:
    # import tira_model has to be done here since it has a side-effect with django and throws
    # django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
    # if it is imported before django is launched otherwise.
    from . import tira_model

    path_for_run = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / run_id

    with open(path_for_run / "run.prototext", "w") as f:
        f.write(
            f'\nsoftwareId: "{software_id}"\nrunId: "{run_id}"\ninputDataset: "{dataset_id}"\ndownloadable:'
            " true\ndeleted: false\n"
        )

    tira_model.add_run(dataset_id=dataset_id, vm_id=vm_id, run_id=run_id)


def __run_cmd_as_documented_background_process(
    cmds: list[list[str]], process_id: int, descriptions: str, callback: Optional[Callable[[], None]]
) -> None:
    import datetime
    import tempfile
    from subprocess import STDOUT, Popen
    from time import sleep

    from . import model as modeldb

    with tempfile.NamedTemporaryFile() as file:
        file.write("".encode("utf8"))
        for cmd, description in zip(cmds, descriptions):
            process = Popen(cmd, stdout=file, stderr=STDOUT, stdin=None, close_fds=True, text=True)
            while process.poll() is None:
                sleep(4)
                stdout = open(file.name, "rt").read()
                last_contact = datetime.datetime.now()
                modeldb.BackendProcess.objects.filter(id=process_id).update(stdout=stdout, last_contact=last_contact)

            exit_code = process.poll()
            stdout = open(file.name, "rt").read()
            last_contact = datetime.datetime.now()
            modeldb.BackendProcess.objects.filter(id=process_id).update(
                stdout=stdout, exit_code=exit_code, last_contact=last_contact
            )

            if exit_code != 0:
                return

        if callback:
            callback()


def run_cmd_as_documented_background_process(
    cmd: list[list[str]],
    vm_id: "Optional[str]",
    task_id: str,
    title: str,
    descriptions: list[str],
    callback: Optional[Callable[[], None]] = None,
) -> int:
    """
    Usage: # run_cmd_forwarding(['sh', '-c', 'echo "1"; sleep 2s; echo "2"; sleep 2s; echo "3"; sleep 2s; echo "4"'])
    """
    import json
    import threading

    from . import model as modeldb

    process_id = modeldb.BackendProcess.objects.create(
        vm_id=vm_id, task_id=task_id, cmd=json.dumps(cmd), title=title
    ).id

    thread = threading.Thread(
        target=__run_cmd_as_documented_background_process,
        name=f"Process-{process_id}",
        args=(cmd, process_id, descriptions, callback),
    )
    thread.start()

    return process_id


def docker_image_details(image: str) -> dict[str, Any]:
    import json
    import subprocess

    ret = subprocess.check_output(["podman", "image", "inspect", image])
    retjson = json.loads(ret)
    if len(ret) != 1:
        raise ValueError(f"Could not handle {retjson}")
    firstret = retjson[0]
    image_id = firstret["Id"] if ":" not in firstret["Id"] else firstret["Id"].split(":")[1]
    return {"image_id": image_id, "size": firstret["Size"], "virtual_size": firstret["VirtualSize"]}


def str2bool(text: str) -> bool:
    """
    Extracts the boolean meaning of the given text. A string of the form "yes", "y", "true", "t", and "1" is
    considered to express the boolean value True. The string may be in upper case as well (e.g., TRUE or True) and may
    be surrounded by whitespaces. Any value that is not considered true, will return false.
    """
    return text.strip().lower() in ("yes", "y", "true", "t", "1")
