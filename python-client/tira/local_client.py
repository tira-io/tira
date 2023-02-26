import requests
import json
import pandas as pd
import os
import zipfile
import io
import docker
import time
from glob import glob
from random import random
from packaging import version
from tira.pyterrier_integration import PyTerrierIntegration
from tira.local_execution_integration import LocalExecutionIntegration


class Client():
    def __init__(self, directory='.'):
        self.pt = PyTerrierIntegration(self)
        self.directory = directory + '/'
        self.tira_cache_dir = os.environ.get('TIRA_CACHE_DIR', os.path.expanduser('~') + '/.tira')
        self.local_execution = LocalExecutionIntegration(self)

    def all_datasets(self):
        ret = []
        for i in glob(self.directory + '*/training-datasets/'):
            cnt = 0
            for j in glob(i + '*'):
                cnt += len(list(open(j)))
        
            ret += [{'dataset': i.split('/training-datasets/')[0], 'records': cnt}]

        for i in set([j.split('/')[1] for j in glob(self.directory + '**/**/**/job-executed-on-*.txt')]):
            ret += [{'dataset': i}]

        return pd.DataFrame(ret).sort_values('dataset')

    def ___load_softwares(self):
        softwares = [json.loads(i) for i in open('.tira/submitted-software.jsonl')]

        return {i['TIRA_TASK_ID'] + '/' + i['TIRA_VM_ID'] + '/' + i['TIRA_SOFTWARE_NAME']: i for i in softwares}

    def all_softwares(self):
        ret = []
        for software_id, software_definition in self.___load_softwares().items():
            ret += [{'approach': software_id, 'id': str(int(software_definition['TIRA_SOFTWARE_ID'].split('docker-software-')[1])), 'team': software_definition['TIRA_VM_ID'], 'image': software_definition['TIRA_IMAGE_TO_EXECUTE_IN_DOCKERHUB'], 'command': software_definition['TIRA_COMMAND_TO_EXECUTE'], 'ids_of_previous_stages': [str(int(i)) for i in software_definition['TIRA_IDS_OF_PREVIOUS_STAGES']]}]

        return pd.DataFrame(ret)

    def __load_evaluators(self):
        evaluators = [json.loads(i) for i in open('.tira/evaluators.jsonl')]
        ret = {i['TIRA_DATASET_ID']: i for i in evaluators}

        for evaluator in evaluators:
            dataset_id = evaluator['TIRA_DATASET_ID']
            current_version = version.parse(ret[dataset_id]['TIRA_EVALUATION_IMAGE_TO_EXECUTE'].split(':')[-1])
            available_version = version.parse(evaluator['TIRA_EVALUATION_IMAGE_TO_EXECUTE'].split(':')[-1])

            if available_version > current_version:
                ret[dataset_id] = evaluator

        return ret

    def __load_job_data(self, job_file):
        job = [i.split('=', 1) for i in open(job_file, 'r')]
        return {k.strip():v.strip() for k,v in job}

    def all_evaluators(self):
        ret = []
        for i in self.__load_evaluators().values():
            ret += [{'dataset': i['TIRA_DATASET_ID'], 'image': i['TIRA_EVALUATION_IMAGE_TO_EXECUTE'], 'command': i['TIRA_EVALUATION_COMMAND_TO_EXECUTE']}]

        return pd.DataFrame(ret)

    def __extract_image_and_command(self, identifier, evaluator=False):
        softwares = self.___load_softwares() if not evaluator else self.__load_evaluators()

        if identifier in softwares and not evaluator:
            return softwares[identifier]['TIRA_IMAGE_TO_EXECUTE'], softwares[identifier]['TIRA_COMMAND_TO_EXECUTE']
        if evaluator:
            for k, v in softwares.items():
                if k.startswith(identifier):
                    return v['TIRA_DATASET_ID'], v['TIRA_EVALUATION_IMAGE_TO_EXECUTE'], v['TIRA_EVALUATION_COMMAND_TO_EXECUTE']

        raise ValueError(f'There is no {("evaluator" if evaluator else "software")} identified by "{identifier}". Choices are: {sorted(list(softwares))}')

    def all_evaluated_appraoches(self):
        id_to_software_name = {int(i['TIRA_SOFTWARE_ID'].split('docker-software-')[1]):i['TIRA_SOFTWARE_NAME'] for i in self.___load_softwares().values()}
        ret = []
        for evaluation in glob('*/*/*/evaluation'):
            job_dir = glob(evaluation + '/../job-executed-on*.txt')
            if len(job_dir) != 1:
                raise ValueError('Can not handle multiple job definitions: ', job_dir)
            
            job_definition = self.__load_job_data(job_dir[0])
            job_identifier = job_definition['TIRA_TASK_ID'] + '/' + job_definition['TIRA_VM_ID'] + '/' + id_to_software_name[int(job_definition['TIRA_SOFTWARE_ID'].split('docker-software-')[1])]
        
            for eval_run in glob(f"{evaluation}/*/output/"):        
                try:
                    i = {'approach': job_identifier, 'dataset': job_definition['TIRA_DATASET_ID']}
                    i.update(self.__load_output(eval_run, evaluation=True))
                    ret += [i]
                except:
                    pass

        return pd.DataFrame(ret)

    def docker_software(self, approach, software_id=None):
        ret = []

        for _, i in self.all_softwares().iterrows():
            if (approach and i['approach'] == approach) or (software_id is not None and str(int(software_id)) == i['id']):
                ret += [{'tira_image_name': i['image'], 'command': i['command'], 'id': i['id'], 'ids_of_previous_stages': i['ids_of_previous_stages']}]

        if len(ret) == 1:
            return ret[0]

        raise ValueError(f'Could not find a unique software with approach="{approach}" or software_id="{software_id}". Found {ret}')

    def submissions(self, task, dataset):
        response = self.json_response(f'/api/submissions/{task}/{dataset}')['context']
        ret = []
        
        for vm in response['vms']:
            for run in vm['runs']:
                if 'review' in run:
                    for k,v in run['review'].items():
                        run['review_' + k] = v
                    del run['review']

                ret += [{**{'task': response['task_id'], 'dataset': response['dataset_id'], 'team': vm['vm_id']}, **run}]

        return pd.DataFrame(ret)

    def evaluations(self, task, dataset, join_submissions=True):
        response = self.json_response(f'/api/evaluations/{task}/{dataset}')['context']
        ret = []
        evaluation_keys = response['ev_keys']

        if join_submissions:
            runs_to_join = {}
            for _, i in self.submissions(task, dataset).iterrows():
                i = i.to_dict()
                runs_to_join[(i['team'], i['run_id'])] = {'software': i['software'], 'input_run_id': i['input_run_id'], 'is_upload': i['is_upload'], 'is_docker': i['is_docker']}

        for evaluation in response['evaluations']:
            run = {'task': response['task_id'], 'dataset': response['dataset_id'], 'team': evaluation['vm_id'], 'run_id': evaluation['input_run_id']}

            if join_submissions and (run['team'], run['run_id']) in runs_to_join:
                software = runs_to_join[(run['team'], run['run_id'])]
                for k,v in software.items():
                    run[k] = v

            for measure_id, measure in zip(range(len(evaluation_keys)), evaluation_keys):
                run[measure] = evaluation['measures'][measure_id]

            ret += [run]

        return pd.DataFrame(ret)

    def run_was_already_executed_on_dataset(self, approach, dataset):
        return self.get_run_execution_or_none(approach, dataset) is not None

    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None):
        task, team, software = approach.split('/')
        
        df_eval = self.evaluations(task=task, dataset=dataset)

        ret = df_eval[(df_eval['dataset'] == dataset) & (df_eval['software'] == software)]
        if len(ret) <= 0:
            return None
        
        if team:
            ret = ret[ret['team'] == team]

        if len(ret) <= 0:
            return None

        if previous_stage_run_id:
            ret = ret[ret['input_run_id'] == previous_stage_run_id]

        if len(ret) <= 0:
            return None

        return ret[['task', 'dataset', 'team', 'run_id']].iloc[0].to_dict()
        
    def download_run(self, task, dataset, software, team=None, previous_stage=None, return_metadata=False):
        ret = self.get_run_execution_or_none(f'{task}/{team}/{software}', dataset, previous_stage)
        if not ret:
            raise ValueError(f'I could not find a run for the filter criteria task="{task}", dataset="{dataset}", software="{software}", team={team}, previous_stage={previous_stage}')
        run_id = ret['run_id']
        
        ret = self.download_zip_to_cache_directory(**ret)
        ret = pd.read_csv(ret + '/run.txt', sep='\\s+', names=["query", "q0", "docid", "rank", "score", "system"])
        if return_metadata:
            return ret, run_id
        else:
            return ret

    def download_zip_to_cache_directory(self, task, dataset, team, run_id):
        target_dir = f'{self.__tira_cache_dir}/extracted_runs/{task}/{dataset}/{team}'

        if os.path.isdir(target_dir + f'/{run_id}'):
            return target_dir + f'/{run_id}/output'

        self.download_and_extract_zip(f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip', target_dir)

        return target_dir + f'/{run_id}/output'

    def download_and_extract_zip(self, url, target_dir):
        for i in range(self.failsave_retries):
            try:
                r = requests.get(url, headers={"Api-Key": self.api_key})
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(target_dir)
                
                return
            except:
                sleep_time = 1+int(random()*self.failsave_max_delay)
                print(f'Error occured while fetching {url}. I will sleep {sleep_time} seconds and continue.')
                time.sleep(sleep_time)

