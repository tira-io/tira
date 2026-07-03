import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from tira.local_execution_integration import LocalExecutionIntegration
from tira.third_party_integrations import temporary_directory
from tira.tirex_tracker import find_tirex_tracker_executable_or_none, tirex_tracker_mounts_or_none


class TirexTrackerTest(unittest.TestCase):
    def test_path_to_tirex_tracker_exists(self):
        actual = find_tirex_tracker_executable_or_none()
        self.assertIsNotNone(actual)
        self.assertTrue(actual.exists())

    def test_discovered_tirex_tracker_has_expected_name(self):
        actual = find_tirex_tracker_executable_or_none()
        self.assertIsNotNone(actual)
        self.assertTrue(actual.name.startswith("tirex-tracker-"))
        self.assertTrue(actual.name.endswith("-linux"))

    def test_discovered_tirex_tracker_mounts_read_only_to_tracked(self):
        tracker = find_tirex_tracker_executable_or_none()
        self.assertIsNotNone(tracker)
        self.assertEqual(
            {str(tracker): {"bind": "/tracked", "mode": "ro"}},
            tirex_tracker_mounts_or_none(),
        )

    @patch("tira.tirex_tracker.find_tirex_tracker_executable_or_none", return_value=Path("/tmp/tracked"))
    def test_tirex_tracker_mounts_existing_binary_read_only(self, _tracker_path):
        self.assertEqual(
            {"/tmp/tracked": {"bind": "/tracked", "mode": "ro"}},
            tirex_tracker_mounts_or_none(),
        )

    def test_tirex_tracker_probe_uses_expected_command_and_detects_tracker(self):
        tira = LocalExecutionIntegration()
        client = Mock()
        client.containers.run.return_value = b"Measures runtime, energy, and many other metrics.\n"

        with patch(
            "tira.local_execution_integration.tirex_tracker_mounts_or_none",
            return_value={"/tmp/tracked": {"bind": "/tracked", "mode": "ro"}},
        ):
            actual = tira.tirex_tracker_available_in_docker_image("test-image", client=client)

        self.assertTrue(actual)
        client.containers.run.assert_called_once_with(
            "test-image",
            entrypoint="sh",
            command="-c '/tracked --help'",
            volumes={"/tmp/tracked": {"bind": "/tracked", "mode": "ro"}},
            detach=False,
            remove=True,
            network_disabled=True,
        )

    def test_tirex_tracker_not_available_in_bash_image(self):
        tira = LocalExecutionIntegration()
        actual = tira.tirex_tracker_available_in_docker_image("bash:alpine3.16")
        self.assertFalse(actual)

    def test_tirex_tracker_is_available_in_debian_image(self):
        tira = LocalExecutionIntegration()
        actual = tira.tirex_tracker_available_in_docker_image("debian:trixie-slim")
        self.assertTrue(actual)

    def test_tirex_tracker_captures_the_execution_command(self):
        tira = LocalExecutionIntegration()
        target_file = temporary_directory() / ".tracking-results.yml"

        tira.run(image="debian:trixie-slim", command="ls -lha", input_dir=".", output_dir=target_file.parent)
        self.assertTrue(target_file.is_file())

        actual = yaml.safe_load(Path.read_text(target_file))
        # TODO This should be fixed urgently, especially for replaying executions...
        self.assertIsNone(actual["implementation"]["executable"])
