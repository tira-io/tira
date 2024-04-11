import unittest
from tests.test_utils import digest_of_dataset, digest_of_run_output
from approvaltests import verify_as_json

class IrLabSoSe2024Test(unittest.TestCase):
    """Unit tests for all use cases of the ir lab in summer semester 2024.
    """
    def test_corpus_is_available(self):
        actual = digest_of_dataset('ir-acl-anthology-20240411-training')
        verify_as_json(actual)

    
    def test_digest_of_run_outputs(self):
        dataset_id = 'ir-acl-anthology-20240411-training'
        approaches = [
            'ir-lab-sose-2024/tira-ir-starter/Index (tira-ir-starter-pyterrier)',
            #'ir-lab-sose-2024/seanmacavaney/DocT5Query',
            #'ir-lab-sose-2024/seanmacavaney/corpus-graph',
            #'ir-lab-sose-2024/ows/pyterrier-anceindex',
            #'ir-lab-sose-2024/naverlabseurope/Splade (Index)',
        ]
        actual = {i: {} for i in approaches}

        run_ids = {"ir-lab-sose-2024": {
            "tira-ir-starter": {
                "Index (tira-ir-starter-pyterrier)": {"ir-acl-anthology-20240411-training": "2024-04-11-19-43-23"}
            }, 
            "seanmacavaney": {
                "DocT5Query": {"ir-acl-anthology-20240411-training": ""},
                "corpus-graph": {"ir-acl-anthology-20240411-training": ""}
            },
            "ows": {
                "pyterrier-anceindex": {"ir-acl-anthology-20240411-training": ""
            }},
            "naverlabseurope": {
                "Splade (Index)": {"ir-acl-anthology-20240411-training": ""}
            }
        }}

        for approach in approaches:
            actual[approach][dataset_id] = digest_of_run_output(approach, dataset_id, run_ids)

        verify_as_json(actual)