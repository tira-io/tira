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
            ],
            'clueweb': [
                'clueweb09-en-trec-web-2009-20230107-training', 'clueweb09-en-trec-web-2010-20230107-training', 'clueweb09-en-trec-web-2011-20230107-training', 'clueweb09-en-trec-web-2012-20230107-training', 'clueweb12-touche-2020-task-2-20230209-training', 'clueweb12-touche-2021-task-2-20230209-training', 'clueweb12-trec-misinfo-2019-20240214-training', 'clueweb12-trec-web-2013-20230107-training', 'clueweb12-trec-web-2014-20230107-training', 'gov-trec-web-2002-20230209-training', 'gov-trec-web-2003-20230209-training', 'gov-trec-web-2004-20230209-training', 'gov2-trec-tb-2004-20230209-training', 'gov2-trec-tb-2005-20230209-training', 'gov2-trec-tb-2006-20230209-training'
            ],
            'trec-core': [
                'wapo-v2-trec-core-2018-20230107-training', 'disks45-nocr-trec8-20230209-training', 'disks45-nocr-trec7-20230209-training', 'disks45-nocr-trec-robust-2004-20230209-training'
            ]
        }

        #we publish document processors only for fully public datasets, query processors can be published on all groups
        fully_public_datasets = dataset_groups['trec-recent'] + dataset_groups['tiny-test-collections'] + dataset_groups['trec-medical'] + dataset_groups['clef-labs']

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
                },
                'salamander': {
                    'classify-comparative-queries': 'qpptk-all-predictors',
                }
                # pre-retrieval query intent, post-retrieval query intent
                # splade
                # comparative questions
                # entity linking
            }
        }
        
        ret = {}

        #for task_id in systems.keys():
        for task_id in []:
            ret[task_id] = {}
            for user_id in systems[task_id].keys():
                ret[task_id][user_id] = {}
                for display_name in systems[task_id][user_id].keys():
                    ret[task_id][user_id][display_name] = {}
                    output_dir = systems[task_id][user_id][display_name]
                    for i in tqdm(fully_public_datasets):
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
                    ret[task_id][user_id][display_name] = {}

                    for dataset_group, datasets in tqdm(dataset_groups.items(), display_name):
                        run_ids = {}
                        file_name = f'{user_id}-{display_name}-{dataset_group}'
                        target_file = f'{output_dir}/{file_name}.zip'

                        for dataset in datasets:
                            runs_on_dataset = model.runs(task_id, dataset, user_id, display_name)
                            if len(runs_on_dataset) > 0:
                                run_ids[dataset] = runs_on_dataset[0]
                            else:
                                print(f'skip dataset {dataset} for {display_name}')


                        if len(run_ids) == 0:
                            print(f'Skip group {dataset_group} for {display_name}.')
                            continue

                        zip_file = zip_runs(user_id, [(k, v) for k,v in run_ids.items()], file_name)
                        shutil.copyfile(zip_file, target_file)
                        ret[task_id][user_id][display_name][dataset_group] = {'dataset_group': dataset_group, 'md5': md5(target_file), 'run_ids': run_ids}

        print(json.dumps(ret))


                    