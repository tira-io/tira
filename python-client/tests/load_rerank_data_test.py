from tira.third_party_integrations import load_rerank_data

def test_loading_rerank_data_from_local_file():
    re_rank_data = load_rerank_data(default='tests/resources/re-ranking-outputs/')
    
    assert 3 == len(re_rank_data)
    assert {"qid": "1", "query": "query 1", "docno": "doc-1", "text": "Text of doc-1", "rank": 1, "score": 10} == re_rank_data.iloc[0].to_dict()
    assert {"qid": "3", "query": "query 3", "docno": "doc-3", "text": "Text of doc-3", "rank": 1, "score": 1} == re_rank_data.iloc[2].to_dict()

def test_loading_rerank_data_from_remote_file():
    re_rank_data = load_rerank_data(default='workshop-on-open-web-search/re-ranking-20231027-training')
    
    assert 6 == len(re_rank_data)
    assert {"qid": "2", "query": "how to exit vim?", "docno": "doc-1", "text": "Press ESC key, then the : (colon), and type the wq command after the colon and hit the Enter key to save and leave Vim.", "rank": 1, "score": 10} == re_rank_data.iloc[2].to_dict()


