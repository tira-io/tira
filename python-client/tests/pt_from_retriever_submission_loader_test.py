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

def retrieval_submission(queries):
    queries = pd.DataFrame([{'qid': str(i)} for i in queries])
    tira = Client('tests/resources/')
    retriever =  tira.pt.from_retriever_submission('ir-benchmarks/tira-ir-starters/retriever', dataset='d1')
    
    ret = retriever(queries)
    return [{'qid': i['qid'], 'docno': i['docno'], 'score': i['score']} for _, i in ret.iterrows()]
