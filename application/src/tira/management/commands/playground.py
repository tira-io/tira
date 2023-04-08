from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Runs some playground command.
    """

    def handle(self, *args, **options):
        from tira.ir_datasets_loader import run_irds_command
        run_irds_command('tmp-test-maik', 'pssda', 'webis/tira-ir-datasets-starter:0.0.45-pangram', '/irds_cli.sh --skip_qrels true --ir_datasets_id pangrams --output_dataset_path $outputDir', '/tmp/sda-1/1/')
        run_irds_command('tmp-test-maik', 'pssda', 'webis/tira-ir-datasets-starter:0.0.45-pangram', '/irds_cli.sh --skip_documents true --ir_datasets_id pangrams --output_dataset_truth_path $outputDir', '/tmp/sda-1/2/')
    

    def add_arguments(self, parser):
        pass
