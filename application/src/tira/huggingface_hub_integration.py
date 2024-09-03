from typing import Iterable, Optional

from huggingface_hub import HFCacheInfo, scan_cache_dir, snapshot_download
from huggingface_hub.constants import HF_HOME

import tira.io_utils as tira_cli_io_utils

HF_CACHE: Optional[HFCacheInfo] = None


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

    return {"MOUNT_HF_MODEL": " ".join(models), "HF_HOME": HF_HOME, "HF_CACHE_SCAN": ret}


def snapshot_download_hf_model(model: str):
    snapshot_download(repo_id=model.replace("--", "/"))
