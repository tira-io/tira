import json
import logging
import os
import shlex
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from tira.io_utils import all_lines_to_pandas

if TYPE_CHECKING:

    from .rest_api_client import Client


def ensure_pyterrier_is_loaded(
    boot_packages=(("com.github.terrierteam", "terrier-prf", "-SNAPSHOT"),),
    packages=(),
    patch_ir_datasets=True,
    is_offline=True,
):
    import pyterrier as pt

    # Detect if we are in the TIRA sandbox
    if patch_ir_datasets:
        try:
            import ir_datasets as original_ir_datasets

            original_ir_datasets.load = load_ir_datasets().load
            logging.info(
                "Due to execution in TIRA, I have patched ir_datasets to always return the single input dataset mounted"
                " to the sandbox."
            )
        except Exception as e:
            logging.error("Could not patch ir_datasets.", exc_info=e)
    else:
        import ir_datasets as original_ir_datasets

        from tira.ir_datasets_util import original_ir_datasets_load

        original_ir_datasets.load = original_ir_datasets_load

    pt_version = os.environ.get("PYTERRIER_VERSION", "5.11")
    pt_helper_version = os.environ.get("PYTERRIER_HELPER_VERSION", "0.0.8")

    if not pt.java.started():
        logging.info(f"Start PyTerrier with version={pt_version}, helper_version={pt_helper_version}, no_download=True")
        pt.terrier.set_version(pt_version)
        pt.terrier.set_helper_version(pt_helper_version)
        pt.java.mavenresolver.offline(is_offline)
        for org_name, package_name, version in list(packages) + list(boot_packages):
            pt.java.add_package(org_name, package_name, version)
        pt.java.init()


def get_preconfigured_chatnoir_client(
    config_directory, features=["TARGET_URI"], num_results=10, retries=25, page_size=10
):
    from chatnoir_api import Index as ChatNoirIndex
    from chatnoir_pyterrier import ChatNoirRetrieve
    from chatnoir_pyterrier.feature import Feature

    chatnoir_config = json.load(open(config_directory + "/chatnoir-credentials.json"))

    chatnoir = ChatNoirRetrieve(api_key=chatnoir_config["apikey"], staging=chatnoir_config.get("staging", False))
    chatnoir.features = [getattr(Feature, i) for i in features]
    chatnoir.num_results = num_results
    chatnoir.retries = retries
    chatnoir.page_size = page_size
    chatnoir.index = getattr(ChatNoirIndex, chatnoir_config["index"])

    logging.info(
        f"ChatNoir Client will retrieve the top-{chatnoir.num_results} with page size of {chatnoir.page_size} from"
        f" index {chatnoir_config['index']} with {chatnoir.retries} retries."
    )

    return chatnoir


def get_output_directory(default_output: str = "/tmp/"):
    output_directory = os.environ.get("TIRA_OUTPUT_DIR", default_output)
    logging.info(f"The output directory is {output_directory}")
    return output_directory


def get_input_directory_and_output_directory(default_input, default_output: str = "/tmp/"):
    input_directory = os.environ.get("TIRA_INPUT_DATASET", None)

    if input_directory:
        print(f"I will read the input data from {input_directory}.")
    else:
        input_directory = default_input
        print(f"I will use a small hardcoded example located in {input_directory}.")

    return (input_directory, get_output_directory(default_output))


def is_running_as_inference_server():
    return os.environ.get("TIRA_INFERENCE_SERVER", None) is not None


def load_rerank_data(default, load_default_text=True):
    default_input = Path(get_input_directory_and_output_directory(default)[0])

    if not os.path.isdir(default_input) and len(default.split("/")) == 2:
        from tira.rest_api_client import Client as RestClient

        default_input = RestClient().download_dataset(default.split("/")[0], default.split("/")[1])

    if not str(default_input).endswith("rerank.jsonl") and not str(default_input).endswith("rerank.jsonl.gz"):
        if os.path.isfile(default_input / "rerank.jsonl.gz"):
            default_input = default_input / "rerank.jsonl.gz"
        elif os.path.isfile(default_input / "rerank.jsonl"):
            default_input = default_input / "rerank.jsonl"

    return all_lines_to_pandas(default_input, load_default_text)


def register_rerank_data_to_ir_datasets(path_to_rerank_file, ir_dataset_id, original_ir_datasets_id=None):
    """
    Load a dynamic ir_datasets integration from a given re_rank_file.
    The dataset will be registered for the id ir_dataset_id.
    The original_ir_datasets_id is used to infer the class of documents, qrels, and queries.
    """
    from tira.ir_datasets_util import register_dataset_from_re_rank_file

    default_input = get_input_directory_and_output_directory(path_to_rerank_file)[0]

    if not default_input.endswith("rerank.jsonl") and not default_input.endswith("rerank.jsonl.gz"):
        if os.path.isfile(default_input + "/rerank.jsonl.gz"):
            default_input = default_input + "/rerank.jsonl.gz"
        elif os.path.isfile(default_input + "/rerank.jsonl"):
            default_input = default_input + "/rerank.jsonl"

    register_dataset_from_re_rank_file(ir_dataset_id, default_input, original_ir_datasets_id)


def persist_and_normalize_run(
    run,
    system_name: str,
    default_output: "Optional[Path]" = None,
    output_file: "Optional[Path]" = None,
    depth: int = 1000,
    upload_to_tira: Optional["str"] = None,
    tira_client: "Optional[Client]" = None,
):
    if output_file is None and default_output is None:
        print(
            'I use the environment variable "TIRA_OUTPUT_DIR" to determine where I should store the run file using "."'
            " as default."
        )
        output_file = Path(os.environ.get("TIRA_OUTPUT_DIR", "."))

    if default_output is not None:
        if os.environ.get("TIRA_OUTPUT_DIR") is None:
            print(f'The run file is normalized outside the TIRA sandbox, I will store it at "{default_output}".')
            output_file = default_output
        else:
            output_file = os.environ.get("TIRA_OUTPUT_DIR")
            print(f'The run file is normalized inside the TIRA sandbox, I will store it at "{output_file}".')

    if not str(output_file).endswith("run.txt"):
        output_file = output_file / "run.txt"
    if upload_to_tira and not in_tira_sandbox():
        tira = _tira_client(tira_client)
        tmp = tira.get_dataset(upload_to_tira)
        if not tmp or "dataset_id" not in tmp:
            upload_to_tira = None
    else:
        upload_to_tira = None

    if upload_to_tira and tira:
        output_file = output_file + ".gz"
    normalize_run(run, system_name, depth).to_csv(output_file, sep=" ", header=False, index=False)

    print(f'Done. run file is stored under "{output_file}".')

    if upload_to_tira and tira:
        output_file = Path(output_file).parent
        upload_run_anonymous(output_file, tira, upload_to_tira)


def _tira_client(default_tira_client=None):
    if in_tira_sandbox():
        return None

    from tira.rest_api_client import Client as RestClient

    if default_tira_client:
        return default_tira_client
    else:
        return RestClient()


def upload_run_anonymous(directory: Path = None, tira_client=None, dataset_id=None):
    tira = _tira_client(tira_client)
    if not tira:
        return

    upload_to_tira = tira.get_dataset(dataset_id)
    tira.upload_run_anonymous(directory, upload_to_tira["dataset_id"])


def temporary_directory() -> Path:
    import tempfile

    try:
        ret = tempfile.TemporaryDirectory(prefix="tira-", delete=False)
        ret = Path(ret.name)
    except:
        ret = tempfile.TemporaryDirectory(prefix="tira-")
        ret = Path(ret.name)

    ret.mkdir(parents=True, exist_ok=True)
    return ret


def normalize_run(run, system_name, depth=1000):
    try:
        run["qid"] = run["qid"].astype(int)
    except Exception:
        pass

    run["system"] = system_name
    run = run.copy().sort_values(["qid", "score", "docno"], ascending=[True, False, False]).reset_index()

    if "Q0" not in run.columns:
        run["Q0"] = 0

    run = run.groupby("qid")[["qid", "Q0", "docno", "score", "system"]].head(depth)

    # Make sure that rank position starts by 1
    run["rank"] = 1
    run["rank"] = run.groupby("qid")["rank"].cumsum()

    return run[["qid", "Q0", "docno", "rank", "score", "system"]]


def extract_to_be_executed_notebook_from_command_or_none(command: str):
    command = command.replace(";", " ").replace("&", " ").replace("|", " ") if command is not None else None
    if command is not None and "--notebook" in command:
        return command.split("--notebook")[1].strip().split(" ")[0].strip()

    if command is not None and ".py" in command:
        for arg in shlex.split(command, posix=False):
            if arg.endswith(".py") or arg.endswith('.py"') or arg.endswith(".py'"):
                return arg

    if command is not None:
        command = shlex.split(command, posix=False)
        if len(command) > 0:
            command = command[0]

        if command and (
            command.endswith(".sh")
            or command.endswith(".bash")
            or command.endswith('.sh"')
            or command.endswith(".sh'")
            or command.endswith('.bash"')
            or command.endswith(".bash'")
        ):
            return command

    return None


def extract_ast_value(v):
    if hasattr(v, "s"):
        # python3.7
        return v.s
    if hasattr(v, "n"):
        # python3.7
        return v.n
    else:
        return v.value


def parse_ast_extract_assignment(python_line: str):
    try:
        import ast

        python_line = ast.parse(python_line).body[0]

        return python_line.targets[0].id, extract_ast_value(python_line.value)
    except Exception:
        return None, None


def parse_extraction_of_tira_approach_bash(bash_line: str):
    try:
        bash_line = bash_line.split("tira-cli")[1]
        bash_line = bash_line.split("download")[1]
        bash_line = bash_line.split("--approach")[1].strip()
        if bash_line.startswith("'"):
            return bash_line[1:].split("'")[0]
        if bash_line.startswith('"'):
            return bash_line[1:].split('"')[0]

        return bash_line.split(")")[0].split()[0].strip()
    except Exception:
        return None


def parse_extraction_of_tira_approach(python_line: str):
    try:
        import ast

        python_line = ast.parse(python_line.split("%")[0].strip()).body[0]

        if "op" in dir(python_line.value) and "left" in dir(python_line.value) and "right" in dir(python_line.value):
            python_line.value = python_line.value.left

        if "attr" in dir(python_line.value.func.value) and python_line.value.func.value.attr != "pt":
            return None

        if not ("id" in dir(python_line.value.func.value) and python_line.value.func.value.id == "tira") and not (
            "value" in dir(python_line.value.func.value) and python_line.value.func.value.value.id == "tira"
        ):
            return None

        if (
            python_line.value.func.attr != "index"
            and python_line.value.func.attr != "from_submission"
            and python_line.value.func.attr != "get_run_output"
            and python_line.value.func.attr != "transform_queries"
            and python_line.value.func.attr != "transform_documents"
        ):
            return None

        return extract_ast_value(python_line.value.args[0])
    except Exception:
        return None


def __read_src_lines(notebook: Path):
    if not notebook.exists():
        return []

    ret = []
    if notebook.suffix == ".py":
        return open(notebook).readlines()

    json_notebook = json.load(open(notebook))
    for cell in json_notebook["cells"]:
        if cell["cell_type"] == "code":
            for src_line in cell["source"]:
                ret += [src_line]

    return ret


def extract_previous_stages_from_notebook(notebook: Path):
    if not notebook.exists():
        return []

    ret = []
    if notebook.suffix == ".sh" or notebook.suffix == ".bash":
        ret = open(notebook).readlines()
        ret = [parse_extraction_of_tira_approach_bash(line) for line in ret]
        return [i for i in ret if i]

    for src_line in __read_src_lines(notebook):
        approach = parse_extraction_of_tira_approach(src_line)
        if approach is not None:
            ret += [approach]

    return ret


def extract_previous_stages_from_docker_image(image: str, command: str = None):
    import tempfile

    from tira.local_execution_integration import LocalExecutionIntegration as Client

    if command is None:
        tira = Client()
        command = tira.extract_entrypoint(image)

    notebook = extract_to_be_executed_notebook_from_command_or_none(command)

    if notebook is None:
        return []

    notebook = shlex.split(notebook)[0]

    tira = Client()

    local_file = tempfile.NamedTemporaryFile().name
    if notebook.endswith(".sh") or notebook.endswith(".bash"):
        local_file += ".sh"
    if notebook.endswith(".py"):
        local_file += ".py"
    tira.export_file_from_software(notebook, local_file, image=image)

    return extract_previous_stages_from_notebook(Path(local_file))


def in_tira_sandbox():
    return "TIRA_INPUT_DATASET" in os.environ


def load_ir_datasets():
    try:
        from ir_datasets.datasets.base import Dataset  # noqa: F401
    except Exception:
        return None

    if in_tira_sandbox():
        from tira.ir_datasets_util import static_ir_dataset

        if os.path.isfile(os.path.join(os.environ["TIRA_INPUT_DATASET"], "rerank.jsonl.gz")) or os.path.isfile(
            os.path.join(os.environ["TIRA_INPUT_DATASET"], "rerank.jsonl")
        ):
            import ir_datasets as original_ir_datasets

            register_rerank_data_to_ir_datasets(os.environ["TIRA_INPUT_DATASET"], "dynamic-ds-in-tira")

            return static_ir_dataset(os.environ["TIRA_INPUT_DATASET"], original_ir_datasets.load("dynamic-ds-in-tira"))

        return static_ir_dataset(os.environ["TIRA_INPUT_DATASET"])
    else:
        try:
            from tira.ir_datasets_util import ir_dataset_from_tira_fallback_to_original_ir_datasets

            return ir_dataset_from_tira_fallback_to_original_ir_datasets()
        except Exception:
            return None


ir_datasets = load_ir_datasets()
