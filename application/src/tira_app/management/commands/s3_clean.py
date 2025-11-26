from django.core.management.base import BaseCommand
from tqdm import tqdm

from tira_app import model as modeldb


class Command(BaseCommand):
    help = "Copy all mirrors S3"

    def handle(self, *args, **options):
        print(options["task"])
        for i in modeldb.Dataset.objects.filter(default_task__task_id=options["task"]):
            print(i)
            for j in modeldb.DatasetHasMirroredResource.objects.filter(dataset=i):
                j.delete()

    def add_arguments(self, parser):
        parser.add_argument("--task", default=None, type=str, required=True)
