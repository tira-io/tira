

STATIC_REDIRECTS = {
    'ir-benchmarks': {
        'tira-ir-starter': {
            'Index (tira-ir-starter-pyterrier)': {
                'msmarco-passage-trec-dl-2019-judged-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-01-07-22-09-56.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-01-07-22-09-56.zip'],
                    'run_id': '2023-01-07-22-09-56',
                },
                'msmarco-passage-trec-dl-2020-judged-20230107-training': {
                    # better caching: dl2020 and 2019 used the same corpus
                    'urls': ['https://zenodo.org/records/10743990/files/2023-01-07-22-09-56.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-01-07-22-09-56.zip'],
                    'run_id': '2023-01-07-22-09-56',

                    #'url': 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-09-19-37-45.zip',
                    #'run_id': '2023-02-09-19-37-45',
                },
                'antique-test-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-01-07-13-40-04.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-01-07-13-40-04.zip'],
                    'run_id': '2023-01-07-13-40-04',
                },
                'vaswani-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-01-07-19-01-50.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-01-07-19-01-50.zip'],
                    'run_id': '2023-01-07-19-01-50',
                },
                'cranfield-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-01-07-13-39-11.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-01-07-13-39-11.zip'],
                    'run_id': '2023-01-07-13-39-11',
                },
                'medline-2004-trec-genomics-2004-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-01-07-19-37-49.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-01-07-19-37-49.zip'],
                    'run_id': '2023-01-07-19-37-49',
                },
                'medline-2017-trec-pm-2017-20230211-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-02-11-20-52-47.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-11-20-52-47.zip'],
                    'run_id': '2023-02-11-20-52-47',
                },
                'cord19-fulltext-trec-covid-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-01-08-15-18-20.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-01-08-15-18-20.zip'],
                    'run_id': '2023-01-08-15-18-20',
                },
                'nfcorpus-test-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-02-09-15-46-37.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-09-15-46-37.zip'],
                    'run_id': '2023-02-09-15-46-37',
                },
                'argsme-touche-2020-task-1-20230209-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-02-09-17-50-22.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-09-17-50-22.zip'],
                    'run_id': '2023-02-09-17-50-22',
                },
                'argsme-touche-2021-task-1-20230209-training': {
                    # better caching: dl2020 and 2019 used the same corpus
                    'urls': ['https://zenodo.org/records/10743990/files/2023-02-09-17-50-22.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-09-17-50-22.zip'],
                    'run_id': '2023-02-09-17-50-22',
                    
                    #    'url': 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/.zip',
                    #    'run_id': '',
                },
                'medline-2017-trec-pm-2018-20230211-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-02-11-15-15-35.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-11-15-15-35.zip'],
                    'run_id': '2023-02-11-15-15-35',
                },
                'medline-2004-trec-genomics-2005-20230107-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-02-09-22-14-32.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-09-22-14-32.zip'],
                    'run_id': '2023-02-09-22-14-32',
                },
                'trec-tip-of-the-tongue-dev-20230607-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-11-10-23-23-59.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-11-10-23-23-59.zip'],
                    'run_id': '2023-11-10-23-23-59',
                },
                'longeval-short-july-20230513-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-11-10-23-22-59.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-11-10-23-22-59.zip'],
                    'run_id': '2023-11-10-23-22-59',
                },
                'longeval-heldout-20230513-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-11-10-23-21-55.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-11-10-23-21-55.zip'],
                    'run_id': '2023-11-10-23-21-55',
                },
                'longeval-long-september-20230513-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-11-10-21-09-17.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-11-10-21-09-17.zip'],
                    'run_id': '2023-11-10-21-09-17',
                },
                'longeval-train-20230513-training': {
                    'urls': ['https://zenodo.org/records/10743990/files/2023-11-11-06-49-15.zip?download=1', 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-11-11-06-49-15.zip'],
                    'run_id': '2023-11-11-06-49-15',
                },
            }
        }
    }
}

RUN_ID_TO_SYSTEM = {}
for task in STATIC_REDIRECTS.keys():
    for team in STATIC_REDIRECTS[task].keys():
        for system_name in STATIC_REDIRECTS[task][team].keys():
            system = STATIC_REDIRECTS[task][team][system_name]
            for config in system.values():
                RUN_ID_TO_SYSTEM[config['run_id']] = system_name

#{"ir-benchmarks": {"tira-ir-starter": {"Index (tira-ir-starter-pyterrier)": {"msmarco-passage-trec-dl-2019-judged-20230107-training": "2023-01-07-22-09-56", "msmarco-passage-trec-dl-2020-judged-20230107-training": "2023-02-09-19-37-45", "antique-test-20230107-training": "2023-01-07-13-40-04", "vaswani-20230107-training": "2023-01-07-19-01-50", "cranfield-20230107-training": "2023-01-07-13-39-11", "medline-2004-trec-genomics-2004-20230107-training": "2023-01-07-19-37-49", "medline-2017-trec-pm-2017-20230211-training": "2023-02-11-20-52-47", "cord19-fulltext-trec-covid-20230107-training": "2023-01-08-15-18-20", "nfcorpus-test-20230107-training": "2023-02-09-15-46-37", "argsme-touche-2020-task-1-20230209-training": "2023-02-09-17-50-22", "argsme-touche-2021-task-1-20230209-training": "2023-02-09-17-50-31", "medline-2017-trec-pm-2018-20230211-training": "2023-02-11-15-15-35", "medline-2004-trec-genomics-2005-20230107-training": "2023-02-09-22-14-32", "trec-tip-of-the-tongue-dev-20230607-training": "2023-11-10-23-23-59", "longeval-short-july-20230513-training": "2023-11-10-23-22-59", "longeval-heldout-20230513-training": "2023-11-10-23-21-55", "longeval-long-september-20230513-training": "2023-11-10-21-09-17", "longeval-train-20230513-training": "2023-11-11-06-49-15"}}}}

QUERY_PROCESSORS = {"ir-benchmarks": {"qpptk": {"all-predictors": {"trec-recent": {"dataset_group": "trec-recent", "md5": "1c25b7cce08acbb6deb0be767a5d6fa2", "run_ids": {"msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-27-21-30-47", "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-27-21-31-54", "trec-tip-of-the-tongue-dev-20230607-training": "2024-02-27-21-36-40"}}, "tiny-test-collections": {"dataset_group": "tiny-test-collections", "md5": "049143bd2cfc933f1f0b9d765444349b", "run_ids": {"antique-test-20230107-training": "2024-02-27-20-06-32", "vaswani-20230107-training": "2024-02-27-21-38-47", "cranfield-20230107-training": "2024-02-27-20-20-33", "nfcorpus-test-20230107-training": "2024-02-27-21-34-23"}}, "trec-medical": {"dataset_group": "trec-medical", "md5": "d1d967b33760c76ddd150b38004f13f1", "run_ids": {"medline-2004-trec-genomics-2004-20230107-training": "2024-02-27-21-21-07", "medline-2017-trec-pm-2017-20230211-training": "2024-02-27-21-27-05", "cord19-fulltext-trec-covid-20230107-training": "2024-02-27-20-18-28", "medline-2017-trec-pm-2018-20230211-training": "2024-02-27-21-28-47", "medline-2004-trec-genomics-2005-20230107-training": "2024-02-27-21-26-22"}}, "clef-labs": {"dataset_group": "clef-labs", "md5": "362f8efcdad0932917bd4a5d029668cc", "run_ids": {"argsme-touche-2020-task-1-20230209-training": "2024-02-27-20-09-14", "argsme-touche-2021-task-1-20230209-training": "2024-02-27-20-10-51", "longeval-short-july-20230513-training": "2024-02-27-21-15-17", "longeval-heldout-20230513-training": "2024-02-27-20-56-41", "longeval-long-september-20230513-training": "2024-02-27-21-10-42", "longeval-train-20230513-training": "2024-02-27-21-19-19"}}, "clueweb": {"dataset_group": "clueweb", "md5": "7f2d29c20638f9a901fe5ffb23772834", "run_ids": {"clueweb12-trec-misinfo-2019-20240214-training": "2024-02-27-20-13-20", "gov-trec-web-2002-20230209-training": "2024-02-27-20-26-06", "gov-trec-web-2003-20230209-training": "2024-02-27-20-27-09", "gov-trec-web-2004-20230209-training": "2024-02-27-20-29-21", "gov2-trec-tb-2004-20230209-training": "2024-02-27-20-30-58", "gov2-trec-tb-2005-20230209-training": "2024-02-27-20-33-27", "gov2-trec-tb-2006-20230209-training": "2024-02-27-20-37-51"}}, "trec-core": {"dataset_group": "trec-core", "md5": "9119381b68f4f405deb3feeed7ab300f", "run_ids": {"wapo-v2-trec-core-2018-20230107-training": "2024-02-27-21-40-17", "disks45-nocr-trec8-20230209-training": "2024-02-27-20-24-50", "disks45-nocr-trec7-20230209-training": "2024-02-27-20-23-24", "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-27-20-22-13"}}}}, "salamander": {"classify-comparative-queries": {"trec-recent": {"dataset_group": "trec-recent", "md5": "b5bcfbbabfab68ca7769f52dc74ff3d2", "run_ids": {"msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-25-16-58-54", "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-25-20-36-41"}}, "tiny-test-collections": {"dataset_group": "tiny-test-collections", "md5": "595b9fd7a6e84ae0f7711be00f7dee25", "run_ids": {"antique-test-20230107-training": "2024-02-25-15-17-55", "vaswani-20230107-training": "2024-02-25-20-40-09", "cranfield-20230107-training": "2024-02-25-15-45-40", "nfcorpus-test-20230107-training": "2024-02-25-20-37-46"}}, "trec-medical": {"dataset_group": "trec-medical", "md5": "99fad757c51ec589fad627c509db1375", "run_ids": {"medline-2004-trec-genomics-2004-20230107-training": "2024-02-25-16-09-36", "medline-2017-trec-pm-2017-20230211-training": "2024-02-25-16-12-21", "cord19-fulltext-trec-covid-20230107-training": "2024-02-25-15-44-30", "medline-2017-trec-pm-2018-20230211-training": "2024-02-25-16-57-26", "medline-2004-trec-genomics-2005-20230107-training": "2024-02-25-16-11-16"}}, "clef-labs": {"dataset_group": "clef-labs", "md5": "cdc91e48f0e0794aed6d3564a3184f23", "run_ids": {"argsme-touche-2020-task-1-20230209-training": "2024-02-25-15-19-08", "argsme-touche-2021-task-1-20230209-training": "2024-02-25-15-20-13", "longeval-short-july-20230513-training": "2024-02-25-16-04-17", "longeval-heldout-20230513-training": "2024-02-25-16-01-03", "longeval-long-september-20230513-training": "2024-02-25-16-03-12", "longeval-train-20230513-training": "2024-02-25-16-06-29"}}, "clueweb": {"dataset_group": "clueweb", "md5": "0e213ab92e2d6d769673b091dba167b0", "run_ids": {"clueweb09-en-trec-web-2009-20230107-training": "2024-02-25-15-21-18", "clueweb09-en-trec-web-2010-20230107-training": "2024-02-25-15-24-17", "clueweb09-en-trec-web-2011-20230107-training": "2024-02-25-15-25-22", "clueweb09-en-trec-web-2012-20230107-training": "2024-02-25-15-26-28", "clueweb12-touche-2020-task-2-20230209-training": "2024-02-25-15-27-38", "clueweb12-touche-2021-task-2-20230209-training": "2024-02-25-15-28-44", "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-25-15-29-50", "clueweb12-trec-web-2013-20230107-training": "2024-02-25-15-30-55", "clueweb12-trec-web-2014-20230107-training": "2024-02-25-15-32-03", "gov-trec-web-2002-20230209-training": "2024-02-25-15-51-54", "gov-trec-web-2003-20230209-training": "2024-02-25-15-53-06", "gov-trec-web-2004-20230209-training": "2024-02-25-15-54-30", "gov2-trec-tb-2004-20230209-training": "2024-02-25-15-55-44", "gov2-trec-tb-2005-20230209-training": "2024-02-25-15-58-17", "gov2-trec-tb-2006-20230209-training": "2024-02-25-15-59-47"}}, "trec-core": {"dataset_group": "trec-core", "md5": "49e5f5fd0ea51f8fba703a80602cbc49", "run_ids": {"wapo-v2-trec-core-2018-20230107-training": "2024-02-25-20-41-24", "disks45-nocr-trec8-20230209-training": "2024-02-25-15-51-07", "disks45-nocr-trec7-20230209-training": "2024-02-25-15-49-58", "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-25-15-48-48"}}}}}}

QUERY_PROCESSORS_PREFIX = {"ir-benchmarks": {
    "qpptk": {
        "all-predictors": 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/qpptk-all-predictors'
    }, "salamander": {
        "classify-comparative-queries": 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/salamander-classify-comparative-queries'
    }
}}


for task in QUERY_PROCESSORS.keys():
    for team in QUERY_PROCESSORS[task].keys():
        if team not in STATIC_REDIRECTS[task]:
            STATIC_REDIRECTS[task][team] = {}

        for system_name in QUERY_PROCESSORS[task][team].keys():
            system = QUERY_PROCESSORS[task][team][system_name]
            if system_name not in STATIC_REDIRECTS[task][team]:
                STATIC_REDIRECTS[task][team][system_name] = {}
            for dataset_group in system.keys():
                for dataset_id, run_id in sorted(list(system[dataset_group]['run_ids'].items())):
                    RUN_ID_TO_SYSTEM[run_id] = system_name
                    STATIC_REDIRECTS[task][team][system_name][dataset_id] = {'run_id': run_id, 'urls': [QUERY_PROCESSORS_PREFIX[task][team][system_name] + f'-{dataset_group}.zip']}

MIRROR_URLS = {}

for task in STATIC_REDIRECTS.keys():
    for team in STATIC_REDIRECTS[task].keys():
        for system_name in STATIC_REDIRECTS[task][team].keys():
            system = STATIC_REDIRECTS[task][team][system_name]
            for dataset_id in system.keys():
                urls = system[dataset_id].get('urls')
                if urls and len(urls) > 0:
                    for url in urls:
                        MIRROR_URLS[url] = [i for i in urls if i != url]

def mirror_url(url):
    mirror_urls = MIRROR_URLS.get(url)
    if mirror_urls and len(mirror_urls) > 0:
        print(f'Switch to mirror {mirror_urls[0]} as due to outage of {url}')
        return mirror_urls[0]
    return url

# do some semi fast tests with:
#    python3 -c 'from tira.rest_api_client import Client; tira = Client(); print(tira.get_run_output("ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)", "argsme-touche-2020-task-1-20230209-training"))'

def redirects(approach=None, dataset=None, url=None):
    default_ret = {'urls': [url]}
    if url is not None:
        if '/task/' in url and '/user/' in url and '/dataset/' in url and '/download/' in url and '.zip' in url:
            #/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip
            ret = url.split('/task/')[1]
            ret = ret.split('/')
            task, team, dataset, run_id = ret[0], ret[2], ret[4], ret[6].replace('.zip', '')
            system = RUN_ID_TO_SYSTEM.get(run_id, None)
        else:
            return default_ret

    else:
        task, team, system = approach.split('/')

    return STATIC_REDIRECTS.get(task, {}).get(team, {}).get(system, {}).get(dataset, default_ret)
