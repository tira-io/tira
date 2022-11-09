from logging import getLogger

from django.core.management.base import BaseCommand, CommandParser

logger = getLogger("tira")


class Command(BaseCommand):
    """
    TODO: Write some documentation.
    """

    def handle(self, *args, **options) -> None:
        print(
            f"TODO: Implement this: "
            f"Import dataset with id {options['ir_datasets_id']}"
        )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--ir_datasets_id",
            type=str,
            required=True,
        )
