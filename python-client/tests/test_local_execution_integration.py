import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import Mock, patch

from tira.local_execution_integration import LocalExecutionIntegration


class TestLocalExecutionIntegration(unittest.TestCase):
    def test_run_tracks_running_container_until_it_finishes(self):
        integration = LocalExecutionIntegration()

        container = Mock()
        container.id = "container-1"

        def attach(**_kwargs):
            self.assertIn(container.id, integration.running_docker_images)
            yield b"container output\n"

        def wait():
            self.assertIn(container.id, integration.running_docker_images)
            return {"StatusCode": 0}

        container.attach = attach
        container.wait = wait

        client = Mock()
        client.containers.run.return_value = container

        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            with patch(
                "tira.local_execution_integration.environment_variables_to_forward",
                return_value={},
            ):
                integration.ensure_image_available_locally = Mock()
                integration.tirex_tracker_available_in_docker_image = Mock(return_value=False)
                integration._LocalExecutionIntegration__docker_client = Mock(return_value=client)

                actual = integration.run(
                    image="test-image",
                    command="echo hello",
                    input_dir=input_dir,
                    output_dir=output_dir,
                )

        self.assertEqual({}, integration.running_docker_images)
        self.assertEqual({"unknown-software-id": os.path.abspath(output_dir)}, actual)

    def test_stop_run_kills_tracked_container(self):
        integration = LocalExecutionIntegration()
        container = Mock()
        integration.running_docker_images["container-1"] = container

        integration.stop_run("container-1")

        container.kill.assert_called_once_with()

    def test_kill_all_running_containers_is_failsafe(self):
        integration = LocalExecutionIntegration()
        integration.running_docker_images = {"container-1": Mock(), "container-2": Mock()}
        integration.stop_run = Mock(side_effect=[ValueError("foo"), None])
        stdout = StringIO()

        with patch("sys.stdout", stdout):
            with self.assertLogs(level="ERROR") as logs:
                integration.kill_all_running_containers()

        self.assertEqual(2, integration.stop_run.call_count)
        self.assertIn("Could not stop running docker image", stdout.getvalue())
        self.assertIn("container-1", stdout.getvalue())
        self.assertTrue(any("Could not stop running docker image with id container-1" in i for i in logs.output))
