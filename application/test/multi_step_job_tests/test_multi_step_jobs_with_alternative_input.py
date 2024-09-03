from datetime import datetime

from django.test import TestCase
from utils_for_testing import set_up_tira_environment

import tira_app.model as modeldb
from tira_app.tira_model import latest_output_of_software_on_dataset

# Used for some tests
now = datetime.now().strftime("%Y%m%d")


class TestMultiStepJobsWithAlternativeInput(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_for_non_existing_software(self):
        actual = latest_output_of_software_on_dataset("task_id", "vm_id", "software_id", -1, "dataset_id", None)

        self.assertIsNone(actual)

    def test_where_suitable_input_exists(self):
        expected = {
            "task_id": "shared-task-1",
            "vm_id": "example_participant",
            "dataset_id": f"dataset-1-{now}-training",
            "run_id": "run-0-example_participant",
        }
        es1 = modeldb.DockerSoftware.objects.filter(
            vm=modeldb.VirtualMachine.objects.get(vm_id="example_participant"),
            task=modeldb.Task.objects.get(task_id="shared-task-1"),
            display_name="software_e1",
        )[0]

        actual = latest_output_of_software_on_dataset(
            "shared-task-1",
            "example_participant",
            "does-not-exist",
            es1.docker_software_id,
            f"dataset-1-{now}-training",
            None,
        )

        self.assertEqual(expected, actual)

    def test_suitable_input_does_not_exist_1(self):
        actual = latest_output_of_software_on_dataset(
            "shared-task-1", "participant-does-not-exist", "does-not-exist----1", -1, f"dataset-1-{now}-training", None
        )

        self.assertIsNone(actual)

    def test_suitable_input_does_not_exist_2(self):
        actual = latest_output_of_software_on_dataset(
            "shared-task-does-not-exist",
            "example_participant",
            "does-not-exist----1",
            -1,
            f"dataset-1-{now}-training",
            None,
        )

        self.assertIsNone(actual)

    def test_suitable_input_does_not_exist_3(self):
        actual = latest_output_of_software_on_dataset(
            "shared-task-1", "example_participant", "does-not-exist", -1, "dataset-does-not-exist", None
        )

        self.assertIsNone(actual)

    @classmethod
    def tearDownClass(cls):
        pass
