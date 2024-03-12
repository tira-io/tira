import unittest
from approvaltests import verify_as_json
from tira.tira_redirects import redirects, mirror_url
from tira.rest_api_client import Client
import requests
from hashlib import md5

def md5_of_first_kilobyte_of_http_resource(url):
    if not url.startswith('https://files.webis.de') and not url.startswith('https://zenodo.org/records'):
        raise ValueError(f'URL {url} is not from webis.de respectively zenodo')
    return md5(requests.get(url, headers={'Range': f'bytes=0-1024'}).content).hexdigest()

RUN_IDS = {
    "ir-benchmarks": {
        "tira-ir-starter": {
            "Index (tira-ir-starter-pyterrier)": {"msmarco-passage-trec-dl-2019-judged-20230107-training": "2023-01-07-22-09-56", "msmarco-passage-trec-dl-2020-judged-20230107-training": "2023-01-07-22-09-56", "antique-test-20230107-training": "2023-01-07-13-40-04", "vaswani-20230107-training": "2023-01-07-19-01-50", "cranfield-20230107-training": "2023-01-07-13-39-11", "medline-2004-trec-genomics-2004-20230107-training": "2023-01-07-19-37-49", "medline-2017-trec-pm-2017-20230211-training": "2023-02-11-20-52-47", "cord19-fulltext-trec-covid-20230107-training": "2023-01-08-15-18-20", "nfcorpus-test-20230107-training": "2023-02-09-15-46-37", "argsme-touche-2020-task-1-20230209-training": "2023-02-09-17-50-22", "argsme-touche-2021-task-1-20230209-training": "2023-02-09-17-50-22", "medline-2017-trec-pm-2018-20230211-training": "2023-02-11-15-15-35", "medline-2004-trec-genomics-2005-20230107-training": "2023-02-09-22-14-32", "trec-tip-of-the-tongue-dev-20230607-training": "2023-11-10-23-23-59", "longeval-short-july-20230513-training": "2023-11-10-23-22-59", "longeval-heldout-20230513-training": "2023-11-10-23-21-55", "longeval-long-september-20230513-training": "2023-11-10-21-09-17", "longeval-train-20230513-training": "2023-11-11-06-49-15"}
        },
        "qpptk": {
            "all-predictors": {"msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-27-21-30-47", "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-27-21-31-54", "trec-tip-of-the-tongue-dev-20230607-training": "2024-02-27-21-36-40", "antique-test-20230107-training": "2024-02-27-20-06-32", "vaswani-20230107-training": "2024-02-27-21-38-47", "cranfield-20230107-training": "2024-02-27-20-20-33", "nfcorpus-test-20230107-training": "2024-02-27-21-34-23", "medline-2004-trec-genomics-2004-20230107-training": "2024-02-27-21-21-07", "medline-2017-trec-pm-2017-20230211-training": "2024-02-27-21-27-05", "cord19-fulltext-trec-covid-20230107-training": "2024-02-27-20-18-28", "medline-2017-trec-pm-2018-20230211-training": "2024-02-27-21-28-47", "medline-2004-trec-genomics-2005-20230107-training": "2024-02-27-21-26-22", "argsme-touche-2020-task-1-20230209-training": "2024-02-27-20-09-14", "argsme-touche-2021-task-1-20230209-training": "2024-02-27-20-10-51", "longeval-short-july-20230513-training": "2024-02-27-21-15-17", "longeval-heldout-20230513-training": "2024-02-27-20-56-41", "longeval-long-september-20230513-training": "2024-02-27-21-10-42", "longeval-train-20230513-training": "2024-02-27-21-19-19", "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-27-20-13-20", "gov-trec-web-2002-20230209-training": "2024-02-27-20-26-06", "gov-trec-web-2003-20230209-training": "2024-02-27-20-27-09", "gov-trec-web-2004-20230209-training": "2024-02-27-20-29-21", "gov2-trec-tb-2004-20230209-training": "2024-02-27-20-30-58", "gov2-trec-tb-2005-20230209-training": "2024-02-27-20-33-27", "gov2-trec-tb-2006-20230209-training": "2024-02-27-20-37-51", "wapo-v2-trec-core-2018-20230107-training": "2024-02-27-21-40-17", "disks45-nocr-trec8-20230209-training": "2024-02-27-20-24-50", "disks45-nocr-trec7-20230209-training": "2024-02-27-20-23-24", "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-27-20-22-13"}
        },
        "salamander": {
            "classify-comparative-queries": {"msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-25-16-58-54", "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-25-20-36-41", "antique-test-20230107-training": "2024-02-25-15-17-55", "vaswani-20230107-training": "2024-02-25-20-40-09", "cranfield-20230107-training": "2024-02-25-15-45-40", "nfcorpus-test-20230107-training": "2024-02-25-20-37-46", "medline-2004-trec-genomics-2004-20230107-training": "2024-02-25-16-09-36", "medline-2017-trec-pm-2017-20230211-training": "2024-02-25-16-12-21", "cord19-fulltext-trec-covid-20230107-training": "2024-02-25-15-44-30", "medline-2017-trec-pm-2018-20230211-training": "2024-02-25-16-57-26", "medline-2004-trec-genomics-2005-20230107-training": "2024-02-25-16-11-16", "argsme-touche-2020-task-1-20230209-training": "2024-02-25-15-19-08", "argsme-touche-2021-task-1-20230209-training": "2024-02-25-15-20-13", "longeval-short-july-20230513-training": "2024-02-25-16-04-17", "longeval-heldout-20230513-training": "2024-02-25-16-01-03", "longeval-long-september-20230513-training": "2024-02-25-16-03-12", "longeval-train-20230513-training": "2024-02-25-16-06-29", "clueweb09-en-trec-web-2009-20230107-training": "2024-02-25-15-21-18", "clueweb09-en-trec-web-2010-20230107-training": "2024-02-25-15-24-17", "clueweb09-en-trec-web-2011-20230107-training": "2024-02-25-15-25-22", "clueweb09-en-trec-web-2012-20230107-training": "2024-02-25-15-26-28", "clueweb12-touche-2020-task-2-20230209-training": "2024-02-25-15-27-38", "clueweb12-touche-2021-task-2-20230209-training": "2024-02-25-15-28-44", "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-25-15-29-50", "clueweb12-trec-web-2013-20230107-training": "2024-02-25-15-30-55", "clueweb12-trec-web-2014-20230107-training": "2024-02-25-15-32-03", "gov-trec-web-2002-20230209-training": "2024-02-25-15-51-54", "gov-trec-web-2003-20230209-training": "2024-02-25-15-53-06", "gov-trec-web-2004-20230209-training": "2024-02-25-15-54-30", "gov2-trec-tb-2004-20230209-training": "2024-02-25-15-55-44", "gov2-trec-tb-2005-20230209-training": "2024-02-25-15-58-17", "gov2-trec-tb-2006-20230209-training": "2024-02-25-15-59-47", "wapo-v2-trec-core-2018-20230107-training": "2024-02-25-20-41-24", "disks45-nocr-trec8-20230209-training": "2024-02-25-15-51-07", "disks45-nocr-trec7-20230209-training": "2024-02-25-15-49-58", "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-25-15-48-48"}
        }
    }
}

class TestRedirects(unittest.TestCase):
    """
    def test_approve_all_redirects(self):
        softwareto_approve = sorted(['ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)'])
        datasets_to_approve = sorted([
            'msmarco-passage-trec-dl-2019-judged-20230107-training', 'msmarco-passage-trec-dl-2020-judged-20230107-training',
            'antique-test-20230107-training', 'vaswani-20230107-training',
            'cranfield-20230107-training', 'medline-2004-trec-genomics-2004-20230107-training',
            'medline-2017-trec-pm-2017-20230211-training', 'cord19-fulltext-trec-covid-20230107-training',
            'nfcorpus-test-20230107-training', 'argsme-touche-2020-task-1-20230209-training', 
            'argsme-touche-2021-task-1-20230209-training', 'medline-2017-trec-pm-2018-20230211-training', 'medline-2004-trec-genomics-2005-20230107-training', 'trec-tip-of-the-tongue-dev-20230607-training',
            'longeval-short-july-20230513-training', 'longeval-heldout-20230513-training',
            'longeval-long-september-20230513-training', 'longeval-train-20230513-training'
        ])
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
        """

    def test_redirects_in_incubator(self):
        softwareto_approve = sorted(['ir-benchmarks/salamander/classify-comparative-queries', 'ir-benchmarks/qpptk/all-predictors'])
        datasets_to_approve = sorted([
            'msmarco-passage-trec-dl-2019-judged-20230107-training', 'msmarco-passage-trec-dl-2020-judged-20230107-training',
            'antique-test-20230107-training', 'vaswani-20230107-training',
            'cranfield-20230107-training', 'medline-2004-trec-genomics-2004-20230107-training',
            'medline-2017-trec-pm-2017-20230211-training', 'cord19-fulltext-trec-covid-20230107-training',
            'nfcorpus-test-20230107-training', 'argsme-touche-2020-task-1-20230209-training', 
            'argsme-touche-2021-task-1-20230209-training', 'medline-2017-trec-pm-2018-20230211-training', 'medline-2004-trec-genomics-2005-20230107-training', 'trec-tip-of-the-tongue-dev-20230607-training',
            'longeval-short-july-20230513-training', 'longeval-heldout-20230513-training',
            'longeval-long-september-20230513-training', 'longeval-train-20230513-training'
        ])
        tira = Client()

        ret = {}
        for software in softwareto_approve:
            ret[software] = {}
            for dataset in datasets_to_approve:
                task, team, system = software.split('/')
                if dataset not in RUN_IDS[task][team][system]:
                    continue

                run_url = f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{RUN_IDS[task][team][system][dataset]}.zip'
                redirected_run_url = redirects(url=run_url)['urls'][0]
                if not redirected_run_url.startswith('https://files.'):
                    continue

                ret[software][dataset] = {
                    'redirect_url': redirects(software, dataset),
                    'run_execution': tira.get_run_execution_or_none(software, dataset),
                    'run_url': run_url,
                    'redirected_run_url': redirected_run_url,
                    'md5_of_first_kilobyte': md5_of_first_kilobyte_of_http_resource(redirects(url=run_url)['urls'][0])
                }
        
        verify_as_json(ret)


    def test_mirrors_for_zenodo(self):
        softwareto_approve = sorted(['ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)'])
        datasets_to_approve = sorted([
            'msmarco-passage-trec-dl-2019-judged-20230107-training', 'msmarco-passage-trec-dl-2020-judged-20230107-training',
            'antique-test-20230107-training', 'vaswani-20230107-training',
            'cranfield-20230107-training', 'medline-2004-trec-genomics-2004-20230107-training',
            'medline-2017-trec-pm-2017-20230211-training', 'cord19-fulltext-trec-covid-20230107-training',
            'nfcorpus-test-20230107-training', 'argsme-touche-2020-task-1-20230209-training', 
            'argsme-touche-2021-task-1-20230209-training', 'medline-2017-trec-pm-2018-20230211-training', 'medline-2004-trec-genomics-2005-20230107-training', 'trec-tip-of-the-tongue-dev-20230607-training',
            'longeval-short-july-20230513-training', 'longeval-heldout-20230513-training',
            'longeval-long-september-20230513-training', 'longeval-train-20230513-training'
        ])

        ret = {}
        for software in softwareto_approve:
            for dataset in datasets_to_approve:
                task, team, system = software.split('/')
                run_url = f'https://www.tira.io/task/{task}/user/{team}/dataset/{dataset}/download/{RUN_IDS[task][team][system][dataset]}.zip'
                run_url = redirects(url=run_url)['urls'][0]
                ret[run_url] = mirror_url(run_url)

        verify_as_json(ret)
