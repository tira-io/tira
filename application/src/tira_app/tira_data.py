import logging
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings

from .endpoints.stdout_beautifier import beautify_ansi_text

logger = logging.getLogger("tira")

if TYPE_CHECKING:
    from typing import Any, Optional, Sequence

DATA_ROOT = Path(settings.TIRA_ROOT) / "data"
RUNS_DIR_PATH = DATA_ROOT / "runs"


def get_run_runtime(dataset_id: str, vm_id: str, run_id: str) -> dict[str, str]:
    """loads a runtime file (runtime.txt) and parses the string to return time, runtime_info"""
    run_dir = RUNS_DIR_PATH / dataset_id / vm_id / run_id
    context = {"time": "0", "cpu": "0", "pagefaults": "0", "swaps": "0", "error": ""}
    if not (run_dir / "runtime.txt").is_file():
        return context

    runtime = (run_dir / "runtime.txt").read_text()
    try:
        context["time"] = runtime.split(" ")[2].strip("elapsed")
        context["cpu"] = runtime.split(" ")[3]
        context["pagefaults"] = runtime.split(" ")[6].strip("pagefaults").strip("(").strip(")")
        context["swaps"] = runtime.split(" ")[7].strip("swaps")
    except IndexError as e:
        logger.exception(f"IndexError while parsing the runtime file {run_dir}/runtime.txt: {e}")
        context["error"] = "IndexError while parsing the runtime file {run_dir}/runtime.txt"

    return context


def get_run_file_list(dataset_id: str, vm_id: str, run_id: str) -> "dict[str, Any]":
    """load the 2 files that describe the outputof a run:
    - file-list.txt (ascii-view of the files) and
    - size.txt (has line count, file count, subdir count)

    returns a dict with the variables: size, lines, fines, dirs, file_list
    """
    run_dir = RUNS_DIR_PATH / dataset_id / vm_id / run_id
    try:
        size: list[Optional[str]] = (run_dir / "size.txt").read_text().split("\n")  # type: ignore [assignment]
    except Exception as e:
        logger.error(f"Failed to read output size.txt of: {dataset_id} -- {vm_id} -- {run_id}\nwith error: {e}")
        size = ["No output could be found for this run or output was corrupted", None, None, None, None]

    if not (run_dir / "file-list.txt").exists():
        file_list = ["", "There are no files in the Output"]
    else:
        file_list = (run_dir / "file-list.txt").read_text().split("\n")
    if len(size) < 5:
        size.extend(["0"] * (5 - len(size)))

    return {"size": size[1], "lines": size[2], "files": size[3], "dirs": size[4], "file_list": file_list}


def get_stdout(dataset_id: str, vm_id: str, run_id: str) -> str:
    # TODO: Don't open whole file but only read the n last lines to not have a full xGB file in memory
    output_lines = 100
    run_dir = RUNS_DIR_PATH / dataset_id / vm_id / run_id
    if not (run_dir / "stdout.txt").exists():
        return "No Stdout recorded"
    with open(run_dir / "stdout.txt", "r") as stdout_file:
        stdout = stdout_file.readlines()
        stdout_len = len(stdout)
        stdout_joined = "".join([f"[{max(stdout_len - output_lines, 0)} more lines]\n"] + stdout[-output_lines:])
    if not stdout_joined:
        return "No Stdout recorded"
    return beautify_ansi_text(stdout_joined)


def get_stderr(dataset_id: str, vm_id: str, run_id: str) -> str:
    run_dir = RUNS_DIR_PATH / dataset_id / vm_id / run_id
    if not (run_dir / "stderr.txt").exists():
        return "No Stderr recorded"
    stderr = (run_dir / "stderr.txt").read_text()
    if not stderr:
        return "No Stderr recorded"
    return beautify_ansi_text(stderr)


def get_tira_log(dataset_id: str, vm_id: str, run_id: str) -> str:
    # TODO: read log once it has a fixed position
    #     log_path =
    #     with open(log_path, 'r') as log:
    #         l = log.read()
    #     return l
    return "foo"
