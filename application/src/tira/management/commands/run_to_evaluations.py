from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.apps import apps
import tira.tira_model as model
import json

class Command(BaseCommand):
    help = 'export run to evaluations'

    def handle(self, *args, **options):
        ret = {}
        for dataset in model.get_datasets_by_task('ir-benchmarks', return_only_names=True):
            mapping = {}
            submissions = model.get_vms_with_reviews(dataset['dataset_id'])
            for submission in submissions:
                for run in submission['runs']:
                    if 'is_evaluation' not in run or not run['is_evaluation']:
                        continue
                    if run['input_run_id'] not in mapping:
                        mapping[run['input_run_id']] = []
                    mapping[run['input_run_id']] += [run['run_id']]
            ret[dataset['dataset_id']] = mapping
        with open('run-to-evaluations.json', 'w') as f:
            f.write(json.dumps(ret))

