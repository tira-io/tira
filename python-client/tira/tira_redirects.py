STATIC_REDIRECTS = {
    'ir-benchmarks': {
        'tira-ir-starter': {
            'Index (tira-ir-starter-pyterrier)': {
                'msmarco-passage-trec-dl-2019-judged-20230107-training': 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/msmarco-passage-trec-dl-2019.zip',
                'msmarco-passage-trec-dl-2020-judged-20230107-training': 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/msmarco-passage-trec-dl-2019.zip',
                'antique-test-20230107-training': 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/pyterrier-indexes/antique-test-20230107-training.zip',
                #'vaswani-20230107-training': 'todo',
                #'antique-test-20230107-training': 'todo',
                #'cranfield-20230107-training': 'todo',
                #'medline-2004-trec-genomics-2004-20230107-training': 'todo',
                #'medline-2017-trec-pm-2017-20230211-training': 'todo',
                #'cord19-fulltext-trec-covid-20230107-training': 'todo',
                #'nfcorpus-test-20230107-training': 'todo',
                #'argsme-touche-2020-task-1-20230209-training': 'todo',
                #'argsme-touche-2021-task-1-20230209-training': 'todo',
                #'medline-2017-trec-pm-2018-20230211-training': 'todo',
                #'medline-2004-trec-genomics-2005-20230107-training': 'todo',

                # second tranche, keep this for longer in files.webis.de as it is not part of original TIREx
                #'trec-tip-of-the-tongue-dev-20230607-training': 'todo',
                #'longeval-short-july-20230513-training': 'todo',
                #'longeval-heldout-20230513-training': 'todo',
                #'longeval-long-september-20230513-training': 'todo',

            }
        }
    }
}
def redirects(approach=None, dataset=None, url=None):
    if url is not None:
        if '/task/' in url and '/user/' in url and '/dataset/' in url and '/download/' in url and '.zip' in url:
            #/task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip
            ret = url.split('/task/')[1]
            ret = ret.split('/')
            task, team, dataset, system = ret[0], ret[2], ret[4], ret[6].replace('.zip', '')
        else:
            return url
    else:
        task, team, system = approach.split('/')
    return STATIC_REDIRECTS.get(task, {}).get(team, {}).get(system, {}).get(dataset, url)