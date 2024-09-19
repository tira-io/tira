from datetime import datetime

from django.test import TestCase
from utils_for_testing import set_up_tira_environment

from tira_app.tira_model import model

now = datetime.now().strftime("%Y%m%d")


class TestCreationOfDatasetId(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_dataset_id_for_existing_dataset_on_task_1(self):
        task_id = "shared-task-1"
        dataset_type = "training"
        dataset_name = "dataset-1"
        expected_dataset_id = f"{dataset_name}-{now}_0-{dataset_type}"

        actual_dataset_id = model.get_new_dataset_id(dataset_name, task_id, dataset_type)

        self.assertEqual(expected_dataset_id, actual_dataset_id)

    def test_dataset_id_forn_new_dataset_on_task_1(self):
        task_id = "shared-task-1"
        dataset_type = "training"
        dataset_name = "dataset-2"
        expected_dataset_id = f"{dataset_name}-{now}-{dataset_type}"

        actual_dataset_id = model.get_new_dataset_id(dataset_name, task_id, dataset_type)

        self.assertEqual(expected_dataset_id, actual_dataset_id)

    @classmethod
    def tearDownClass(cls):
        pass
