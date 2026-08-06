import os
import subprocess
from typing import Optional

from celery.app.control import Inspect
from tira.io_utils import resolve_cache_dir
from tira.tira_client import TiraClient


def resolve_dynamic_mounts(
    dynamic_mounts: Optional[dict],
    client: TiraClient,
    task: str,
    dataset: str,
    team: str,
) -> Optional[dict]:
    if dynamic_mounts is None:
        return None

    ret = {}
    for mount_name, mount_config in dynamic_mounts.items():
        ret[mount_name] = dict(mount_config)
        if mount_config.get("source") != "OUTPUT_OF_OTHER_EXECUTION" or "run_id" not in mount_config:
            continue

        downloaded_run = client.download_zip_to_cache_directory(
            task=task, dataset=dataset, team=team, run_id=mount_config["run_id"]
        )
        ret[mount_name]["source"] = str(resolve_cache_dir(downloaded_run.parent, mount_name))

    return ret


def gpu_device_ids():
    ret = subprocess.check_output(["nvidia-smi", "-L"]).decode("utf-8")
    return _parse_resource_requirements(ret)


def _parse_resource_requirements(nvidia_smi_output: str) -> str:
    if "NVIDIA_VISIBLE_DEVICES" not in os.environ or not os.environ["NVIDIA_VISIBLE_DEVICES"]:
        raise ValueError("Please specify an environment variable NVIDIA_VISIBLE_DEVICES")
    ret = [i for i in nvidia_smi_output.split("\n") if os.environ["NVIDIA_VISIBLE_DEVICES"] in i]
    if len(ret) != 1:
        raise ValueError(f"I do not know how to process gpus {ret} from {os.environ['NVIDIA_VISIBLE_DEVICES']}.")

    return [os.environ["NVIDIA_VISIBLE_DEVICES"]]


def all_workers():
    ret = set()
    try:
        from tira_worker import app, gpu_executor

        for i in [app, gpu_executor]:
            inspect: Inspect = i.control.inspect()

            for qlist in inspect.active_queues().values():
                for q in qlist:
                    ret.add(q["name"])
    except:
        pass
    return ret
