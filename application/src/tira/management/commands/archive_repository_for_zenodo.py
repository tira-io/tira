from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.apps import apps
from tira.views import zip_run
from tira.endpoints.data_api import public_submission_or_none
from tqdm import tqdm
import json

class Command(BaseCommand):
    help = 'Dump software outputs for Zenodo'

    def handle(self, *args, **options):
        datasets = [
            'msmarco-passage-trec-dl-2019-judged-20230107-training', 'msmarco-passage-trec-dl-2020-judged-20230107-training',
            'antique-test-20230107-training', 'vaswani-20230107-training',
            'antique-test-20230107-training', 'cranfield-20230107-training',
            'medline-2004-trec-genomics-2004-20230107-training', 'medline-2017-trec-pm-2017-20230211-training',
            'cord19-fulltext-trec-covid-20230107-training', 'nfcorpus-test-20230107-training',
            'argsme-touche-2020-task-1-20230209-training', 'argsme-touche-2021-task-1-20230209-training',
            'medline-2017-trec-pm-2018-20230211-training', 'medline-2004-trec-genomics-2005-20230107-training'

                # second tranche, keep this for longer in files.webis.de as it is not part of original TIREx
                #'trec-tip-of-the-tongue-dev-20230607-training': 'todo',
                #'longeval-short-july-20230513-training': 'todo',
                #'longeval-heldout-20230513-training': 'todo',
                #'longeval-long-september-20230513-training': 'todo',]
        ]

        systems = {
            'ir-benchmarks': {
                'tira-ir-starter': {
                    'Index (tira-ir-starter-pyterrier)': 'data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes'
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
                        submission = public_submission_or_none(task_id, user_id, display_name)

                        ret[task_id][user_id][display_name][i] = submission

        print(json.dumps(ret))

