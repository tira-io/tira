import os
from typing import Iterable

from django.conf import settings
from huggingface_hub import scan_cache_dir
from huggingface_hub import snapshot_download as hfsnapshot_download

import tira.io_utils as tira_cli_io_utils

TIRA_HOST_HF_HOME = tira_cli_io_utils.default_hf_home_in_tira_host(settings.TIRA_ROOT)
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


def snapshot_download(*args, **kwargs) -> str:
    return hfsnapshot_download(*args, cache_dir=TIRA_HOST_HF_HOME / "hub", **kwargs)


snapshot_download.__doc__ = hfsnapshot_download.__doc__
