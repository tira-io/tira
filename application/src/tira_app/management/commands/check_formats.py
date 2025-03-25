import json
import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

logger = logging.getLogger("tira")


class Command(BaseCommand):
    def handle(self, *args, **options):
        from tira.check_format import report_valid_formats

        from ... import model as modeldb

        for upload in tqdm(modeldb.AnonymousUploads.objects.all()):
            upload.valid_formats = json.dumps(report_valid_formats(upload.get_path_in_file_system()))
            upload.save()

    def add_arguments(self, parser):
        pass
