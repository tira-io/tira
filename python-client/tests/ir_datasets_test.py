from tira.third_party_integrations import register_rerank_data_to_ir_datasets
import ir_datasets

register_rerank_data_to_ir_datasets('tests/sample-tirex-rerank-data', 'tirex-sample-dataset')

    
def test_document_exists():
    
    dataset = ir_dataset.load('tirex-sample-dataset', 'vaswani')
    
    assert False

