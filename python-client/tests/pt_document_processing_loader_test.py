from tira.local_client import Client

import pandas as pd


def test_for_loading_keyphrase_extraction_for_multiple_documents():
    expected = {
        'FT921-3964': ["increased economic aid","king hussein","increase aid","president george bush","tariq aziz iraq's deputy prime minister"],
        'LA061489-0137': ["public appearances gorbachev","crowds","government ministries gorbachev","place gorbachev","west german well-wishers"]}
    
    actual = keyphrase_extraction(['FT921-3964', 'LA061489-0137'])
    
    assert len(actual) == 2
    assert actual['FT921-3964'] == expected['FT921-3964']
    assert actual['LA061489-0137'] == expected['LA061489-0137']


def test_for_loading_keyphrase_extraction_for_single_documents():
    expected = {"LA120390-0047": ["even friendly technology takeovers","largest technology takeover","computer industry takeover","statement sunday","attempts"]}
    
    actual = keyphrase_extraction(["LA120390-0047"])
    
    assert len(actual) == 1
    assert actual["LA120390-0047"] == expected["LA120390-0047"]


def test_pyterrier_can_be_loaded():
    from tira.third_party_integrations import ensure_pyterrier_is_loaded
    ensure_pyterrier_is_loaded()


def keyphrase_extraction(docs):
    queries = pd.DataFrame([{'docno': str(i)} for i in docs])
    tira = Client('tests/resources/')
    query_segmentation =  tira.pt.transform_documents('ir-benchmarks/webis-keyphrase-extraction/BCExtractorFO', dataset='d1')
    
    ret = query_segmentation(queries)
    return {i['docno']: i['keyphrases'] for _, i in ret.iterrows()}

