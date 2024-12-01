from django.core.management.base import BaseCommand

from tira_app.endpoints.v1._datasets import add_mirrored_resource


class Command(BaseCommand):
    """Add a mirror to a dataset."""

    def handle(self, *args, **options):
        if "dataset_id" not in options or not options["dataset_id"]:
            raise ValueError("Please pass --dataset_id")

        if "url" not in options or not options["url"]:
            raise ValueError("Please pass --url")

        if "name" not in options or not options["name"]:
            raise ValueError("Please pass --name")

        add_mirrored_resource(options["dataset_id"], options["url"], options["name"])

    def add_arguments(self, parser):
        parser.add_argument("--dataset_id", default=None, type=str)
        parser.add_argument("--url", default=None, type=str)
        parser.add_argument("--name", default=None, type=str)
