import gzip
import io
import json
import logging
import os
import uuid
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from glob import glob
from pathlib import Path
from subprocess import check_output
from typing import Any, Dict, Generator, Iterable, List, Optional, Union

import pandas as pd

from tira.check_format import _fmt, log_message
from tira.tira_client import TiraClient


def dataset_as_dataframe(
    dataset_id_or_path: "Union[str, Path]", dataset_format: str, tira_client: "Optional[TiraClient]" = None
):
    """Load all entries in a dataset (either a local directory passed as Path or the TIRA ID of a dataset) in the specified format.

    Args:
        dataset_id_or_path (Union[str, Path]): the dataset that should be iterated, either as a path to a local dataset directory or the ID of a TIRA dataset.
        dataset_format (str): The format of the dataset.
        tira_client (TiraClient, optional): The rest API client to load the dataset in case the dataset is provided as ID. Defaults to None to use the default REST API.

    Returns:
        pd.DataFrame: The entries in the dataset parsed into a pandas DataFrame.
    """
    import pandas as pd

    ret = [i for i in dataset_as_iterator(dataset_id_or_path, dataset_format, tira_client)]
    return pd.DataFrame(ret)


def dataset_as_iterator(
    dataset_id_or_path: "Union[str, Path]", dataset_format: str, tira_client: "Optional[TiraClient]" = None
):
    """Load all entries in a dataset (either a local directory passed as Path or the TIRA ID of a dataset) in the specified format.

    Args:
        dataset_id_or_path (Union[str, Path]): the dataset that should be iterated, either as a path to a local dataset directory or the ID of a TIRA dataset.
        dataset_format (str): The format of the dataset.
        tira_client (TiraClient, optional): The rest API client to load the dataset in case the dataset is provided as ID. Defaults to None to use the default REST API.

    Yields:
        ANY: the entries in the dataset parsed in the specified format.
    """
    if Path(dataset_id_or_path).exists():
        dataset = Path(dataset_id_or_path)
    else:
        if tira_client is None:
            from tira.rest_api_client import Client

            tira_client = Client()

        dataset = Path(tira_client.download_dataset(dataset=dataset_id_or_path, task=None, allow_local_dataset=True))
    from tira.check_format import lines_if_valid

    for i in lines_if_valid(dataset, dataset_format):
        yield i


def verify_docker_installation():
    try:
        from tira.local_execution_integration import LocalExecutionIntegration

        local_execution = LocalExecutionIntegration()
        assert local_execution.docker_is_installed_failsave()
        return _fmt.OK, "Docker/Podman is installed."
    except:
        return _fmt.ERROR, "Docker/Podman is not installed. You can not run dockerized TIRA submissions."


def tira_home_exists():
    try:
        from tira.rest_api_client import Client

        assert Path(Client().tira_cache_dir).exists()
        return _fmt.OK, "TIRA home is writable."
    except:
        return _fmt.ERROR, "TIRA can not write data to disk, ensure that TIRA_CACHE_DIR is writable."


def api_key_is_valid():
    try:
        from tira.rest_api_client import Client

        assert Client().api_key_is_valid()
        return _fmt.OK, "You are authenticated against www.tira.io."
    except:
        return _fmt.WARN, "Your TIRA client is not authenticated. Please run 'tira-cli login'."


def verify_tirex_tracker():
    return _fmt.OK, "The tirex-tracker works and will track experimental metadata."


def verify_tira_installation():
    ret = _fmt.OK

    for i in [api_key_is_valid, tira_home_exists, verify_docker_installation, verify_tirex_tracker]:
        status, msg = i()
        log_message(msg, status)
        if status == _fmt.ERROR:
            ret = _fmt.ERROR
        if status == _fmt.WARN and ret != _fmt.ERROR:
            ret = _fmt.WARN

    return ret


def parse_jsonl_line(input: Union[str, bytearray, bytes], load_default_text: bool) -> Dict:
    """
    Deseralizes the line using JSON deserialization. Optionally strips the 'original_query' and 'original_document'
    fields from the resulting object and converts the qid and docno fields to strings.

    :param str | bytearray | bytes input: A json-serialized string.
    :param bool load_default_text: If true, the original_query and original_document fields are removed and the qid and
        docno values are converted to strings.
    :return: The deserialized and (optionally) processed object.
    :rtype: dict

    :Example:
        >>> parse_jsonl_line('{}', False)
        {}
        >>> parse_jsonl_line('{"original_query": "xxxx"}', False)
        {'original_query': 'xxxx'}
        >>> parse_jsonl_line('{"original_query": "xxxx"}', True)
        {}
        >>> parse_jsonl_line('{"original_query": "xxxx", "qid": 42, "pi": 3.14}', False)
        {'original_query': 'xxxx', 'qid': 42, 'pi': 3.14}
        >>> parse_jsonl_line('{"original_query": "xxxx", "qid": 42, "pi": 3.14}', True)
        {'qid': '42', 'pi': 3.14}
    """
    obj = json.loads(input)
    assert isinstance(obj, dict)
    if load_default_text:
        for field_to_del in ["original_query", "original_document"]:
            obj.pop(field_to_del, None)

        for field_to_str in ["qid", "docno"]:
            if field_to_str in obj:
                obj[field_to_str] = str(obj[field_to_str])

    return obj


def zip_dir(file_path):
    from tira.third_party_integrations import temporary_directory

    zip_file = temporary_directory()
    zip_file = zip_file / "tira-upload.zip"

    zf = zipfile.ZipFile(zip_file, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9)
    for root, _, files in os.walk(file_path):
        for name in files:
            filePath = os.path.join(root, name)
            zf.write(filePath, arcname=Path(filePath).relative_to(file_path))

    zf.close()
    return zip_file


def stream_all_lines(input_file: Union[str, Iterable[bytes]], load_default_text: bool) -> Generator[Dict, Any, Any]:
    """
    .. todo:: add documentation
    .. todo:: this function has two semantics: handling a file and handling file-contents
    """
    if type(input_file) is str:
        if not os.path.isfile(input_file):
            return

        if input_file.endswith(".gz"):
            with gzip.open(input_file, "rt", encoding="utf-8") as f:
                yield from stream_all_lines(f, load_default_text)
        else:
            with open(input_file, "r") as f:
                yield from stream_all_lines(f, load_default_text)

        return

    for line in input_file:
        yield parse_jsonl_line(line, load_default_text)


def huggingface_model_mounts(models: "Iterable[str]") -> dict:
    """Determine the mounts to make the described huggingface models available in the container. The models must
    already exist in the local huggingface cache of the host.

    Args:
        models (Iterable[str]): A list of huggingface models that you want to mount, e.g., ["openai-community/gpt2"].

    Returns:
        dict: The mounts required to make the specified models available in the container.
    """
    hf_cache = Path(os.path.expanduser("~/.cache/huggingface/hub"))
    if "HF_HUB_CACHE" in os.environ:
        hf_cache = Path(os.environ["HF_HUB_CACHE"])
    elif "HF_HOME" in os.environ:
        hf_cache = Path(os.environ["HF_HOME"]) / "hub"
    ret = {}
    if not models:
        return ret

    hf_cache = hf_cache.absolute()
    for model in models:
        model_in_fs = ("models/" + str(model)).replace("/", "--")
        model_path = hf_cache / model_in_fs
        if not model_path.exists():
            msg = (
                f"Model {model} does not in HF_HUB_CACHE = '{hf_cache}'. Expected a directory '{model_path}' to exist."
                " Please ensure that the model is available via your preferred way to download it."
            )
            print(msg)
            raise ValueError(msg)
        else:
            ret[str(model_path)] = {"bind": f"/root/.cache/huggingface/hub/{model_in_fs}", "mode": "ro"}

    return ret


def change_workdir_cmd(workdir: str):
    """
    Returns a shell command that changes the working directory to the specified directory to be executed in the TIRA
    sandbox before the real command.
    """

    if not workdir:
        return 'echo "did not change the working directory"'

    workdir = workdir.strip()

    if not workdir or not workdir.startswith("/"):
        return 'echo "did not change the working directory"'

    return f'cd {workdir}; echo "changed workdir to {workdir}"'


def _ln_huggingface_model_mounts(models: str) -> str:
    """Create a set of ln statements for symbolic links to huggingface models within a running container. Fails if the
    models do not exist in the local huggingface cache of the host.

    Args:
        models (str): A space seperated list of huggingface models that you want to mount, e.g.,
            "openai-community/gpt2 openai-community/gpt2-large".

    Returns:
        str: the ln command for usage with eval.
    """
    if not models:
        return ""
    models = sorted(list(set([i for i in models.split(" ") if i])))

    if not models:
        return ""

    ret = ["mkdir -p /root/.cache/huggingface/hub/"]
    for model in models:
        i = huggingface_model_mounts([model])
        k = list(i.keys())
        if not k or not len(k) == 1:
            raise ValueError(f"Expected exactly one model to be mounted, got: {i}")
        target_dir = i[k[0]]["bind"]
        src_dir = k[0]

        ret += [f"rm -Rf {target_dir}", f"ln -s {src_dir} {target_dir}"]

    return "; ".join(ret + [f'echo "mounted {len(models)} models"'])


def all_lines_to_pandas(input_file: Union[str, Iterable[str]], load_default_text: bool) -> pd.DataFrame:
    """
    .. todo:: add documentation
    .. todo:: this function has two semantics: handling a file and handling file-contents
    """
    if type(input_file) is str:
        if input_file.endswith(".gz"):
            with gzip.open(input_file, "rt", encoding="utf-8") as f:
                return all_lines_to_pandas(f, load_default_text)
        else:
            with open(input_file, "r") as f:
                return all_lines_to_pandas(f, load_default_text)

    import pandas as pd

    ret = []

    for line in input_file:
        ret += [parse_jsonl_line(line, load_default_text)]

    return pd.DataFrame(ret)


def __num(input: str) -> "Union[str, int, float]":
    """
    Converts the input to an int or float if possible. Returns the inputted string otherwise.

    :param str input: The string that should be converted to a float or int if possible.
    :return: The intrepteted input.
    :rtype: str | int | float

    :Example:
        >>> __num("hello world")
        "hello world"
        >>> __num("-42")
        -42
        >>> __num("3.5")
        3.5
        >>> __num("2e-6")
        2e-6
        >>> __num(" -42")
        " -42"
    """
    try:
        return int(input)
    except ValueError:
        try:
            return float(input)
        except ValueError:
            return input


def run_cmd(cmd: List[str], ignore_failure=False):
    import subprocess

    exit_code = subprocess.call(cmd)

    if not ignore_failure and exit_code != 0:
        raise ValueError(f"Command {cmd} did exit with return code {exit_code}.")


def create_tira_size_txt(run_dir):
    ret = check_output(
        ["bash", "-c", '(du -sb "' + str(run_dir.parent) + '" && du -hs "' + str(run_dir.parent) + '") | cut -f1']
    )
    ret += check_output(["bash", "-c", 'find "' + str(run_dir) + '" -type f -exec cat {} + | wc -l'])
    ret += check_output(["bash", "-c", 'find "' + str(run_dir) + '" -type f | wc -l'])
    ret += check_output(["bash", "-c", 'find "' + str(run_dir) + '" -type d | wc -l'])
    return ret


class MonitoredExecution:
    def run(self, method):
        from tira.third_party_integrations import temporary_directory

        ret = temporary_directory()
        output_dir = ret / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        stdout = io.StringIO()
        stderr = io.StringIO()
        exception_text = ""
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                method(output_dir)
            except Exception as e:
                exception_text = "\n\n" + str(repr(e))

        (ret / "stdout.txt").write_text(stdout.getvalue() + exception_text)
        (ret / "stderr.txt").write_text(stderr.getvalue() + exception_text)

        return ret


def run_prototext(output_dir, run_id, input_run_id, software_id, dataset_id, task_id):
    with open(output_dir / "run.prototext", "w") as f:
        f.write(
            '''softwareId: "'''
            + str(software_id)
            + '''"
runId: "'''
            + run_id
            + '''"
inputDataset: "'''
            + dataset_id
            + '''"
inputRun: "'''
            + input_run_id
            + '''"
downloadable: false
deleted: false
taskId: "'''
            + task_id
            + '''"
accessToken: "'''
            + str(uuid.uuid4())
            + '''"'''
        )


def parse_prototext_key_values(file_name):
    lines = open(file_name, "r").read()
    lines = lines.replace("measure{", "measure {")
    for i in [i for i in lines.split("measure {")]:
        ret = {}
        for line in i.split("\n"):
            if len(line.split(":")) < 2:
                continue
            elif len(line.split(":")) > 2:
                raise ValueError(f'Could not parse "{line}".')
            key = line.split(":")[0]
            value = line.split(":")[1].split('"')[1]
            ret[key.strip()] = __num(value.strip())
        if len(ret) > 0:
            yield ret


def to_prototext(m: List[Dict[str, Any]], upper_k: str = "") -> str:
    ret = ""

    def _to_prototext(d: Dict[str, Any], upper_k: str = "") -> str:
        ret = ""
        for k, v in d.items():
            new_k = upper_k
            if not new_k:
                new_k = k
            elif not new_k.endswith(k):
                new_k = upper_k + "_" + k
            if isinstance(v, dict):
                ret += _to_prototext(v, upper_k=new_k)
            else:
                ret += 'measure{\n  key: "' + str(new_k.replace("_", " ").title()) + '"\n  value: "' + str(v) + '"\n}\n'
        return ret

    for d in m:
        ret += _to_prototext(d, upper_k=upper_k)

    return ret


def all_environment_variables_for_github_action_or_fail(params):
    ret = {}

    for i in params:
        if len(i.split("=")) != 2:
            raise ValueError(f"Expect that exactly one '=' occurs in each passed parameter, got: '{i}'")

        key, value = i.split("=")

        if key in ret:
            raise ValueError(f"Got duplicated key: '{key}'")

        ret[key] = value

    expected_keys = [
        "GITHUB_SHA",
        "TIRA_VM_ID",
        "TIRA_TASK_ID",
        "TIRA_DOCKER_REGISTRY_TOKEN",
        "TIRA_DOCKER_REGISTRY_USER",
        "TIRA_CLIENT_TOKEN",
        "TIRA_CLIENT_USER",
        "TIRA_CODE_REPOSITORY_ID",
    ]

    for k in expected_keys:
        if k not in ret or not ret[k]:
            raise ValueError(
                f"I need the parameter {k} to continue, but could not find one or it is empty. This likely is a"
                " configuration error, e.g., due to missing secrets."
            )

    if "TIRA_JUPYTER_NOTEBOOK" in ret:
        for to_del in ["TIRA_DOCKER_FILE", "TIRA_DOCKER_PATH", "TIRA_COMMAND"]:
            if to_del in ret:
                del ret[to_del]
        ret["IMAGE_TAG"] = (
            f'registry.webis.de/code-research/tira/tira-user-{ret["TIRA_VM_ID"]}/submission:{ret["GITHUB_SHA"]}'
        )
    else:
        for expected_key in ["TIRA_DOCKER_FILE", "TIRA_DOCKER_PATH", "TIRA_COMMAND"]:
            if k not in ret or not ret[k]:
                raise ValueError(
                    f"I need the parameter {k} to continue, but could not find one or it is empty. This likely is a"
                    " configuration error, e.g., due to missing secrets."
                )

            submission_id = f'{ret["TIRA_DOCKER_PATH"].replace("/", "-").replace(" ", "-")}:{ret["GITHUB_SHA"]}'
            ret["IMAGE_TAG"] = (
                f'registry.webis.de/code-research/tira/tira-user-{ret["TIRA_VM_ID"]}/submission-{submission_id}'
            )

    return [k + "=" + v for k, v in ret.items()]


def load_output_of_directory(directory: Path, evaluation: bool = False) -> "Union[Dict, pd.DataFrame]":
    files = glob(str(directory) + "/*")

    if evaluation:
        files = [i for i in files if i.endswith(".prototext")]

    if len(files) != 1:
        raise ValueError("Expected exactly one output file. Got: ", files)

    files = files[0]

    logging.debug(f"Read file from {files}")

    if evaluation:
        ret = {}
        for i in [i for i in open(files, "r").read().split("measure") if "key:" in i and "value:" in i]:
            key = i.split("key:")[1].split("value")[0].split('"')[1]
            value = i.split("key:")[1].split("value")[1].split('"')[1]

            ret[key.strip()] = __num(value.strip())

        return ret
    else:
        return pd.read_json(files, lines=True, orient="records")
