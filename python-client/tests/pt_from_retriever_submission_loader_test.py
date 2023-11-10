from tira.local_client import Client

import pandas as pd

def test_for_multiple_queries():
    expected = [
        {'qid': '1', 'docno': 'doc-1', 'score':10},
        {'qid': '1', 'docno': 'doc-2', 'score':9},
        {'qid': '3', 'docno': 'doc-3', 'score': 1},
    ]
    
    actual = retrieval_submission([1, 3])

    assert len(actual) == 3
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]
    assert actual[2] == expected[2]

def test_for_single_query_no_1():
    expected = [
        {'qid': '1', 'docno': 'doc-1', 'score':10},
        {'qid': '1', 'docno': 'doc-2', 'score':9},
    ]
    
    actual = retrieval_submission([1])

    assert len(actual) == 2
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]

def test_for_single_query_no_3():
    expected = [
        {'qid': '3', 'docno': 'doc-3', 'score': 1},
    ]
    
    actual = retrieval_submission([3])

    assert len(actual) == 1
    assert actual[0] == expected[0]

def test_retrieval_submission_from_rest_api():
    from tira.rest_api_client import Client
    from tira.third_party_integrations import ensure_pyterrier_is_loaded
    import pyterrier as pt
    ensure_pyterrier_is_loaded()
    tira = Client()

    q = tira.pt.from_submission('ir-benchmarks/tira-ir-starter/BM25 Re-Rank (tira-ir-starter-pyterrier)', pt.get_dataset("irds:disks45/nocr/trec-robust-2004"))
    assert len(q(pd.DataFrame([{'qid': '306'}]))) == 1000
    assert q(pd.DataFrame([{'qid': '306'}])).iloc[0].to_dict()['docno'] == 'LA021790-0114'
    assert q(pd.DataFrame([{'qid': '306'}])).iloc[0].to_dict()['qid'] == '306'
    assert q(pd.DataFrame([{'qid': '306'}])).iloc[999].to_dict()['docno'] == 'FBIS4-47956'
    assert q(pd.DataFrame([{'qid': '306'}])).iloc[999].to_dict()['qid'] == '306'

def retrieval_submission(queries):
    queries = pd.DataFrame([{'qid': str(i)} for i in queries])
    tira = Client('tests/resources/')
    retriever =  tira.pt.from_retriever_submission('ir-benchmarks/tira-ir-starters/retriever', dataset='d1')
    
    ret = retriever(queries)
    return [{'qid': i['qid'], 'docno': i['docno'], 'score': i['score']} for _, i in ret.iterrows()]
