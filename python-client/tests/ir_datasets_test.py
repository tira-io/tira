from tira.third_party_integrations import register_rerank_data_to_ir_datasets
import ir_datasets

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

