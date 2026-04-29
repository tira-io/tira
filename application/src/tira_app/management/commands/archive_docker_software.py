import json
import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand
from slugify import slugify
from tqdm import tqdm

from ...tira_model import (
    get_git_integration,
)

logger = logging.getLogger("tira")


class Command(BaseCommand):
    """Run git_runner via cli.
    Later this will become a fully fledged cli tool that we use as wrapper in the repository.
    At the moment, we just execute some predefined commands
    """
    def archive_docker_software(self, approach, git_runner):
        from ... import model as modeldb
        from ...util import docker_image_details

        task_id, vm_id, name = approach.split("/")
        software = modeldb.DockerSoftware.objects.filter(
            vm__vm_id=vm_id, task__task_id=task_id, display_name=name, deleted=False
        )

        if len(software) != 1:
            raise ValueError(f"Found {software} but expected a single entry.")

        software = software[0]
        if software.public_image_name and software.public_image_size:
            print(f'Software "{approach}" is already public.')
            return

        print(software)
        image_name = (slugify(software.tira_image_name)).replace("/", "-")
        dockerhub_image = f"docker.io/webis/{task_id}-submissions:" + image_name.split("-tira-user-")[1].strip()

        software_definition = {
            "TIRA_IMAGE_TO_EXECUTE": software.tira_image_name,
            "TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB": dockerhub_image,
        }
        git_runner.archive_software(
            "/tmp/", software_definition, download_images=True, persist_images=False, upload_images=True
        )
        image_metadata = docker_image_details(software.tira_image_name)

        print(image_metadata)
        print(image_name)
        print(dockerhub_image)
        software.public_image_name = dockerhub_image
        software.public_image_size = image_metadata["size"]
        software.save()

    def handle(self, *args, **options):
        git_runner = get_git_integration("webis", None)
        print(f"Use {git_runner}.")
        self.archive_docker_software(options["software"], git_runner)

    def add_arguments(self, parser):
        parser.add_argument("--software", default=None, type=str)
