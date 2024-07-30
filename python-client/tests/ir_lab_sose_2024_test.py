import unittest

from approvaltests import verify_as_json

from tests.test_utils import digest_of_dataset, digest_of_run_output


class IrLabSoSe2024Test(unittest.TestCase):
    """Unit tests for all use cases of the ir lab in summer semester 2024."""

    def test_corpus_is_available(self):
        actual = digest_of_dataset("ir-acl-anthology-20240411-training")
        verify_as_json(actual)

    def test_longeval_06_corpus_is_available(self):
        actual = digest_of_dataset("longeval-2023-06-20240418-training")
        verify_as_json(actual)

    def test_longeval_08_corpus_is_available(self):
        actual = digest_of_dataset("longeval-2023-08-20240418-training")
        verify_as_json(actual)

    def test_padua_longeval_06_corpus_is_available(self):
        actual = digest_of_dataset("longeval-2023-06-20240422-training")
        verify_as_json(actual)

    def test_padua_longeval_08_corpus_is_available(self):
        actual = digest_of_dataset("longeval-2023-08-20240422-training")
        verify_as_json(actual)

    def test_longeval_train_corpus_is_available(self):
        actual = digest_of_dataset("longeval-train-20230513-training")
        verify_as_json(actual)

    def test_longeval_short_jul_corpus_is_available(self):
        actual = digest_of_dataset("longeval-short-july-20230513-training")
        verify_as_json(actual)

    def test_longeval_heldout_corpus_is_available(self):
        actual = digest_of_dataset("longeval-heldout-20230513-training")
        verify_as_json(actual)

    def test_training_corpus_is_available(self):
        actual = digest_of_dataset("ir-acl-anthology-20240504-training")
        verify_as_json(actual)

    def test_training_corpus_truth_is_available(self):
        actual = digest_of_dataset("ir-acl-anthology-20240504-training", truth=True)
        verify_as_json(actual)

    def test_longeval_long_september_corpus_is_available(self):
        actual = digest_of_dataset("longeval-long-september-20230513-training")
        verify_as_json(actual)

    def test_longeval_2023_01_is_available(self):
        actual = digest_of_dataset("longeval-2023-01-20240423-training")
        verify_as_json(actual)

    def test_digest_of_run_outputs(self):
        dataset_id = "ir-acl-anthology-20240411-training"
        approaches = [
            "ir-lab-sose-2024/tira-ir-starter/Index (tira-ir-starter-pyterrier)",
            "ir-lab-sose-2024/tira-ir-starter/Index (pyterrier-stanford-lemmatizer)",
            # 'ir-lab-sose-2024/seanmacavaney/DocT5Query',
            # 'ir-lab-sose-2024/seanmacavaney/corpus-graph',
            "ir-lab-sose-2024/ows/pyterrier-anceindex",
            "ir-lab-sose-2024/naverlabseurope/Splade (Index)",
        ]
        actual = {i: {} for i in approaches}

        run_ids = {
            "ir-lab-sose-2024": {
                "tira-ir-starter": {
                    "Index (tira-ir-starter-pyterrier)": {
                        "ir-acl-anthology-20240411-training": "2024-04-11-19-43-23",
                    },
                    "Index (pyterrier-stanford-lemmatizer)": {
                        "ir-acl-anthology-20240411-training": "2024-04-16-11-05-06"
                    },
                },
                "seanmacavaney": {
                    "DocT5Query": {"ir-acl-anthology-20240411-training": ""},
                    "corpus-graph": {"ir-acl-anthology-20240411-training": ""},
                },
                "ows": {"pyterrier-anceindex": {"ir-acl-anthology-20240411-training": "2024-04-11-19-47-18"}},
                "naverlabseurope": {"Splade (Index)": {"ir-acl-anthology-20240411-training": "2024-04-14-08-40-58"}},
            }
        }

        for approach in approaches:
            actual[approach][dataset_id] = digest_of_run_output(approach, dataset_id, run_ids)

        verify_as_json(actual)

    def test_digest_of_index_ir_lab_training(self):
        approach = "ir-lab-sose-2024/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        dataset_id = "ir-acl-anthology-20240504-training"

        run_id = "2024-05-04-16-05-53"
        run_ids = {"ir-lab-sose-2024": {"tira-ir-starter": {"Index (tira-ir-starter-pyterrier)": {dataset_id: run_id}}}}

        actual = digest_of_run_output(approach, dataset_id, run_ids)
        verify_as_json(actual)

    def test_digest_of_index_2023_01(self):
        approach = "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        dataset_id = "longeval-2023-01-20240423-training"

        run_id = "2024-04-24-01-24-17"
        run_ids = {"ir-benchmarks": {"tira-ir-starter": {"Index (tira-ir-starter-pyterrier)": {dataset_id: run_id}}}}

        actual = digest_of_run_output(approach, dataset_id, run_ids)
        verify_as_json(actual)

    def test_digest_of_index_2023_06(self):
        approach = "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        dataset_id = "longeval-2023-06-20240418-training"

        run_id = "2024-04-18-18-04-27"
        run_ids = {"ir-benchmarks": {"tira-ir-starter": {"Index (tira-ir-starter-pyterrier)": {dataset_id: run_id}}}}

        actual = digest_of_run_output(approach, dataset_id, run_ids)
        verify_as_json(actual)

    def test_digest_of_index_2023_08(self):
        approach = "ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)"
        dataset_id = "longeval-2023-08-20240418-training"

        run_id = "2024-04-18-18-16-52"
        run_ids = {"ir-benchmarks": {"tira-ir-starter": {"Index (tira-ir-starter-pyterrier)": {dataset_id: run_id}}}}

        actual = digest_of_run_output(approach, dataset_id, run_ids)
        verify_as_json(actual)
