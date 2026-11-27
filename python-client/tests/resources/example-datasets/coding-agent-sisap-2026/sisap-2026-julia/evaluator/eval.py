#!/usr/bin/env python3
import argparse
import json
from glob import glob
from pathlib import Path

import h5py
import numpy as np
import yaml


def load_results(dirname):
    matches = glob(str(Path(dirname) / "*.h5"))
    assert len(matches) >= 1
    for match in matches:
        yield h5py.File(match, "r")


def get_recall(indices, gt, k):
    assert k <= indices.shape[1]
    assert len(indices) == len(gt)

    n = len(indices)
    recall = 0
    for i in range(n):
        recall += len(set(indices[i, :k]) & set(gt[i, :k]))
    return recall / (n * k)


def load_ir_metadata(input_dir):
    try:
        return yaml.safe_load((Path(input_dir) / ".tracking-results.yml").read_text())["resources"]
    except Exception:
        return None


def detect_task(input_dir):
    config_files = glob(f"{input_dir}/*.json")
    assert len(config_files) == 1
    cfg = json.loads(Path(config_files[0]).read_text())
    task_keys = [k for k in cfg.keys() if k.startswith("task")]
    if len(task_keys) != 1:
        raise ValueError(f"Expected exactly one task in config, found: {task_keys}")
    return task_keys[0]


def get_h5_item(f, path):
    if isinstance(path, list):
        cur = f
        for p in path:
            cur = cur[p]
        return cur
    cur = f
    for p in path.split("/"):
        cur = cur[p]
    return cur


def run_evaluation(task_description, input_file, results_file):
    cfg = json.loads(Path(task_description).read_text())
    with h5py.File(input_file, "r") as f_gt:
        gt_I = np.array(get_h5_item(f_gt, cfg["gt_I"]))

    values = {
        "recall": [],
        "buildtime": [],
        "querytime": [],
    }

    for results in load_results(results_file):
        with results:
            values["recall"].append(get_recall(np.array(results["knns"]), gt_I, cfg["k"]))
            values["buildtime"].append(float(results.attrs["buildtime"]))
            values["querytime"].append(float(results.attrs["querytime"]))

    return {
        f"{metric} ({extreme})": float(getattr(np, extreme)(metric_values))
        for metric, metric_values in values.items()
        for extreme in ["min", "max"]
    }


def persist_prototext(results, filename):
    from tira.io_utils import to_prototext

    with open(filename, "w") as f:
        for field_to_delete in ["algo", "dataset", "params", "task"]:
            if field_to_delete in results:
                del results[field_to_delete]

        print(results)
        f.write(to_prototext([results]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--private", help="private queries held out for evaluation", action="store_true", default=False)

    parser.add_argument("task_description")
    parser.add_argument("truth_data")
    parser.add_argument("results")
    parser.add_argument("file")
    args = parser.parse_args()
    results = run_evaluation(args.task_description, args.truth_data, args.results)

    if args.file.endswith(".prototext"):
        persist_prototext(results, args.file)
    else:
        raise ValueError("Implement other formats ...")
