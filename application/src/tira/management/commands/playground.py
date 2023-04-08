from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Runs some playground command.
    """

    def handle(self, *args, **options):
        from tira.ir_datasets_loader import run_irds_command
        run_irds_command('tmp-test-maik', 'pssda', 'pangram-ir-dataset', '/irds_cli.sh --skip_qrels --ir_datasets_id pangrams --output_dataset_path $outputDir', '/tmp/sda-1/1/')
    

    def add_arguments(self, parser):
        pass
