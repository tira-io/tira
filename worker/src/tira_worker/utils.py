import os
import subprocess


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
