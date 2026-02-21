from pathlib import Path

from django.test import TestCase

from tira_app.git_runner_integration import GitRunner


class TestRenderingOfJobFile(TestCase):
    def test_git_runner_can_be_instantiated(self):
        git_runner = GitRunner()

        self.assertIsNotNone(git_runner)

