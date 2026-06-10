from typing import Iterable, Optional

import tira.io_utils as tira_cli_io_utils
from huggingface_hub import HFCacheInfo, scan_cache_dir, snapshot_download
from huggingface_hub.constants import HF_HOME


def huggingface_model_mounts(models: "Iterable[str]"):
    if not models:
        return []

    mounts = tira_cli_io_utils.huggingface_model_mounts(models, lazy=True)

    return {"MOUNT_HF_MODEL": " ".join(models), "HF_HOME": HF_HOME}


def snapshot_download_hf_model(model: str):
    snapshot_download(repo_id=model.replace("--", "/"))
