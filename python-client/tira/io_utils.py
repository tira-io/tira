import gzip
import json
import logging
import os
from glob import glob
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Union

import pandas as pd


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


def huggingface_model_mounts(models: Iterable[str]) -> dict:
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


def __num(input: str) -> Union[str, int, float]:
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


def parse_prototext_key_values(file_name):
    for i in [i for i in open(file_name, "r").read().split("measure {")]:
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


def load_output_of_directory(directory: Path, evaluation: bool = False) -> Union[Dict, pd.DataFrame]:
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
