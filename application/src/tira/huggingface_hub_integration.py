import os
import sys
from importlib.util import module_from_spec, spec_from_file_location
from types import ModuleType
from typing import Iterable

from huggingface_hub import scan_cache_dir, snapshot_download


def load_tira_cli_io_utils() -> ModuleType:
    for p in sys.path:
        p = str(os.path.abspath(p)) + "/"
        if "-packages/" in p:
            p = p.split("-packages/")[0] + "-packages/"

        if os.path.exists(f"{p}/tira/io_utils.py"):
            tira_cli_io_utils_spec = spec_from_file_location("tira_cli.io_utils", f"{p}/tira/io_utils.py")
            assert tira_cli_io_utils_spec is not None
            assert tira_cli_io_utils_spec.loader is not None
            tira_cli_io_utils = module_from_spec(tira_cli_io_utils_spec)
            assert tira_cli_io_utils is not None
            tira_cli_io_utils_spec.loader.exec_module(tira_cli_io_utils)
            return tira_cli_io_utils

    raise ModuleNotFoundError()


tira_cli_io_utils = load_tira_cli_io_utils()


TIRA_HOST_HF_HOME = tira_cli_io_utils._default_hf_home_in_tira_host()
HF_CACHE = None


def _hf_repos() -> dict[str, str]:
    global HF_CACHE
    if HF_CACHE is None:
        HF_CACHE = scan_cache_dir()
    return {i.repo_id: str(i) for i in HF_CACHE.repos}


def huggingface_model_mounts(models: Iterable[str]):
    if not models:
        return []

    mounts = tira_cli_io_utils.huggingface_model_mounts(models)
    repos = _hf_repos()
    print(mounts)
    print(repos)
    print(models)

    ret = []
    for model in models:
        if model in repos:
            ret.append(repos[model])
        else:
            raise Exception(f"Model {model} is not available in the Huggingface cache")

    return {"MOUNT_HF_MODEL": " ".join(models), "HF_HOME": TIRA_HOST_HF_HOME, "HF_CACHE_SCAN": ret}


def snapshot_download_hf_model(model: str):
    os.environ["HF_HOME"] = TIRA_HOST_HF_HOME
    snapshot_download(repo_id=model.replace("--", "/"))
