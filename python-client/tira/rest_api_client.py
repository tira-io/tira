import requests
import json
import pandas as pd
import os
import zipfile
import io


class Client():
    def __init__(self, api_key=None):
        self.__tira_cache_dir = os.environ.get('TIRA_CACHE_DIR', os.path.expanduser('~') + '/.tira')

        if api_key is None:
            self.__api_key = json.load(open(self.__tira_cache_dir + '/.tira-settings.json', 'r'))['api_key']
        else:
            self.__api_key = api_key

        self.fail_if_api_key_is_invalid()


    def fail_if_api_key_is_invalid(self):
        role = self.json_response('/api/role')
        
        if not role or 'status' not in role or 'role' not in role or 0 != role['status']:
            raise ValueError('It seems like the api key is invalid. Got: ', role)

    def datasets(self, task):
        return json.loads(self.json_response(f'/api/datasets_by_task/{task}')['context']['datasets'])

    def docker_software_id(self, approach):
        task, team, software = approach.split('/')
        docker_softwares = self.metadata_for_task(task, team)['context']['docker']['docker_softwares']

        for i in docker_softwares:
            if i['display_name'] == software:
                return i['docker_software_id']

    def metadata_for_task(self, task_name, team_name):
        return self.json_response(f'/api/task/{task_name}/user/{team_name}')

    def submissions(self, task, dataset):
        response = self.json_response(f'/api/submissions/{task}/{dataset}')['context']
        ret = []
        
        for vm in response['vms']:
            for run in vm['runs']:
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
                runs_to_join[(i['team'], i['run_id'])] = {'software': i['software'], 'is_upload': i['is_upload'], 'is_docker': i['is_docker']}

        for evaluation in response['evaluations']:
            run = {'task': response['task_id'], 'dataset': response['dataset_id'], 'team': evaluation['vm_id'], 'run_id': evaluation['input_run_id']}

            if join_submissions:
                software = runs_to_join[(run['team'], run['run_id'])]
                for k,v in software.items():
                    run[k] = v

            for measure_id, measure in zip(range(len(evaluation_keys)), evaluation_keys):
                run[measure] = evaluation['measures'][measure_id]

            ret += [run]

        return pd.DataFrame(ret)

    def download_run(self, task, dataset, software, team=None, previous_stage=None):
        df_eval = self.evaluations(task=task, dataset=dataset)

        ret = df_eval[(df_eval['dataset'] == dataset) & (df_eval['software'] == software)]
        if team:
            ret = ret[ret['team'] == team]
        
        if previous_stage:
            _, prev_team, prev_software = approach.split('/')
            ret = ret[ret['input_run_id'] == prev_software]

        ret = self.download_zip_to_cache_directory(**ret[['task', 'dataset', 'team', 'run_id']].iloc[0].to_dict())
        return pd.read_csv(ret + '/run.txt', sep='\\s+', names=["query", "q0", "docid", "rank", "score", "system"])

    def pt_transformer_from_run(self, approach, dataset, previous_stage=None):
        import pyterrier as pt
        task, team, software = approach.split('/')
        
        if previous_stage and type(previous_stage) != str:
            previous_stage = previous_stage.name

        ret = self.download_run(task, dataset, software, team, previous_stage)
        ret['qid'] = ret['query'].astype(str)
        ret['docid'] = ret['docid'].astype(str)
        del ret['query']
        del ret['docid']
        
        ret = pt.Transformer.from_df(ret)
        ret.name = approach
    
        return ret

    def download_zip_to_cache_directory(self, task, dataset, team, run_id):
        target_dir = f'{self.__tira_cache_dir}/extracted_runs/{task}/{dataset}/{team}'

        if os.path.isdir(target_dir + f'/{run_id}'):
            return target_dir + f'/{run_id}/output'

        r = requests.get(f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip', headers={"Api-Key": self.__api_key})
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(target_dir)
    
        return target_dir + f'/{run_id}/output'

    def run_software(self, approach, dataset, resources):
        task, team, software = approach.split('/')
        software_id = self.docker_software_id(approach)
        if not software_id:
            raise ValueError(f'Could not find software id for "{approach}". Got: "{software_id}".')
        
        url = f'https://www.tira.io/grpc/{task}/{team}/run_execute/docker/{dataset}/{software_id}/{resources}'
        print(f'Start software...\n\t{url}\n')

        ret = requests.post(url, headers={"Api-Key": discourse_api_key, "Accept": "application/json", "content-type": "application/json", 'Cookie': 'csrftoken=Rtgzr0LxAXUz39pxwsSdpKez0W8Lu9mw'})
    
        ret = ret.content.decode('utf8')

        print(ret)
        ret = json.loads(ret)
        assert ret['status'] == 0

    def json_response(self, endpoint, params=None):
        headers = {"Api-Key": self.__api_key, "Accept": "application/json"}
        resp = requests.get(url='https://www.tira.io' + endpoint, headers=headers, params=params)
        
        return resp.json()

