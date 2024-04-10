import unittest
from tests.test_utils import digest_of_dataset, digest_of_run_output
from approvaltests import verify_as_json

class IrLabSoSe2024Test(unittest.TestCase):
    """Unit tests for all use cases of the ir lab in summer semester 2024.
    """
    def test_corpus_is_available(self):
        actual = digest_of_dataset('anthology-20240408-training')
        verify_as_json(actual)

    
    def test_digest_of_run_outputs(self):
        dataset_id = 'anthology-20240408-training'
        approaches = [
            'ir-lab-sose-2024/tira-ir-starter/Index (tira-ir-starter-pyterrier)',
            'ir-lab-sose-2024/seanmacavaney/DocT5Query',
            'ir-lab-sose-2024/seanmacavaney/corpus-graph',
            'ir-lab-sose-2024/ows/pyterrier-anceindex',
            'ir-lab-sose-2024/naverlabseurope/Splade (Index)',
        ]
        actual = {i: {} for i in approaches}

        run_ids = {"ir-lab-sose-2024": {
            "tira-ir-starter": {
                "Index (tira-ir-starter-pyterrier)": {"anthology-20240408-training": "2024-04-08-15-52-07"}
            }, 
            "seanmacavaney": {
                "DocT5Query": {"anthology-20240408-training": "2024-04-09-22-03-26"},
                "corpus-graph": {"anthology-20240408-training": "2024-04-09-16-35-50"}
            },
            "ows": {
                "pyterrier-anceindex": {"anthology-20240408-training": "2024-04-08-18-00-08"
            }},
            "naverlabseurope": {
                "Splade (Index)": {"anthology-20240408-training": "2024-04-09-16-40-49"}
            }
        }}

        for approach in approaches:
            actual[approach][dataset_id] = digest_of_run_output(approach, dataset_id, run_ids)

        verify_as_json(actual)