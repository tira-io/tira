import requests
import json
import pandas as pd
import os
import zipfile
import io
import docker
from tira.pyterrier_integration import PyTerrierIntegration


class Client():
    def __init__(self, api_key=None):
        self.__tira_cache_dir = os.environ.get('TIRA_CACHE_DIR', os.path.expanduser('~') + '/.tira')

        if api_key is None:
            self.api_key = self.load_settings()['api_key']
        else:
            self.api_key = api_key
        
        self.fail_if_api_key_is_invalid()
        self.pt = PyTerrierIntegration(self)

    def load_settings(self):
        return json.load(open(self.__tira_cache_dir + '/.tira-settings.json', 'r'))

    def fail_if_api_key_is_invalid(self):
        role = self.json_response('/api/role')
        
        if not role or 'status' not in role or 'role' not in role or 0 != role['status']:
            raise ValueError('It seems like the api key is invalid. Got: ', role)

    def datasets(self, task):
        return json.loads(self.json_response(f'/api/datasets_by_task/{task}')['context']['datasets'])

    def docker_software_id(self, approach):
        return self.docker_software(approach)['docker_software_id']

    def docker_software(self, approach):
        task, team, software = approach.split('/')
        docker_softwares = self.metadata_for_task(task, team)['context']['docker']['docker_softwares']

        for i in docker_softwares:
            if i['display_name'] == software:
                return i

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

    def download_run(self, task, dataset, software, team=None, previous_stage=None, return_metadata=False):
        df_eval = self.evaluations(task=task, dataset=dataset)

        ret = df_eval[(df_eval['dataset'] == dataset) & (df_eval['software'] == software)]
        if team:
            ret = ret[ret['team'] == team]
        
        if previous_stage:
            _, prev_team, prev_software = approach.split('/')
            ret = ret[ret['input_run_id'] == prev_software]

        ret = ret[['task', 'dataset', 'team', 'run_id']].iloc[0].to_dict()
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

        r = requests.get(f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip', headers={"Api-Key": self.api_key})
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(target_dir)
    
        return target_dir + f'/{run_id}/output'

    def run_software(self, approach, dataset, resources, rerank_dataset='none'):
        task, team, software = approach.split('/')
        authentication_cookie = self.get_authentication_cookie(self.load_settings()['user'], self.load_settings()['password'])
        
        software_id = self.docker_software_id(approach)
        if not software_id:
            raise ValueError(f'Could not find software id for "{approach}". Got: "{software_id}".')
        
        url = f'https://www.tira.io/grpc/{task}/{team}/run_execute/docker/{dataset}/{software_id}/{resources}/{rerank_dataset}'
        print(f'Start software...\n\t{url}\n')

        csrf_token = self.get_csrf_token()
        headers = {   
            #'Api-Key': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cookie': authentication_cookie,
            'x-csrftoken': csrf_token,
        }

        ret = requests.post(url, headers=headers, json={"csrfmiddlewaretoken": csrf_token, "action": "post"})
        ret = ret.content.decode('utf8')
        print(ret)
        ret = json.loads(ret)
        assert ret['status'] == 0

    def get_csrf_token(self):
        ret = requests.get('https://www.tira.io/', headers={"Api-Key": self.api_key})

        return ret.content.decode('utf-8').split('name="csrfmiddlewaretoken" value="')[1].split('"')[0]

    def json_response(self, endpoint, params=None):
        headers = {"Api-Key": self.api_key, "Accept": "application/json"}
        resp = requests.get(url='https://www.tira.io' + endpoint, headers=headers, params=params)
        
        return resp.json()

    def __normalize_command(self, cmd):
        to_normalize = {'inputRun': '/tira-data/output',
                        'outputDir': '/tira-data/output',
                        'inputDataset': '/tira-data/input'
                       }

        if 'inputRun' in cmd:
            to_normalize['outputDir'] = '/tira-data/eval_output'
            to_normalize['inputDataset'] = '/tira-data/input_truth'
    
        for k,v in to_normalize.items():
            cmd = cmd.replace('$' + k, v).replace('${' + k + '}', v)
    
        return cmd


    def run(self, identifier=None, image=None, command=None, input_dir=None, output_dir=None, evaluate=False, verbose=False):
        if image is None or command is None:
            ds = self.docker_software(identifier)
            image, command = ds['tira_image_name'], ds['command']
        try:
            client = docker.from_env()
        
            assert len(client.images.list()) >= 0
            assert len(client.containers.list()) >= 0
        except Exception as e:
            raise ValueError('It seems like docker is not installed?', e)

        command = self.__normalize_command(command)
    
        if not input_dir or not output_dir:
            raise ValueError('please pass input_dir and output_dir')
    
        input_dir = os.path.abspath(input_dir)
        output_dir = os.path.abspath(output_dir)
    
        if verbose:
            print(f'Run software with: docker run --rm -ti -v {input_dir}:/tira-data/input:ro -v {output_dir}:/tira-data/output:rw --entrypoint sh {image} {command}')
    
        client.containers.run(image, entrypoint='sh', command=f'-c "{command}"', volumes={
            str(input_dir): {'bind': '/tira-data/input', 'mode': 'ro'},
            str(output_dir): {'bind': '/tira-data/output', 'mode': 'rw'}
        })
    
        if evaluate:
            if type(evaluate) is not str:
                evaluate = data
            evaluate, image, command = __extract_image_and_command(evaluate, evaluator=True)
            command = __normalize_command(command)
            if verbose:
                print(f'Evaluate software with: docker run --rm -ti -v {input_dir}:/tira-data/input -v {output_dir}/:/tira-data/output --entrypoint sh {image} -c \'{command}\'')
        
            client.containers.run(image, entrypoint='sh', command=f'-c "{command}"', volumes={str(data_dir): {'bind': '/tira-data/', 'mode': 'rw'}})

        if evaluate:
            approach_name = identifier if identifier else f'"{command}"@{image}'
            eval_results = {'approach': approach_name, 'evaluate': evaluate}
            eval_results.update(load_output_of_directory(Path(data_dir) / 'eval_output', evaluation=True, verbose=verbose))
            return load_output_of_directory(Path(data_dir) / 'output', verbose=verbose), pd.DataFrame([eval_results])
        else:
            return load_output_of_directory(Path(data_dir) / 'output', verbose=verbose)



