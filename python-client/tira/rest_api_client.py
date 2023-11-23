import requests
import json
import pandas as pd
import os
import zipfile
import io
import docker
import time
from random import randint
from tira.pyterrier_integration import PyTerrierIntegration
from tira.pandas_integration import PandasIntegration
from tira.local_execution_integration import LocalExecutionIntegration
import logging


class Client():
    def __init__(self, api_key=None, failsave_retries=5, failsave_max_delay=15, api_user_name=None):
        self.tira_cache_dir = os.environ.get('TIRA_CACHE_DIR', os.path.expanduser('~') + '/.tira')
        self.json_cache = {}

        if api_key is None:
            self.api_key = self.load_settings()['api_key']
            self.api_user_name = self.load_settings()['api_user_name']
        else:
            self.api_key = api_key
            self.api_user_name = api_user_name

        self.failsave_retries = 1
        if self.api_key != 'no-api-key':
            self.fail_if_api_key_is_invalid()
        self.pd = PandasIntegration(self)
        self.pt = PyTerrierIntegration(self)
        self.local_execution = LocalExecutionIntegration(self)

        self.failsave_retries = failsave_retries
        self.failsave_max_delay = failsave_max_delay

    def load_settings(self):
        try:
            return json.load(open(self.tira_cache_dir + '/.tira-settings.json', 'r'))
        except Exception:
            logging.info(f'No settings given in {self.tira_cache_dir}/.tira-settings.json. I will use defaults.')
            return {'api_key': 'no-api-key', 'api_user_name': 'no-api-key-user'}

    def fail_if_api_key_is_invalid(self):
        role = self.json_response('/api/role')
        
        if not role or 'status' not in role or 'role' not in role or 0 != role['status']:
            raise ValueError('It seems like the api key is invalid. Got: ', role)

    def datasets(self, task):
        return json.loads(self.json_response(f'/api/datasets_by_task/{task}')['context']['datasets'])

    def docker_software_id(self, approach):
        return self.docker_software(approach)['docker_software_id']

    def all_softwares(self, task_id):
        """
        Return all public submissions.
        """
        return [task_id + '/' + i['vm_id'] + '/' + i['display_name'] for i in self.json_response(f'/api/task/{task_id}/public-submissions')['context']['public_submissions']]

    def docker_software(self, approach):
        task, team, software = approach.split('/')
        return self.json_response(f'/api/task/{task}/submission-details/{team}/{software}')['context']['submission']

    def docker_software_details(self, approach):
        task, team, software = approach.split('/')
        ret = self.json_response(f'/task/{task}/vm/{team}/software_details/{software}')

        return ret

    def metadata_for_task(self, task_name, team_name):
        return self.json_response(f'/api/task/{task_name}/user/{team_name}')

    def add_docker_software(self, image, command, tira_vm_id, tira_task_id, code_repository_id, build_environment):
        headers = {   
            'Api-Key': self.api_key,
            'Api-Username': self.api_user_name,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        self.fail_if_api_key_is_invalid()
        url = f'https://www.tira.io/task/{tira_task_id}/vm/{tira_vm_id}/add_software/docker'
        ret = requests.post(url, headers=headers, json={"action": "post", "image": image, "command": command, "code_repository_id": code_repository_id,"build_environment": json.dumps(build_environment)})
        ret = ret.content.decode('utf8')
        ret = json.loads(ret)

        assert ret['status'] == 0
        logging.info(f'Software with name {ret["context"]["display_name"]} was created.')
        logging.info(f'Please visit https://www.tira.io/submit/{tira_task_id}/user/{tira_vm_id}/docker-submission to run your software.')

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

    def submissions_with_evaluation_or_none(self, task, dataset, team, software):
        """ This method returns all runs of the specified software in the task on the dataset by the team.
            This is especially suitable to batch evaluate all submissions of the software because the evaluation is none if no successfull evaluation was conducted (or there is a new evaluator).
            E.g., by code like:

            ```
            for approach in ['approach-1', ..., 'approach-n]:
                runs_for_approach = tira.submissions_with_evaluation_or_none(task, dataset, team, approach)
                for i in runs_for_approach:
                    if not i['evaluation']:
                        tira.evaluate_run(team, dataset, i['run_id'])
            ```
        """
        submissions = self.submissions(task, dataset)
        evaluations = self.evaluations(task, dataset, join_submissions=False)
        run_to_evaluation = {}
        for _, i in evaluations.iterrows():
            i = i.to_dict()
            run_id = i["run_id"]
            del i['task']
            del i['dataset']
            del i['team']
            del i['run_id']
            run_to_evaluation[run_id] = i

        if len(submissions) < 1:
            return []

        submissions = submissions[(submissions['task'] == task) & (submissions['dataset'] == dataset) & (submissions['team'] == team) & (submissions['software'] == software)]
        ret = []
        for run_id in submissions.run_id.unique():
            ret += [{"run_id": run_id, "task": task, "dataset": dataset, "team": team, "software": software, "evaluation": run_to_evaluation.get(run_id, None)}]

        return ret

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
            run = {'task': response['task_id'], 'dataset': response['dataset_id'], 'team': evaluation['vm_id'], 'run_id': evaluation['input_run_id'], 'evaluation_run_id': evaluation['run_id'], 'published': evaluation['published'], 'blinded': evaluation['blinded']}

            if join_submissions and (run['team'], run['run_id']) in runs_to_join:
                software = runs_to_join[(run['team'], run['run_id'])]
                for k, v in software.items():
                    run[k] = v

            for measure_id, measure in zip(range(len(evaluation_keys)), evaluation_keys):
                run[measure] = evaluation['measures'][measure_id]

            ret += [run]

        return pd.DataFrame(ret)

    def run_was_already_executed_on_dataset(self, approach, dataset):
        return self.get_run_execution_or_none(approach, dataset) is not None

    def get_run_output(self, approach, dataset, allow_without_evaluation=False):
        """
        Downloads the run (or uses the cached version) of the specified approach on the specified dataset.
        Returns the directory containing the outputs of the run.
        """
        task, team, software = approach.split('/')
        run_execution = self.get_run_execution_or_none(approach, dataset)
        if run_execution:
            return self.download_zip_to_cache_directory(task, dataset, team, run_execution['run_id'])

        run_execution = self.submissions_with_evaluation_or_none(task, dataset, team, software)
        run_execution = [i for i in run_execution if ('evaluation' in i and i['evaluation']) or allow_without_evaluation]

        if run_execution is None or len(run_execution) < 1:
            raise ValueError(f'Could not get run for approach "{approach}" on dataset "{dataset}".')

        return self.download_zip_to_cache_directory(run_execution[0]['task'], run_execution[0]['dataset'], run_execution[0]['team'], run_execution[0]['run_id'])

    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None):
        task, team, software = approach.split('/')

        public_runs = self.json_response(f'/api/list-runs/{task}/{dataset}/{team}/' + software.replace(' ', '%20'))
        if public_runs and 'context' in public_runs and 'runs' in public_runs['context'] and public_runs['context']['runs']:
            return {'task': task, 'dataset': dataset, 'team': team, 'run_id': public_runs['context']['runs'][0]}

        df_eval = self.submissions_of_team(task=task, dataset=dataset, team=team)
        if len(df_eval) <= 0:
            return None

        ret = df_eval[(df_eval['dataset'] == dataset) & (df_eval['software'] == software)]
        if len(ret) <= 0:
            return None
        
        if team:
            ret = ret[ret['team'] == team]

        # FIXME: Is this really necessary or is it checked with the if len(ret) <= 0 later on?
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
        ret = pd.read_csv(ret + '/run.txt', sep='\\s+', names=["query", "q0", "docid", "rank", "score", "system"], dtype={"query": str, "docid": str})
        if return_metadata:
            return ret, run_id
        else:
            return ret

    def download_evaluation(self, task, dataset, software, team):
        ret = self.submissions_with_evaluation_or_none(task, dataset, team, software)
        if not ret or len(ret) < 1:
            raise ValueError(f'I could not find a run for the filter criteria task="{task}", dataset="{dataset}", software="{software}", team={team}.')
        run_id = ret[0]['run_id']

        submissions = self.submissions(task, dataset)
        submissions = submissions[(submissions['input_run_id'] == run_id) & (submissions['is_evaluation'])]

        if submissions is None or len(submissions) < 1:
            raise ValueError(f'I could not find a evaluation for the filter criteria task="{task}", dataset="{dataset}", software="{software}", team={team}, run_id={run_id}.')

        return self.download_zip_to_cache_directory(task, dataset, team, submissions.iloc[0].to_dict()['run_id'])

    def download_dataset(self, task, dataset, truth_dataset=False):
        """
        Download the dataset. Set truth_dataset to true to load the truth used for evaluations.
        """
        target_dir = f'{self.tira_cache_dir}/extracted_datasets/{task}/{dataset}/'
        suffix = ("input-data" if not truth_dataset else "truth-data")
        if os.path.isdir(target_dir + suffix):
            return target_dir + suffix
        data_type = 'training' if dataset.endswith('-training') else 'test'
        self.download_and_extract_zip(f'https://www.tira.io/data-download/{data_type}/input-{("" if not truth_dataset else "truth")}/{dataset}.zip', target_dir)

        os.rename(target_dir + f'/{dataset}', target_dir + suffix)

        return target_dir + suffix

    def download_zip_to_cache_directory(self, task, dataset, team, run_id):
        target_dir = f'{self.tira_cache_dir}/extracted_runs/{task}/{dataset}/{team}'

        if os.path.isdir(target_dir + f'/{run_id}'):
            return target_dir + f'/{run_id}/output'

        self.download_and_extract_zip(f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip', target_dir)

        return target_dir + f'/{run_id}/output'

    def add_run_to_leaderboard(self, task, team, dataset, evaluation_run_id=None, run_id=None):
        """
        Publish the specified run to the leaderboard.
        
        This is especially suitable to batch add all submissions of submissions, e.g., by code like:

            ```
            for approach in ['approach-1', ..., 'approach-n]:
                runs_for_approach = tira.submissions_with_evaluation_or_none(task, dataset, team, approach)
                for i in runs_for_approach:
                    if i['evaluation']:
                        tira.add_run_to_leaderboard(TASK, team, dataset, run_id=i['run_id'])
        
        """
        if run_id and evaluation_run_id:
            raise ValueError(f'Please pass either a evaluation_run_id or a run_id, but both were passed: evaluation_run_id={evaluation_run_id}, run_id={run_id}')
        if run_id and not evaluation_run_id:
            submissions = self.submissions(task, dataset)
            submissions = submissions[(submissions['input_run_id'] == run_id) & (submissions['is_evaluation'])]

            for evaluation_run_id in submissions['run_id'].unique():
                self.add_run_to_leaderboard(task, team, dataset, evaluation_run_id=evaluation_run_id)

        if evaluation_run_id:
            logging.info(f'Publish run: {evaluation_run_id}.')
            ret = self.json_response(f'/publish/{team}/{dataset}/{evaluation_run_id}/true')

            if ('status' not in ret) or ('0' != ret['status']) or ('published' not in ret) or (not ret['published']):
                raise ValueError(f'Adding the run to the leaderboard failed. Got {ret}')

    def get_configuration_of_evaluation(self, task_id, dataset_id):
        """ Get the configuration of the evaluator for the passed dataset inside the task specified by task_id.
        """
        ret = self.json_response(f'/api/configuration-of-evaluation/{task_id}/{dataset_id}')

        if 'status' not in ret or '0' != str(ret['status']):
            raise ValueError(f'Failed to load configuration of an evaluator. Got {ret}')

        return ret['context']['dataset']

    def evaluate_run(self, team, dataset, run_id):
        """ Evaluate the run of the specified team and identified by the run_id (the run must be submitted on the specified dataset).
        """
        ret = self.json_response(f'/grpc/{team}/run_eval/{dataset}/{run_id}')

        if 'status' not in ret or '0' != str(ret['status']):
            raise ValueError(f'Failed to evaluate the run. Got {ret}')

        return ret

    def download_and_extract_zip(self, url, target_dir):
        for i in range(self.failsave_retries):
            status_code = None
            try:
                headers={"Api-Key": self.api_key, "Api-Username": self.api_user_name}
                if self.api_key == 'no-api-key':
                    del headers["Api-Key"]
                if self.api_user_name == 'no-api-key-user':
                    del headers["Api-Username"]

                r = requests.get(url, headers=headers)
                status_code = r.status_code
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(target_dir)

                return
            except Exception as e:
                sleep_time = randint(1, self.failsave_max_delay)
                logging.info(f'Code: {status_code}')
                logging.info(f'Error occured while fetching {url}. I will sleep {sleep_time} seconds and continue.', exc_info=e)
                time.sleep(sleep_time)

    def get_authentication_cookie(self, user, password):
        import requests

        resp = requests.get('https://www.tira.io/session/csrf', headers={'x-requested-with': 'XMLHttpRequest'})

        header = {
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': '_forum_session=' + resp.cookies['_forum_session'],
            'x-csrf-token': resp.json()['csrf'],
            'x-requested-with': 'XMLHttpRequest'
        }

        resp = requests.post('https://www.tira.io/session', data=f'login={user}&password={password}', headers=header)

        return f'_t={resp.cookies["_t"]}; _forum_session={resp.cookies["_forum_session"]}'

    def run_software(self, approach, dataset, resources, rerank_dataset='none'):
        task, team, software = approach.split('/')
        authentication_cookie = self.get_authentication_cookie(self.load_settings()['user'], self.load_settings()['password'])

        software_id = self.docker_software_id(approach)
        if not software_id:
            raise ValueError(f'Could not find software id for "{approach}". Got: "{software_id}".')

        url = f'https://www.tira.io/grpc/{task}/{team}/run_execute/docker/{dataset}/{software_id}/{resources}/{rerank_dataset}'
        logging.info(f'Start software...\n\t{url}\n')

        csrf_token = self.get_csrf_token()
        headers = {
            # 'Api-Key': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cookie': authentication_cookie,
            'x-csrftoken': csrf_token,
        }

        ret = requests.post(url, headers=headers, json={"csrfmiddlewaretoken": csrf_token, "action": "post"})
        ret = ret.content.decode('utf8')
        logging.info(ret)
        ret = json.loads(ret)
        assert ret['status'] == 0

    def get_csrf_token(self):
        ret = requests.get('https://www.tira.io/', headers={"Api-Key": self.api_key})

        return ret.content.decode('utf-8').split('name="csrfmiddlewaretoken" value="')[1].split('"')[0]

    def json_response(self, endpoint, params=None):
        cache_key = endpoint + '----' + ('' if not params else json.dumps(params))

        if cache_key in self.json_cache:
            return self.json_cache[cache_key]

        headers = {"Api-Key": self.api_key, "Accept": "application/json", "Api-Username": self.api_user_name}

        if self.api_key == 'no-api-key':
            del headers["Api-Key"]

        if self.api_user_name == 'no-api-key-user':
            del headers["Api-Username"]

        for i in range(self.failsave_retries):
            try:
                resp = requests.get(url='https://www.tira.io' + endpoint, headers=headers, params=params)

                if resp.status_code not in {200, 202}:
                    raise ValueError('Got statuscode ', resp.status_code, 'for ', endpoint, '. Got', resp)
                else:
                    break
            except Exception as e:
                sleep_time = randint(1, self.failsave_max_delay)
                logging.info(f'Code: {resp.status_code}')
                logging.info(f'Error occured while fetching {endpoint}. I will sleep {sleep_time} seconds and continue.', exc_info=e)
                time.sleep(sleep_time)

        self.json_cache[cache_key] = resp.json()

        return self.json_cache[cache_key]
