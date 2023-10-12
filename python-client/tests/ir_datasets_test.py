from tira.third_party_integrations import register_rerank_data_to_ir_datasets, load_ir_datasets, ensure_pyterrier_is_loaded
import ir_datasets
import os


register_rerank_data_to_ir_datasets('tests/sample-tirex-rerank-data', 'tirex-sample-dataset', 'vaswani')

    
def test_for_existing_document():
    dataset = ir_datasets.load('tirex-sample-dataset')

    expected_text = "microwave spectroscopy  includes chapters on spectroscope technique\nand design on measurements on gases liquids and solids on nuclear\nproperties on molecular structure and on further possible applications\nof microwaves\n"

    assert expected_text == dataset.docs_store().get('8172').text
    assert '8172' == dataset.docs_store().get('8172').doc_id


def test_for_non_existing_document():
    dataset = ir_datasets.load('tirex-sample-dataset')

    assert dataset.docs_store().get('does-not-exist') is None


def test_for_queries():
    dataset = ir_datasets.load('tirex-sample-dataset')

    assert len(list(dataset.queries_iter())) == 1
    assert 'MEASUREMENT OF DIELECTRIC CONSTANT OF LIQUIDS BY THE USE OF MICROWAVE TECHNIQUES\n' == list(dataset.queries_iter())[0].text


def test_for_scoreddocs():
    dataset = ir_datasets.load('tirex-sample-dataset')
    print(list(dataset.scoreddocs))
    assert len(list(dataset.scoreddocs)) == 10
    assert '8172' == list(dataset.scoreddocs)[0].doc_id
    assert '1' == list(dataset.scoreddocs)[0].query_id

def test_loading_raw_ir_datasets():
    ir_datasets = load_ir_datasets()
    dataset = ir_datasets.load('cranfield')
    queries = {i.query_id: i.text for i in dataset.queries_iter()}

    assert len(list(dataset.queries_iter())) == 225
    assert queries['269'] == 'has a criterion been established for determining the axial compressor\nchoking line .'
    

def test_loading_queries_from_ir_datasets_from_custom_directory():
    os.environ['TIRA_INPUT_DIRECTORY'] = 'tests/resources/sample-input-full-rank'
    ir_datasets = load_ir_datasets()
    del os.environ['TIRA_INPUT_DIRECTORY']
    dataset = ir_datasets.load('does-not-exist-and-is-not-used')
    queries = {i.query_id: i.text for i in dataset.queries_iter()}

    assert len(list(dataset.queries_iter())) == 2
    assert queries['1'] == 'fox jumps above animal'

def test_loading_documents_from_ir_datasets_from_custom_directory():
    os.environ['TIRA_INPUT_DIRECTORY'] = 'tests/resources/sample-input-full-rank'
    ir_datasets = load_ir_datasets()
    del os.environ['TIRA_INPUT_DIRECTORY']
    dataset = ir_datasets.load('does-not-exist-and-is-not-used')
    docs = {i.doc_id: i.text for i in dataset.docs_iter()}

    assert len(list(dataset.docs_iter())) == 5
    assert docs['pangram-02'] == 'Quick fox jumps nightly above wizard.'


def test_loading_docs_store_from_ir_datasets_from_custom_directory():
    os.environ['TIRA_INPUT_DIRECTORY'] = 'tests/resources/sample-input-full-rank'
    ir_datasets = load_ir_datasets()
    del os.environ['TIRA_INPUT_DIRECTORY']
    dataset = ir_datasets.load('does-not-exist-and-is-not-used')

    assert dataset.docs_store()['pangram-03'].text == 'The jay, pig, fox, zebra and my wolves quack!'

def test_no_patching_for_pyterrier_datasets():
    ensure_pyterrier_is_loaded()
    import pyterrier as pt
    dataset = pt.get_dataset('irds:cranfield')
    queries = {i['qid']: i['query'] for _, i in dataset.get_topics().iterrows()}

    assert len(dataset.get_topics()) == 225
    assert queries['269'] == 'has a criterion been established for determining the axial compressor choking line'

def test_patching_for_pyterrier_datasets():
    os.environ['TIRA_INPUT_DIRECTORY'] = 'tests/resources/sample-input-full-rank'
    import ir_datasets
    l = ir_datasets.load
    ensure_pyterrier_is_loaded()
    import pyterrier as pt
    dataset = pt.get_dataset('irds:does-not-exist-and-is-not-used')
    ir_datasets.load = l
    del os.environ['TIRA_INPUT_DIRECTORY']

    queries = {i['qid']: i['query'] for _, i in dataset.get_topics().iterrows()}

    assert len(list(dataset.get_topics())) == 2
    assert queries['1'] == 'fox jumps above animal'

def test_loading_ir_dataset_via_rest_api_from_tira():
    from tira.third_party_integrations import ir_datasets
    dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
    
    assert dataset.has_docs(), "dataset has no documents"
    assert dataset.has_queries(), "dataset has no queries"
    assert dataset.has_qrels(), "dataset has no qrels"
    
def test_loading_qrels_via_rest_api_from_tira():
    from tira.third_party_integrations import ir_datasets
    dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
    
    assert len([i for i in dataset.qrels_iter()]) == 2635
    assert '''TrecQrel(query_id='1', doc_id='2005.ipm_journal-ir0anthology0volumeA41A1.7', relevance=1, iteration='0')''' == str([i for i in dataset.qrels_iter()][0])

def test_loading_docs_via_rest_api_from_tira():
    from tira.third_party_integrations import ir_datasets
    dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
    
    assert len([i for i in dataset.docs_iter()]) == 53673
    docsstore = dataset.docs_store()

    assert docsstore.get('2005.ipm_journal-ir0anthology0volumeA41A1.7').text.startswith('A probabilistic model for stemmer generation AbstractIn this paper')


def test_loading_queries_via_rest_api_from_tira():
    from tira.third_party_integrations import ir_datasets
    dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
    
    assert 68 == len(list(dataset.queries_iter()))
    assert '''GenericQuery(query_id='1', text='retrieval system improving effectiveness')''' == str(list(dataset.queries_iter())[0])
    
