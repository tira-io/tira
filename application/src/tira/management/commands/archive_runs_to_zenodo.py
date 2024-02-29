from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.apps import apps
from tira.views import zip_run
from tira.endpoints.data_api import model, public_submission_or_none
from tqdm import tqdm
import json
import shutil

class Command(BaseCommand):
    help = 'Dump software outputs for Zenodo'

    def handle(self, *args, **options):
        datasets = [
            'msmarco-passage-trec-dl-2019-judged-20230107-training','msmarco-passage-trec-dl-2020-judged-20230107-training',
            'antique-test-20230107-training', 'vaswani-20230107-training',
            'cranfield-20230107-training', 'medline-2004-trec-genomics-2004-20230107-training',
            'medline-2017-trec-pm-2017-20230211-training', 'cord19-fulltext-trec-covid-20230107-training',
            'nfcorpus-test-20230107-training', 'argsme-touche-2020-task-1-20230209-training',
            'argsme-touche-2021-task-1-20230209-training', 'medline-2017-trec-pm-2018-20230211-training',
            'medline-2004-trec-genomics-2005-20230107-training', 'trec-tip-of-the-tongue-dev-20230607-training',
            'longeval-short-july-20230513-training', 'longeval-heldout-20230513-training',
            'longeval-long-september-20230513-training', 'longeval-train-20230513-training',
        ]

        systems = {
            'ir-benchmarks': {
                'tira-ir-starter': {
                    'Index (tira-ir-starter-pyterrier)': 'pyterrier-indexes'
                }
            }
        }
        
        ret = {}

        for task_id in systems.keys():
            ret[task_id] = {}
            for user_id in systems[task_id].keys():
                ret[task_id][user_id] = {}
                for display_name in systems[task_id][user_id].keys():
                    ret[task_id][user_id][display_name] = {}
                    output_dir = systems[task_id][user_id][display_name]
                    for i in tqdm(datasets):
                        run_id = model.runs(task_id, i, user_id, display_name)[0]
                        zip_file = zip_run(i, user_id, run_id)
                        ret[task_id][user_id][display_name][i] = run_id
                        shutil.copyfile(zip_file, f'{output_dir}/{run_id}.zip')

        print(json.dumps(ret))

