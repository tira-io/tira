from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Runs some playground command.
    """

    def handle(self, *args, **options):
        from tira.endpoints.data_api import add_registration
        class tmp():
            body= '{"group": "ir-lab-sose-2023-armafira", "team": "a", "username": "mf2", "email": "del-me", "affiliation": "mf2", "country": "c", "employment": "e", "participation": "p", "instructorName": "i", "instructorEmail": "i", "questions": ""}'
            session = {}
        
        print(tmp().body)
        
        request = tmp()
        context = {'user_id': 'mf2'}
        print(add_registration(request, context, 'ir-lab-jena-leipzig-sose-2023', 'del-me-maik'))
    
        #from tira.ir_datasets_loader import run_irds_command
        #run_irds_command('tmp-test-maik', 'pssda', 'webis/tira-ir-datasets-starter:0.0.45-pangram', '/irds_cli.sh --skip_qrels true --ir_datasets_id pangrams --output_dataset_path $outputDir', '/tmp/sda-1/1/')
        #run_irds_command('tmp-test-maik', 'pssda', 'webis/tira-ir-datasets-starter:0.0.45-pangram', '/irds_cli.sh --skip_documents true --ir_datasets_id pangrams --output_dataset_truth_path $outputDir', '/tmp/sda-1/2/')
    

    def add_arguments(self, parser):
        pass
