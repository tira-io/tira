import json

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
{json.dumps(metadata)}
</body>
</html>
"""

    def process_dataset(self, task_id, dataset_id, submitted_softwares):
        metadata = {"task": task_id, "softwareSubmissions": submitted_softwares}
        ir_datasets_id = TIREX_DATASET_TO_IRDS_DATASET.get(dataset_id)
        metadata["irDatasetsId"] = ir_datasets_id

        print(self.html_for_dataset_id(dataset_id, metadata))

    def handle(self, *args, **options):
        tira = Client()
        # help(tira)
        for task in tira.all_tasks():
            if task["task_id"] != "ir-benchmarks":
                # speed up for debugging
                continue
            all_softwares = tira.all_softwares(task["task_id"])
            for dataset in tira.datasets(task["task_id"]):
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

                self.process_dataset(task["task_id"], dataset, submitted_softwares)
                break

            # help(tira)
            # print(task)
