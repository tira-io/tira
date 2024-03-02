from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.apps import apps
from tira.views import zip_run, zip_runs
from tira.endpoints.data_api import model, public_submission_or_none
from tqdm import tqdm
import json
import shutil

def md5(filename):
    import hashlib
    return hashlib.md5(open(filename,'rb').read()).hexdigest()

class Command(BaseCommand):
    help = 'Dump software outputs for Zenodo'

    def handle(self, *args, **options):
        dataset_groups = {
            'trec-recent': [
                'msmarco-passage-trec-dl-2019-judged-20230107-training', 'msmarco-passage-trec-dl-2020-judged-20230107-training', 'trec-tip-of-the-tongue-dev-20230607-training'
            ],
            'tiny-test-collections': [
                'antique-test-20230107-training', 'vaswani-20230107-training', 'cranfield-20230107-training', 'nfcorpus-test-20230107-training'
            ],
            'trec-medical': [
                'medline-2004-trec-genomics-2004-20230107-training', 'medline-2017-trec-pm-2017-20230211-training', 'cord19-fulltext-trec-covid-20230107-training', 'medline-2017-trec-pm-2018-20230211-training', 'medline-2004-trec-genomics-2005-20230107-training'
            ],
            'clef-labs': [
                'argsme-touche-2020-task-1-20230209-training', 'argsme-touche-2021-task-1-20230209-training', 'longeval-short-july-20230513-training', 'longeval-heldout-20230513-training', 'longeval-long-september-20230513-training', 'longeval-train-20230513-training'
            ]
        }

        datasets = dataset_groups['trec-recent'] + dataset_groups['tiny-test-collections'] + dataset_groups['trec-medical'] + dataset_groups['clef-labs']

        systems = {
            'ir-benchmarks': {
                'tira-ir-starter': {
                    'Index (tira-ir-starter-pyterrier)': 'pyterrier-indexes'
                }
            }
        }

        aggregated_systems = {
            'ir-benchmarks': {
                'qpptk': {
                    'all-predictors': 'qpptk-all-predictors',
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
                        target_file = f'{output_dir}/{run_id}.zip'

                        zip_file = zip_run(i, user_id, run_id)
                        shutil.copyfile(zip_file, target_file)
                        ret[task_id][user_id][display_name][i] = {'run_id': run_id, 'md5': md5(target_file)}

        print(json.dumps(ret))

        ret = {}

        for task_id in aggregated_systems.keys():
            ret[task_id] = {}
            for user_id in aggregated_systems[task_id].keys():
                ret[task_id][user_id] = {}
                for display_name, output_dir in aggregated_systems[task_id][user_id].items():
                    for dataset_group, datasets in tqdm(dataset_groups.items(), display_name):
                        run_ids = {}
                        target_file = f'{output_dir}/{user_id}-{display_name}-{dataset_group}.zip'

                        for dataset in datasets:
                            run_ids[dataset] = model.runs(task_id, dataset, user_id, display_name)[0]

                        run_ids = sorted(list(run_ids))
                        zip_file = zip_runs(i, user_id, [(k, v) for k,v in run_ids.items()])
                        shutil.copyfile(zip_file, target_file)
                        ret[task_id][user_id][display_name][dataset_group] = {'dataset_group': dataset_group, 'md5': md5(target_file), 'run_ids': run_ids}

        print(json.dumps(ret))


                    