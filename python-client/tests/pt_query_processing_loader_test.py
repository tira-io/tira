from tira.local_client import Client

import pandas as pd


def test_for_loading_query_segmentations_for_multiple_queries():
    expected = {'350': ["health and","computer terminals"], '353': ["antarctica","exploration"]}
    
    actual = query_segmentation([350, 353])
    
    assert len(actual) == 2
    assert actual['350'] == expected['350']
    assert actual['353'] == expected['353']


def test_for_loading_query_segmentations_for_single_query():
    expected = {'351': ["falkland","petroleum exploration"]}
    
    actual = query_segmentation([351])
    
    assert len(actual) == 1
    assert actual['351'] == expected['351']


def test_pyterrier_can_be_loaded():
    from tira.third_party_integrations import ensure_pyterrier_is_loaded
    ensure_pyterrier_is_loaded()


def query_segmentation(queries):
    queries = pd.DataFrame([{'qid': str(i)} for i in queries])
    tira = Client('tests/resources/')
    query_segmentation =  tira.pt.transform_queries('ir-benchmarks/webis-query-segmentation/wt-snp-baseline', dataset='d1')
    
    ret = query_segmentation(queries)
    return {i['qid']: i['segmentation'] for _, i in ret.iterrows()}

