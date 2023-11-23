from tira.third_party_integrations import register_rerank_data_to_ir_datasets, load_ir_datasets, ensure_pyterrier_is_loaded
import ir_datasets
import os
import unittest


# TODO: this file still uses "unclean" assertions and should be converted to use unittest assertions

class TestIRDatasets(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        register_rerank_data_to_ir_datasets('tests/sample-tirex-rerank-data', 'tirex-sample-dataset', 'vaswani')

    def test_for_existing_document_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        dataset = ir_datasets.load('tirex-sample-dataset')

        expected_text = "microwave spectroscopy  includes chapters on spectroscope technique\nand design on measurements on gases liquids and solids on nuclear\nproperties on molecular structure and on further possible applications\nof microwaves\n"

        assert expected_text == dataset.docs_store().get('8172').text
        assert '8172' == dataset.docs_store().get('8172').doc_id


    def test_for_existing_document_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        dataset = ir_datasets.load('tirex-sample-dataset')

        expected_text = "microwave spectroscopy  includes chapters on spectroscope technique\nand design on measurements on gases liquids and solids on nuclear\nproperties on molecular structure and on further possible applications\nof microwaves\n"

        assert expected_text == dataset.docs_store().get('8172').text
        assert '8172' == dataset.docs_store().get('8172').doc_id


    def test_for_non_existing_document_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        dataset = ir_datasets.load('tirex-sample-dataset')

        assert dataset.docs_store().get('does-not-exist') is None


    def test_for_non_existing_document_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        dataset = ir_datasets.load('tirex-sample-dataset')

        assert dataset.docs_store().get('does-not-exist') is None


    def test_for_queries_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        dataset = ir_datasets.load('tirex-sample-dataset')

        assert len(list(dataset.queries_iter())) == 1
        assert 'MEASUREMENT OF DIELECTRIC CONSTANT OF LIQUIDS BY THE USE OF MICROWAVE TECHNIQUES\n' == list(dataset.queries_iter())[0].text


    def test_for_queries_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        dataset = ir_datasets.load('tirex-sample-dataset')

        assert len(list(dataset.queries_iter())) == 1
        assert 'MEASUREMENT OF DIELECTRIC CONSTANT OF LIQUIDS BY THE USE OF MICROWAVE TECHNIQUES\n' == list(dataset.queries_iter())[0].text


    def test_for_scoreddocs_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        dataset = ir_datasets.load('tirex-sample-dataset')
        print(list(dataset.scoreddocs))
        assert len(list(dataset.scoreddocs)) == 10
        assert '8172' == list(dataset.scoreddocs)[0].doc_id
        assert '1' == list(dataset.scoreddocs)[0].query_id


    def test_for_scoreddocs_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        dataset = ir_datasets.load('tirex-sample-dataset')
        print(list(dataset.scoreddocs))
        assert len(list(dataset.scoreddocs)) == 10
        assert '8172' == list(dataset.scoreddocs)[0].doc_id
        assert '1' == list(dataset.scoreddocs)[0].query_id


    def test_for_scoreddocs_within_tira(self):
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/re-ranking-outputs'
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        dataset = ir_datasets.load('msmarco-passage/eval/small')
        print(list(dataset.scoreddocs))
        del os.environ['TIRA_INPUT_DATASET']
        assert len(list(dataset.scoreddocs)) == 3
        assert 'doc-1' == list(dataset.scoreddocs)[0].doc_id
        assert '1' == list(dataset.scoreddocs)[0].query_id
        assert 10 == list(dataset.scoreddocs)[0].score
        register_rerank_data_to_ir_datasets('tests/sample-tirex-rerank-data', 'tirex-sample-dataset', None)


    def test_loading_raw_ir_datasets_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        ir_datasets = load_ir_datasets()
        dataset = ir_datasets.load('cranfield')
        queries = {i.query_id: i.text for i in dataset.queries_iter()}

        assert len(list(dataset.queries_iter())) == 225
        assert queries['269'] == 'has a criterion been established for determining the axial compressor\nchoking line .'


    def test_loading_raw_ir_datasets_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        ir_datasets = load_ir_datasets()
        dataset = ir_datasets.load('cranfield')
        queries = {i.query_id: i.text for i in dataset.queries_iter()}

        assert len(list(dataset.queries_iter())) == 225
        assert queries['269'] == 'has a criterion been established for determining the axial compressor\nchoking line .'


    def test_loading_queries_from_ir_datasets_from_custom_directory_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')
        queries = {i.query_id: i.text for i in dataset.queries_iter()}

        assert len(list(dataset.queries_iter())) == 2
        assert queries['1'] == 'fox jumps above animal'


    def test_loading_queries_from_ir_datasets_from_custom_directory_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')
        queries = {i.query_id: i.text for i in dataset.queries_iter()}

        assert len(list(dataset.queries_iter())) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_loading_queries_from_ir_datasets_from_custom_directory_2_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank-without-documents'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')
        queries = {i.query_id: i.text for i in dataset.queries_iter()}

        assert len(list(dataset.queries_iter())) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_loading_queries_from_ir_datasets_from_custom_directory_2_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank-without-documents'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')
        queries = {i.query_id: i.text for i in dataset.queries_iter()}

        assert len(list(dataset.queries_iter())) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_loading_documents_from_ir_datasets_from_custom_directory_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')
        docs = {i.doc_id: i.text for i in dataset.docs_iter()}

        assert len(list(dataset.docs_iter())) == 5
        assert docs['pangram-02'] == 'Quick fox jumps nightly above wizard.'

    def test_loading_documents_from_ir_datasets_from_custom_directory_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')
        docs = {i.doc_id: i.text for i in dataset.docs_iter()}

        assert len(list(dataset.docs_iter())) == 5
        assert docs['pangram-02'] == 'Quick fox jumps nightly above wizard.'

    def test_loading_docs_store_from_ir_datasets_from_custom_directory_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')

        assert dataset.docs_store()['pangram-03'].text == 'The jay, pig, fox, zebra and my wolves quack!'

    def test_loading_docs_store_from_ir_datasets_from_custom_directory_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        ir_datasets = load_ir_datasets()
        del os.environ['TIRA_INPUT_DATASET']
        dataset = ir_datasets.load('does-not-exist-and-is-not-used')

        assert dataset.docs_store()['pangram-03'].text == 'The jay, pig, fox, zebra and my wolves quack!'

    def test_no_patching_for_pyterrier_datasets_01(self):
        ensure_pyterrier_is_loaded()
        import pyterrier as pt
        dataset = pt.get_dataset('irds:cranfield')
        queries = {i['qid']: i['query'] for _, i in dataset.get_topics().iterrows()}

        assert len(dataset.get_topics()) == 225
        assert queries['269'] == 'has a criterion been established for determining the axial compressor choking line'

    def test_no_patching_for_pyterrier_datasets_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        import pyterrier as pt
        dataset = pt.get_dataset('irds:cranfield')
        queries = {i['qid']: i['query'] for _, i in dataset.get_topics().iterrows()}

        assert len(dataset.get_topics()) == 225
        assert queries['269'] == 'has a criterion been established for determining the axial compressor choking line'

    def test_patching_for_pyterrier_datasets_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        import ir_datasets
        l = ir_datasets.load
        ensure_pyterrier_is_loaded()
        import pyterrier as pt
        dataset = pt.get_dataset('irds:does-not-exist-and-is-not-used')
        ir_datasets.load = l
        del os.environ['TIRA_INPUT_DATASET']

        queries = {i['qid']: i['query'] for _, i in dataset.get_topics().iterrows()}

        assert len(list(dataset.get_topics('title'))) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_patching_for_pyterrier_datasets_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        import ir_datasets
        l = ir_datasets.load
        ensure_pyterrier_is_loaded()
        import pyterrier as pt
        dataset = pt.get_dataset('irds:does-not-exist-and-is-not-used')
        ir_datasets.load = l
        del os.environ['TIRA_INPUT_DATASET']

        queries = {i['qid']: i['query'] for _, i in dataset.get_topics().iterrows()}

        assert len(list(dataset.get_topics('title'))) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_patching_for_pyterrier_datasets_for_text_queries_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        import ir_datasets
        l = ir_datasets.load
        ensure_pyterrier_is_loaded()
        import pyterrier as pt
        dataset = pt.get_dataset('irds:does-not-exist-and-is-not-used')
        ir_datasets.load = l
        del os.environ['TIRA_INPUT_DATASET']

        queries = {i['qid']: i['query'] for _, i in dataset.get_topics('text').iterrows()}

        assert len(list(dataset.get_topics('text'))) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_patching_for_pyterrier_datasets_for_text_queries_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        import ir_datasets
        l = ir_datasets.load
        ensure_pyterrier_is_loaded()
        import pyterrier as pt
        dataset = pt.get_dataset('irds:does-not-exist-and-is-not-used')
        ir_datasets.load = l
        del os.environ['TIRA_INPUT_DATASET']

        queries = {i['qid']: i['query'] for _, i in dataset.get_topics('text').iterrows()}

        assert len(list(dataset.get_topics('text'))) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_patching_for_pyterrier_datasets_for_title_queries_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        import ir_datasets
        l = ir_datasets.load
        ensure_pyterrier_is_loaded()
        import pyterrier as pt
        dataset = pt.get_dataset('irds:does-not-exist-and-is-not-used')
        ir_datasets.load = l
        del os.environ['TIRA_INPUT_DATASET']

        queries = {i['qid']: i['query'] for _, i in dataset.get_topics('title').iterrows()}

        assert len(list(dataset.get_topics('title'))) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_patching_for_pyterrier_datasets_for_title_queries_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/sample-input-full-rank'
        import ir_datasets
        l = ir_datasets.load
        ensure_pyterrier_is_loaded()
        import pyterrier as pt
        dataset = pt.get_dataset('irds:does-not-exist-and-is-not-used')
        ir_datasets.load = l
        del os.environ['TIRA_INPUT_DATASET']

        queries = {i['qid']: i['query'] for _, i in dataset.get_topics('title').iterrows()}

        assert len(list(dataset.get_topics('title'))) == 2
        assert queries['1'] == 'fox jumps above animal'

    def test_loading_ir_dataset_via_rest_api_from_tira_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert dataset.has_docs(), "dataset has no documents"
        assert dataset.has_queries(), "dataset has no queries"
        assert dataset.has_qrels(), "dataset has no qrels"

    def test_loading_ir_dataset_via_rest_api_from_tira_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert dataset.has_docs(), "dataset has no documents"
        assert dataset.has_queries(), "dataset has no queries"
        assert dataset.has_qrels(), "dataset has no qrels"
        
    def test_loading_qrels_via_rest_api_from_tira_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert len([i for i in dataset.qrels_iter()]) == 2635
        assert '''TrecQrel(query_id='1', doc_id='2005.ipm_journal-ir0anthology0volumeA41A1.7', relevance=1, iteration='0')''' == str([i for i in dataset.qrels_iter()][0])

    def test_loading_qrels_via_rest_api_from_tira_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert len([i for i in dataset.qrels_iter()]) == 2635
        assert '''TrecQrel(query_id='1', doc_id='2005.ipm_journal-ir0anthology0volumeA41A1.7', relevance=1, iteration='0')''' == str([i for i in dataset.qrels_iter()][0])

    def test_loading_docs_via_rest_api_from_tira_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert len([i for i in dataset.docs_iter()]) == 53673
        docsstore = dataset.docs_store()

        assert docsstore.get('2005.ipm_journal-ir0anthology0volumeA41A1.7').text.startswith('A probabilistic model for stemmer generation AbstractIn this paper')

    def test_loading_docs_via_rest_api_from_tira_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert len([i for i in dataset.docs_iter()]) == 53673
        docsstore = dataset.docs_store()

        assert docsstore.get('2005.ipm_journal-ir0anthology0volumeA41A1.7').text.startswith('A probabilistic model for stemmer generation AbstractIn this paper')

    def test_loading_topics_via_rest_api_from_tira_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.topics_file('ir-lab-jena-leipzig-wise-2023/training-20231104-training')
        
        assert dataset.endswith('/training-20231104-training/truth-data/queries.xml')

    def test_loading_topics_via_rest_api_from_tira_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.topics_file('ir-lab-jena-leipzig-wise-2023/training-20231104-training')
        
        assert dataset.endswith('/training-20231104-training/truth-data/queries.xml')

    def test_loading_topics_via_rest_api_from_rerank_dataset_from_tira_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        os.environ['TIRA_INPUT_DATASET'] = 'tests/resources/re-ranking-outputs'
        ir_datasets = load_ir_datasets()
        dataset = ir_datasets.load('workshop-on-open-web-search/re-ranking-20231027-training')
        del os.environ['TIRA_INPUT_DATASET']

        assert len([i for i in dataset.queries_iter()]) == 2
        assert len([i for i in dataset.docs_iter()]) == 3

    def test_loading_queries_via_rest_api_from_tira_01(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=False)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert 68 == len(list(dataset.queries_iter()))
        print(str(list(dataset.queries_iter())[0]))
        assert '''TirexQuery(query_id='1', text='retrieval system improving effectiveness', title='retrieval system improving effectiveness', query='retrieval system improving effectiveness', description='What papers focus on improving the effectiveness of a retrieval system?', narrative='Relevant papers include research on what makes a retrieval system effective and what improves the effectiveness of a retrieval system. Papers that focus on improving something else or improving the effectiveness of a system that is not a retrieval system are not relevant.')''' == str(list(dataset.queries_iter())[0])

    def test_loading_queries_via_rest_api_from_tira_02(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        from tira.third_party_integrations import ir_datasets
        dataset = ir_datasets.load('ir-lab-jena-leipzig-sose-2023/iranthology-20230618-training')
        
        assert 68 == len(list(dataset.queries_iter()))
        print(str(list(dataset.queries_iter())[0]))
        assert '''TirexQuery(query_id='1', text='retrieval system improving effectiveness', title='retrieval system improving effectiveness', query='retrieval system improving effectiveness', description='What papers focus on improving the effectiveness of a retrieval system?', narrative='Relevant papers include research on what makes a retrieval system effective and what improves the effectiveness of a retrieval system. Papers that focus on improving something else or improving the effectiveness of a system that is not a retrieval system are not relevant.')''' == str(list(dataset.queries_iter())[0])

    def test_patching_for_pyterrier_datasets_to_tira(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        import pyterrier as pt
        dataset = pt.get_dataset('irds:workshop-on-open-web-search/retrieval-20231027-training')
        queries = {i['qid']: i['title'] for _, i in dataset.get_topics().iterrows()}

        assert len(dataset.get_topics()) == 3
        assert queries['1'] == 'hubble telescope achievements'

    def test_patching_for_pyterrier_datasets_with_qrels_to_tira(self):
        ensure_pyterrier_is_loaded(patch_ir_datasets=True)
        import pyterrier as pt
        dataset = pt.get_dataset('irds:workshop-on-open-web-search/retrieval-20231027-training')
        qrels =[i.to_dict() for _, i in dataset.get_qrels().iterrows()]

        assert len(dataset.get_qrels()) == 3
        assert qrels[0] == {'docno': 'doc-1', 'iteration': '0', 'label': 1, 'qid': '1'}
