import unittest

from tira.local_execution_integration import LocalExecutionIntegration
from tira.tirex_tracker import find_tirex_tracker_executable_or_none


class TirexTrackerTest(unittest.TestCase):
    def test_path_to_tirex_tracker_exists(self):
        actual = find_tirex_tracker_executable_or_none()
        self.assertIsNotNone(actual)
        self.assertTrue(actual.exists())

    def test_tirex_tracker_not_available_in_bash_image(self):
        tira = LocalExecutionIntegration()
        actual = tira.tirex_tracker_available_in_docker_image("bash:alpine3.16")
        self.assertFalse(actual)

    def test_tirex_tracker_is_available_in_debian_image(self):
        tira = LocalExecutionIntegration()
        actual = tira.tirex_tracker_available_in_docker_image("debian:trixie-slim")
        self.assertTrue(actual)
