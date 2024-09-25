import json
from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from tira.rest_api_client import Client
from tira.tira_redirects import mirror_urls_for_run_output
from tira.tirex import IRDS_TO_TIREX_DATASET
from tqdm import tqdm

TIREX_DATASET_TO_IRDS_DATASET = {v: k for k, v in IRDS_TO_TIREX_DATASET.items()}


class Command(BaseCommand):
    help = "Export for data.tira.io"

    def html_for_dataset_id(self, dataset_id, metadata):
        return f"""
<!DOCTYPE html>
<html>
<head>
<title>{dataset_id}</title>
</head>
<body>
<h1>{dataset_id}</h1>
</body>
</html>
"""

    def persist(self, html, metadata, path: Path):
        path.mkdir(exist_ok=True, parents=True)
        with open(path / "index.html", "wt") as f:
            f.write(html)

        with open(path / "data.json", "wt") as f:
            f.write(json.dumps(metadata))

    def process_dataset(self, task_id: str, dataset_id: str, submitted_softwares: dict, output_dir: Path):
        metadata = {"task": task_id, "softwareSubmissions": submitted_softwares}
        ir_datasets_id = TIREX_DATASET_TO_IRDS_DATASET.get(dataset_id)
        metadata["irDatasetsId"] = ir_datasets_id

        self.persist(self.html_for_dataset_id(dataset_id, metadata), metadata, output_dir / dataset_id)
        if ir_datasets_id is not None:
            self.persist(self.html_for_dataset_id(dataset_id, metadata), metadata, output_dir / Path(ir_datasets_id))

    def handle(self, *args, **options):
        output = Path(options["output_dir"])
        tira = Client()
        # help(tira)
        for task in tira.all_tasks():
            if task["task_id"] != "ir-benchmarks":
                # speed up for debugging
                continue

            all_softwares = tira.all_softwares(task["task_id"])
            for dataset in tira.datasets(task["task_id"]):
                evaluations = tira.evaluations(task["task_id"], dataset, join_submissions=False)
                evaluations = [i.to_dict() for _, i in evaluations.iterrows()]

                submitted_softwares = {}
                for software in tqdm(all_softwares):
                    try:
                        execution = tira.get_run_execution_or_none(software, dataset)
                        if execution is not None:
                            execution["mirrors"] = mirror_urls_for_run_output(
                                task["task_id"], execution["team"], dataset, execution["run_id"]
                            )
                            submitted_softwares[software] = execution
                    except ValueError:
                        submitted_softwares[software] = "Not public"

                metadata = {"software": submitted_softwares, "evaluations": evaluations}
                self.process_dataset(task["task_id"], dataset, metadata, output)

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default=None, type=str, required=True)
