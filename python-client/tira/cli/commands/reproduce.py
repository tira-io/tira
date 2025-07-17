import logging
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from git import Repo, exc

from ...check_format import FormatMsgType, log_message

if TYPE_CHECKING:
    from os import PathLike
    from typing import Any, Mapping, TextIO, TypeVar, Union

    _KT = TypeVar("_KT")  # Key type.
    _VT = TypeVar("_VT")  # Value type.

DOCKERFILE_TEMPLATE = """
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

WORKDIR /app

COPY <<EOF requirements.txt
{dependencies}
EOF

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
"""


def __get_nested(
    d: "Mapping[_KT, Union[dict, _VT]]", keys: "list[_KT]"
) -> "Union[Mapping[_KT, Union[dict, _VT]], _VT]":
    out: "Union[Mapping[_KT, Union[dict, _VT]], _VT]" = d
    for i, key in enumerate(keys):
        if not isinstance(out, Mapping):
            raise TypeError(f"The value at {'>'.join(map(str, keys[:i]))} is not a mapping")
        if key not in out:
            raise KeyError(f"The key {'>'.join(map(str, keys[:i+1]))} could not be found")
        out = out[key]
    return out


def __load_metadata(metadata: "TextIO") -> "dict[str, Any]":
    try:
        data = yaml.safe_load(metadata)
        log_message("Input is a correctly formatted YAML file", FormatMsgType.OK)
        return data
    except yaml.YAMLError as e:
        log_message(f"Failed to parse the input file: {e}", FormatMsgType.OK)
        logging.critical("The input file is not formatted correctly", exc_info=e)
        sys.exit(1)


def __download_code(metadata: "dict[str, Any]", dest: "PathLike") -> Repo:
    # Find out where I can get the code from
    try:
        repository = __get_nested(metadata, ["implementation", "source", "repository"])
        commit = __get_nested(metadata, ["implementation", "source", "commit"])
        assert isinstance(repository, str)
        assert isinstance(commit, str)
        log_message(f"Repository is at {repository}#{commit}", FormatMsgType.OK)
    except KeyError as e:
        log_message(f"Failed to locate the code from the metadata: {e}", FormatMsgType.ERROR)
        logging.critical("Vital information is not present in the metadata", exc_info=e)
        sys.exit(2)

    # Download the code
    try:
        repo = Repo.clone_from(repository, to_path=dest)
        log_message("Cloned into the repository", FormatMsgType.OK)
        return repo
    except exc.GitError as e:
        log_message(f"Failed to clone repository: {e}", FormatMsgType.ERROR)
        logging.critical(f"Failed to clone repository from {repository}", exc_info=e)
        sys.exit(3)


def __configure_docker_container(metadata: "dict[str, Any]", dest: Path):
    # Search for an existing Docker configuration
    # TODO: implement
    log_message("No docker configuration found; I will create one from the metadata...", FormatMsgType.WARN)
    # Construct a Docker Container
    try:
        packages = __get_nested(metadata, ["implementation", "python", "packages"])
        dockerfile = DOCKERFILE_TEMPLATE.format_map({"dependencies": "\n".join(packages)})
        (dest / "Dockerfile").write_text(dockerfile)
        log_message("Created a docker file", FormatMsgType.OK)
        # Build the container
        # TODO: implement
    except KeyError as e:
        log_message(f"Failed to construct a dockerfile from the metadata: {e}", FormatMsgType.ERROR)
        logging.critical("Vital information is not present in the metadata", exc_info=e)
        sys.exit(4)


def __run_experiment(metadata: "dict[str, Any]"):
    # Find out what script to run
    try:
        script = __get_nested(metadata, ["implementation", "script", "path"])
        log_message(f"Running {script}", FormatMsgType.OK)
    except KeyError as e:
        log_message(f"Failed to find the command that ran the experiments: {e}", FormatMsgType.ERROR)
        logging.critical("Vital information is not present in the metadata", exc_info=e)
        sys.exit(4)
    # Run the script
    # TODO


def reproduce_command(metadata: "TextIO", **kwargs) -> int:
    data = __load_metadata(metadata)
    with tempfile.TemporaryDirectory() as tmpdir:
        log_message(f"Switched working directory to {tmpdir}", FormatMsgType.OK)
        with __download_code(data, Path(tmpdir)) as repo:
            __configure_docker_container(data, Path(tmpdir))
            __run_experiment(data)
    return 0
