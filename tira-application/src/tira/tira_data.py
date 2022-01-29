from pathlib import Path
import logging
from django.conf import settings

logger = logging.getLogger("tira")

DATA_ROOT = Path(settings.TIRA_ROOT) / "data"
RUNS_DIR_PATH = DATA_ROOT / "runs"


def get_run_runtime(dataset_id, vm_id, run_id):
    """ loads a runtime file (runtime.txt) and parses the string to return time, runtime_info"""
    run_dir = (RUNS_DIR_PATH / dataset_id / vm_id / run_id)
    if not (run_dir / "runtime.txt").exists():
        return None

    runtime = open(run_dir / "runtime.txt", 'r').read()
    try:
        time = runtime.split(" ")[2].strip("elapsed")
        cpu = runtime.split(" ")[3]
        pagefaults = runtime.split(" ")[6].strip("pagefaults").strip("(").strip(")")
        swaps = runtime.split(" ")[7].strip("swaps")
    except IndexError as e:
        logger.exception(f"IndexError while parsing the runtime file {run_dir}/runtime.txt: {e}")
        time = None
        cpu = None
        pagefaults = None
        swaps = None

    return {"runtime": runtime, "time": time, "cpu": cpu, "pagefaults": pagefaults, "swaps": swaps}


def get_run_file_list(dataset_id, vm_id, run_id):
    """ load the 2 files that describe the outputof a run:
    - file-list.txt (ascii-view of the files) and
    - size.txt (has line count, file count, subdir count)

    returns a dict with the variables: size, lines, fines, dirs, file_list
    """
    run_dir = (RUNS_DIR_PATH / dataset_id / vm_id / run_id)
    try:
        size = open(run_dir / "size.txt").read().split("\n")
    except Exception as e:
        logger.error(f"Failed to read output size.txt of: {dataset_id} -- {vm_id} -- {run_id}\n"
                     f"with error: {e}")
        size = ["No output could be found for this run or output was corrupted", None, None, None, None]

    if not (run_dir / "file-list.txt").exists():
        file_list = ["", "There are no files in the Output"]
    else:
        file_list = open(run_dir / "file-list.txt").read().split("\n")

    return {"size": size[1], "lines": size[2], "files": size[3], "dirs": size[4], "file_list": file_list}


def get_stdout(dataset_id, vm_id, run_id):
    # TODO: Don't open whole file but only read the n last lines to not have a full xGB file in memory
    output_lines = 100
    run_dir = (RUNS_DIR_PATH / dataset_id / vm_id / run_id)
    if not (run_dir / "stdout.txt").exists():
        return "No Stdout recorded"
    with open(run_dir / "stdout.txt", 'r') as stdout_file:
        stdout = stdout_file.readlines()
        stdout_len = len(stdout)
        stdout = ''.join([f"[{max(stdout_len - output_lines, 0)} more lines]\n"] + stdout[-output_lines:])
    if not stdout:
        return "No Stdout recorded"
    return stdout


def get_stderr(dataset_id, vm_id, run_id):
    run_dir = (RUNS_DIR_PATH / dataset_id / vm_id / run_id)
    if not (run_dir / "stderr.txt").exists():
        return "No Stderr recorded"
    stderr = open(run_dir / "stderr.txt", 'r').read()
    if not stderr:
        return "No Stderr recorded"
    return stderr


def get_tira_log(dataset_id, vm_id, run_id):
# TODO: read log once it has a fixed position
#     log_path = 
#     with open(log_path, 'r') as log:
#         l = log.read()
#     return l
    return "foo"
