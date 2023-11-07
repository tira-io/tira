from tira.rest_api_client import Client
tira = Client()


def test_all_softwares_works_for_tirex():
    actual = tira.all_softwares("ir-benchmarks")
    
    assert 'ir-benchmarks/tira-ir-starter/ChatNoir' in actual
    assert 'ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)' in actual

def test_details_of_public_software_01():
    actual = tira.docker_software( 'ir-benchmarks/tira-ir-starter/TF_IDF (tira-ir-starter-pyterrier)')

    assert actual is not None
    assert actual['ir_re_ranker'] == False

