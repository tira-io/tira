import unittest
from approvaltests import verify_as_json
from tira.tira_redirects import redirects
from tira.rest_api_client import Client
import requests
from hashlib import md5

def md5_of_first_kilobyte_of_http_resource(url):
    return md5(requests.get(url, headers={'Range': f'bytes=0-1024'}).content).hexdigest()

class TestRedirects(unittest.TestCase):

    def test_approve_all_redirects(self):
        softwareto_approve = sorted(['ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)'])
        datasets_to_approve = sorted(['msmarco-passage-trec-dl-2019-judged-20230107-training', 'msmarco-passage-trec-dl-2020-judged-20230107-training', 'antique-test-20230107-training'])
        tira = Client()

        ret = {}
        for software in softwareto_approve:
            ret[software] = {}
            for dataset in datasets_to_approve:
                task, team, system = software.split('/')
                run_url = f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{system}.zip'
                ret[software][dataset] = {
                    'redirect_url': redirects(software, dataset),
                    'run_execution': tira.get_run_execution_or_none(software, dataset),
                    'run_url': run_url,
                    'redirected_run_url': redirects(url=run_url),
                    'md5_of_first_kilobyte': md5_of_first_kilobyte_of_http_resource(redirects(url=run_url))
                }
        
        verify_as_json(ret)
