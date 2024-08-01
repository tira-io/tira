from django.test import TestCase
from utils_for_testing import set_up_tira_environment, software_non_public, software_public, software_with_inputs

from tira.tira_model import model

PARTICIPANT = "PARTICIPANT-FOR-TEST-1"
TASK = "shared-task-1"


class TestMultiStepJobsWithMultipleInputs(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_for_none_as_input(self):
        docker_software = None
        actual = model.get_ordered_additional_input_runs_of_software(docker_software)

        self.assertEqual(actual, [], "Should return list of length 0")

    def test_for_non_existing_software(self):
        docker_software = {"docker_software_id": -120102121}
        actual = model.get_ordered_additional_input_runs_of_software(docker_software)

        self.assertEqual(actual, [], "Should return list of length 0")

    def test_for_existing_software_without_inputs(self):
        docker_software = model.get_docker_software_by_name(software_public, PARTICIPANT, TASK)
        actual = model.get_ordered_additional_input_runs_of_software(docker_software)

        self.assertIsNotNone(docker_software)
        self.assertIsNotNone(docker_software["docker_software_id"])
        self.assertEqual(actual, [], "Should return list of length 0")

    def test_for_existing_software_with_inputs(self):
        docker_software = model.get_docker_software_by_name(software_with_inputs, PARTICIPANT, TASK)
        expected = [
            (model.get_docker_software_by_name(software_public, PARTICIPANT, TASK)["docker_software_id"], None),
            (model.get_docker_software_by_name(software_non_public, PARTICIPANT, TASK)["docker_software_id"], None),
            (model.get_docker_software_by_name(software_public, PARTICIPANT, TASK)["docker_software_id"], None),
        ]

        actual = model.get_ordered_additional_input_runs_of_software(docker_software)

        self.assertIsNotNone(docker_software)
        self.assertIsNotNone(docker_software["docker_software_id"])
        self.assertEqual(len(actual), 3, "Should return list of length 3")
        self.assertEqual(actual, expected, "Order should be public, non public, public")

    @classmethod
    def tearDownClass(cls):
        pass
