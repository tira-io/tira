

STATIC_REDIRECTS = {
    'ir-benchmarks': {
        'tira-ir-starter': {
            'Index (tira-ir-starter-pyterrier)': {
                'msmarco-passage-trec-dl-2019-judged-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-01-07-22-09-56.zip?download=1',
                    'run_id': '2023-01-07-22-09-56',
                },
                'msmarco-passage-trec-dl-2020-judged-20230107-training': {
                    # better caching: dl2020 and 2019 used the same corpus
                    'url': 'https://zenodo.org/records/10743990/files/2023-01-07-22-09-56.zip?download=1',
                    'run_id': '2023-01-07-22-09-56',

                    #'url': 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/2023-02-09-19-37-45.zip',
                    #'run_id': '2023-02-09-19-37-45',
                },
                'antique-test-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-01-07-13-40-04.zip?download=1',
                    'run_id': '2023-01-07-13-40-04',
                },
                'vaswani-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-01-07-19-01-50.zip?download=1',
                    'run_id': '2023-01-07-19-01-50',
                },
                'cranfield-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-01-07-13-39-11.zip?download=1',
                    'run_id': '2023-01-07-13-39-11',
                },
                'medline-2004-trec-genomics-2004-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-01-07-19-37-49.zip?download=1',
                    'run_id': '2023-01-07-19-37-49',
                },
                'medline-2017-trec-pm-2017-20230211-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-02-11-20-52-47.zip?download=1',
                    'run_id': '2023-02-11-20-52-47',
                },
                'cord19-fulltext-trec-covid-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-01-08-15-18-20.zip?download=1',
                    'run_id': '2023-01-08-15-18-20',
                },
                'nfcorpus-test-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-02-09-15-46-37.zip?download=1',
                    'run_id': '2023-02-09-15-46-37',
                },
                'argsme-touche-2020-task-1-20230209-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-02-09-17-50-22.zip?download=1',
                    'run_id': '2023-02-09-17-50-22',
                },
                'argsme-touche-2021-task-1-20230209-training': {
                    # better caching: dl2020 and 2019 used the same corpus
                    'url': 'https://zenodo.org/records/10743990/files/2023-02-09-17-50-22.zip?download=1',
                    'run_id': '2023-02-09-17-50-22',
                    
                    #    'url': 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/.zip',
                    #    'run_id': '',
                },
                'medline-2017-trec-pm-2018-20230211-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-02-11-15-15-35.zip?download=1',
                    'run_id': '2023-02-11-15-15-35',
                },
                'medline-2004-trec-genomics-2005-20230107-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-02-09-22-14-32.zip?download=1',
                    'run_id': '2023-02-09-22-14-32',
                },
                'trec-tip-of-the-tongue-dev-20230607-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-11-10-23-23-59.zip?download=1',
                    'run_id': '2023-11-10-23-23-59',
                },
                'longeval-short-july-20230513-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-11-10-23-22-59.zip?download=1',
                    'run_id': '2023-11-10-23-22-59',
                },
                'longeval-heldout-20230513-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-11-10-23-21-55.zip?download=1',
                    'run_id': '2023-11-10-23-21-55',
                },
                'longeval-long-september-20230513-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-11-10-21-09-17.zip?download=1',
                    'run_id': '2023-11-10-21-09-17',
                },
                'longeval-train-20230513-training': {
                    'url': 'https://zenodo.org/records/10743990/files/2023-11-11-06-49-15.zip?download=1',
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


def redirects(approach=None, dataset=None, url=None):
    default_ret = {'url': url}
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
