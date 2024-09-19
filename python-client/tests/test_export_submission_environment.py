import unittest

from tira.io_utils import all_environment_variables_for_github_action_or_fail


class TestExportSubmissionEnvironment(unittest.TestCase):
    def test_empty_parameters_fails(self):
        with self.assertRaises(ValueError):
            all_environment_variables_for_github_action_or_fail([])

    def test_all_required_parameters_are_there_docker_image(self):
        actual = all_environment_variables_for_github_action_or_fail(
            [
                "GITHUB_SHA=sha",
                "TIRA_VM_ID=vm",
                "TIRA_TASK_ID=task",
                "TIRA_DOCKER_REGISTRY_TOKEN=docker-token",
                "TIRA_DOCKER_REGISTRY_USER=docker-user",
                "TIRA_CLIENT_TOKEN=tira-token",
                "TIRA_CLIENT_USER=tira-user",
                "TIRA_CODE_REPOSITORY_ID=repo-id",
                "TIRA_DOCKER_FILE=Dockerfile",
                "TIRA_DOCKER_PATH=dockerpath",
                "TIRA_COMMAND=cmd",
            ]
        )

        self.assertTrue("GITHUB_SHA=sha" in actual)
        self.assertTrue(
            "IMAGE_TAG=registry.webis.de/code-research/tira/tira-user-vm/submission-dockerpath:sha" in actual
        )

    def test_all_required_parameters_are_there_jupyter_notebook(self):
        actual = all_environment_variables_for_github_action_or_fail(
            [
                "GITHUB_SHA=sha",
                "TIRA_VM_ID=vm",
                "TIRA_TASK_ID=task",
                "TIRA_DOCKER_REGISTRY_TOKEN=docker-token",
                "TIRA_DOCKER_REGISTRY_USER=docker-user",
                "TIRA_CLIENT_TOKEN=tira-token",
                "TIRA_CLIENT_USER=tira-user",
                "TIRA_CODE_REPOSITORY_ID=repo-id",
                "TIRA_DOCKER_FILE=Dockerfile",
                "TIRA_DOCKER_PATH=dockerpath",
                "TIRA_COMMAND=cmd",
                "TIRA_JUPYTER_NOTEBOOK=123",
            ]
        )

        self.assertTrue("GITHUB_SHA=sha" in actual)
        self.assertTrue("IMAGE_TAG=registry.webis.de/code-research/tira/tira-user-vm/submission:sha" in actual)
