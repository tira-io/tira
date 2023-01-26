import requests
import json
import pandas as pd

class Client():
    def __init__(self, api_key):
        self.__api_key = api_key
        self.fail_if_api_key_is_invalid()

    def fail_if_api_key_is_invalid(self):
        role = self.json_response('/api/role')
        
        if not role or 'status' not in role or 'role' not in role or 0 != role['status']:
            raise ValueError('It seems like the api key is invalid. Got: ', role)

    def datasets(self, task):
        return self.json_response('/api/datasets_by_task/{task}')['context']['datasets']

    def submissions(self, task, dataset):
        response = self.json_response(f'/api/submissions/{task}/{dataset}')
        if 'status' not in response or 'context' not in response or response['status'] != 1:
            raise ValueError('Got invalid response: ', json.dumps(response)[:150])
        
        response = response['context']
        
        ret = []
        
        for vm in response['vms']:
            for run in vm['runs']:
                for k,v in run['review'].items():
                    run['review_' + k] = v
                del run['review']

                ret += [{**{'task': response['task_id'], 'dataset': response['dataset_id'], 'team': vm['vm_id']}, **run}]

        return pd.DataFrame(ret)

    def json_response(self, endpoint, params=None):
        headers = {"Api-Key": self.__api_key, "Accept": "application/json"}
        resp = requests.get(url='https://www.tira.io' + endpoint, headers=headers, params=params)
        
        return resp.json()

