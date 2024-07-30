import json
import logging
from os.path import abspath
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse

import tira.tira_model as model
from tira.checks import check_permissions
from tira.views import add_context

logger = logging.getLogger("tira")


def doc_file_for_run(vm_id, dataset_id, task_id, run_id):
    checked_paths = []
    for evaluation in model.get_evaluations_of_run(vm_id, run_id):
        for f in [
            ".data-top-10-for-rendering.jsonl.gz",
            ".data-top-10-for-rendering.jsonl",
            ".data-top-10-for-rendering.json.gz",
            ".data-top-10-for-rendering.json",
        ]:
            p = Path(settings.TIRA_ROOT) / "data" / "runs" / dataset_id / vm_id / evaluation / "output" / f
            checked_paths += [str(p)]
            if p.is_file():
                return p
    raise ValueError(f"Could not find .data-top-10-for-rendering.jsonl. Searched in {checked_paths}.")


def load_irds_metadata_of_task(task, dataset):
    dataset_type = "training-datasets" if dataset.endswith("-training") else "test-datasets"

    metadata_file = Path(settings.TIRA_ROOT) / "data" / "datasets" / dataset_type / task / dataset / "metadata.json"

    if not metadata_file.is_file():
        raise ValueError(f"Configuration error: The expected file {metadata_file} does not exist.")

    return json.load(open(metadata_file, "r"))


def __normalize_ids(a, b):
    return "---".join(sorted([a, b]))


@add_context
@check_permissions
def diffir(request, context, task_id, run_id_1, run_id_2, topk):
    if request.method == "GET":
        try:
            run_1 = model.get_run(dataset_id=None, vm_id=None, run_id=run_id_1)
            run_2 = model.get_run(dataset_id=None, vm_id=None, run_id=run_id_2)

            if run_1["dataset"] != run_2["dataset"]:
                raise ValueError(
                    f'Run {run_id_1} has dataset {run_1["dataset"]} while run {run_id_2} has dataset '
                    + f'{run_2["dataset"]}. Expected both to be identical'
                )

            diffir_file = (
                Path(settings.TIRA_ROOT)
                / "state"
                / "serp"
                / "version-0.0.1"
                / "runs"
                / run_1["dataset"]
                / __normalize_ids(run_1["vm"], run_2["vm"])
                / __normalize_ids(run_id_1, run_id_2)
                / "diffir.html"
            )
            diffir_dir = (diffir_file / "..").resolve()

            if diffir_file.is_file():
                return HttpResponse(open(diffir_file).read())

            run_dir = Path(settings.TIRA_ROOT) / "data" / "runs" / run_1["dataset"]
            run_1_file = run_dir / run_1["vm"] / run_id_1 / "output" / "run.txt"
            run_2_file = run_dir / run_2["vm"] / run_id_2 / "output" / "run.txt"

            if not run_1_file.is_file():
                raise ValueError(f"Error: The expected file {run_1_file} does not exist.")

            if not run_2_file.is_file():
                raise ValueError(f"Error: The expected file {run_2_file} does not exist.")

            doc_files = [
                doc_file_for_run(run_1["vm"], run_1["dataset"], task_id, run_id_1),
                doc_file_for_run(run_2["vm"], run_1["dataset"], task_id, run_id_2),
            ]

            for doc_file in doc_files:
                if not doc_file or not doc_file.is_file():
                    raise ValueError(f"Error: expected two evaluations, but got only one in {doc_files}")

            from diffir.run import diff_from_local_data

            _, ret = diff_from_local_data(
                [abspath(run_1_file), abspath(run_2_file)],
                [str(i) for i in doc_files],
                cli=False,
                web=True,
                print_html=False,
                topk=topk,
            )

            diffir_dir.mkdir(parents=True, exist_ok=True)
            with open(diffir_file, "w") as f:
                f.write(ret)

            return HttpResponse(ret)
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"status": "0", "message": f"Encountered an exception: {e}"})
