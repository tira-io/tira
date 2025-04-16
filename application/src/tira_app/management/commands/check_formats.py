import json
import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

logger = logging.getLogger("tira")


class Command(BaseCommand):
    def handle(self, *args, **options):
        from tira.check_format import report_valid_formats

        from ... import model as modeldb
        from ...tira_model import model

        if "task" in options and options["task"]:
            for dataset in tqdm(model.get_datasets_by_task(options["task"])):
                # print(dataset["dataset_id"])
                for run in modeldb.Run.objects.filter(input_dataset__dataset_id=dataset["dataset_id"]):
                    if run.evaluator:
                        continue
                    run.valid_formats = json.dumps(report_valid_formats(run.get_path_in_file_system()))
                    if len(run.valid_formats) < 4:
                        run.valid_formats = None
                    run.save()
        else:
            for upload in tqdm(modeldb.AnonymousUploads.objects.all()):
                upload.valid_formats = json.dumps(report_valid_formats(upload.get_path_in_file_system()))
                upload.save()

    def add_arguments(self, parser):
        parser.add_argument("--task", default=None, type=str)
