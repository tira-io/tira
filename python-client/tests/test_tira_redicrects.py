import unittest
from approvaltests import verify_as_json
from tira.tira_redirects import redirects
from tira.rest_api_client import Client
import requests
from hashlib import md5

def md5_of_first_kilobyte_of_http_resource(url):
    if not url.startswith('https://files.webis.de'):
        raise ValueError(f'URL {url} is not from webis.de')
    return md5(requests.get(url, headers={'Range': f'bytes=0-1024'}).content).hexdigest()

RUN_IDS = {"ir-benchmarks": {"tira-ir-starter": {"Index (tira-ir-starter-pyterrier)": {"msmarco-passage-trec-dl-2019-judged-20230107-training": "2023-01-07-22-09-56", "msmarco-passage-trec-dl-2020-judged-20230107-training": "2023-01-07-22-09-56", "antique-test-20230107-training": "2023-01-07-13-40-04", "vaswani-20230107-training": "2023-01-07-19-01-50", "cranfield-20230107-training": "2023-01-07-13-39-11", "medline-2004-trec-genomics-2004-20230107-training": "2023-01-07-19-37-49", "medline-2017-trec-pm-2017-20230211-training": "2023-02-11-20-52-47", "cord19-fulltext-trec-covid-20230107-training": "2023-01-08-15-18-20", "nfcorpus-test-20230107-training": "2023-02-09-15-46-37", "argsme-touche-2020-task-1-20230209-training": "2023-02-09-17-50-22", "argsme-touche-2021-task-1-20230209-training": "2023-02-09-17-50-31", "medline-2017-trec-pm-2018-20230211-training": "2023-02-11-15-15-35", "medline-2004-trec-genomics-2005-20230107-training": "2023-02-09-22-14-32", "trec-tip-of-the-tongue-dev-20230607-training": "2023-11-10-23-23-59", "longeval-short-july-20230513-training": "2023-11-10-23-22-59", "longeval-heldout-20230513-training": "2023-11-10-23-21-55", "longeval-long-september-20230513-training": "2023-11-10-21-09-17", "longeval-train-20230513-training": "2023-11-11-06-49-15"}}}}

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
                run_url = f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{RUN_IDS[task][team][system][dataset]}.zip'
                ret[software][dataset] = {
                    'redirect_url': redirects(software, dataset),
                    'run_execution': tira.get_run_execution_or_none(software, dataset),
                    'run_url': run_url,
                    'redirected_run_url': redirects(url=run_url),
                    'md5_of_first_kilobyte': md5_of_first_kilobyte_of_http_resource(redirects(url=run_url)['url'])
                }
        
        verify_as_json(ret)
