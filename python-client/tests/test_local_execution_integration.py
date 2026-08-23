import os
import stat
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, call, patch

from tira.local_execution_integration import LocalExecutionIntegration


class TestLocalExecutionIntegration(unittest.TestCase):
    def test_get_valid_docker_socket_returns_and_caches_working_socket(self):
        integration = LocalExecutionIntegration()
        unavailable_client = Mock()
        unavailable_client.images.list.side_effect = ConnectionError("Docker is unavailable")
        podman_client = Mock()
        podman_client.images.list.return_value = []
        podman_client.containers.list.return_value = []

        socket_stat = Mock()
        socket_stat.st_mode = stat.S_IFSOCK
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("tira.local_execution_integration.sys.platform", "linux"),
            patch.object(
                integration,
                "_LocalExecutionIntegration__docker_linux_sockets",
                return_value=["/var/run/docker.sock", "/run/user/1000/podman/podman.sock"],
            ),
            patch("tira.local_execution_integration.os.path.exists", return_value=True),
            patch("tira.local_execution_integration.os.stat", return_value=socket_stat),
            patch(
                "tira.local_execution_integration.docker.from_env",
                side_effect=[unavailable_client, podman_client],
            ) as from_env,
            patch("tira.local_execution_integration.logging.warning") as warning,
        ):
            actual = integration.get_valid_docker_socket()
            cached = integration.get_valid_docker_socket()

        self.assertEqual("unix:///run/user/1000/podman/podman.sock", actual)
        self.assertEqual(actual, cached)
        self.assertEqual(actual, integration.docker_socket)
        self.assertEqual(2, from_env.call_count)
        unavailable_client.close.assert_called_once_with()
        podman_client.close.assert_called_once_with()
        warning.assert_called_once()

    def test_get_valid_docker_socket_returns_configured_docker_host(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        client.images.list.return_value = []
        client.containers.list.return_value = []

        with (
            patch.dict(os.environ, {"DOCKER_HOST": "unix:///custom/podman.sock"}, clear=True),
            patch("tira.local_execution_integration.docker.from_env", return_value=client) as from_env,
            patch("tira.local_execution_integration.logging.warning") as warning,
        ):
            actual = integration.get_valid_docker_socket()

        self.assertEqual("unix:///custom/podman.sock", actual)
        self.assertEqual(actual, integration.docker_socket)
        self.assertEqual("unix:///custom/podman.sock", from_env.call_args.kwargs["environment"]["DOCKER_HOST"])
        client.close.assert_called_once_with()
        warning.assert_not_called()

    def test_get_valid_docker_socket_raises_for_invalid_configured_docker_host(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        client.images.list.side_effect = ConnectionError("Docker is unavailable")
        with (
            patch.dict(os.environ, {"DOCKER_HOST": "unix:///invalid/docker.sock"}, clear=True),
            patch("tira.local_execution_integration.docker.from_env", return_value=client),
        ):
            with self.assertRaises(ConnectionError):
                integration.get_valid_docker_socket()

        self.assertIsNone(integration.docker_socket)
        client.close.assert_called_once_with()

    def test_container_cli_uses_and_caches_cli_matching_socket(self):
        integration = LocalExecutionIntegration()

        with (
            patch.object(
                integration,
                "get_valid_docker_socket",
                return_value="unix:///run/user/1000/podman/podman.sock",
            ),
            patch("tira.local_execution_integration.shutil.which", return_value="/usr/bin/podman") as which,
        ):
            actual = integration.get_container_cli()
            cached = integration.get_container_cli()

        self.assertEqual("podman", actual)
        self.assertEqual(actual, cached)
        which.assert_called_once_with("podman")

    def test_container_cli_uses_docker_for_docker_socket(self):
        integration = LocalExecutionIntegration()

        with (
            patch.object(
                integration,
                "get_valid_docker_socket",
                return_value="unix:///var/run/docker.sock",
            ),
            patch("tira.local_execution_integration.shutil.which", return_value="/usr/bin/docker") as which,
        ):
            actual = integration.get_container_cli()

        self.assertEqual("docker", actual)
        which.assert_called_once_with("docker")

    def test_container_cli_does_not_use_docker_for_podman_socket(self):
        integration = LocalExecutionIntegration()

        with (
            patch.object(
                integration,
                "get_valid_docker_socket",
                return_value="unix:///run/user/1000/podman/podman.sock",
            ),
            patch("tira.local_execution_integration.shutil.which", return_value=None) as which,
        ):
            with self.assertRaisesRegex(ValueError, "Neither Docker nor Podman is installed"):
                integration.get_container_cli()

        which.assert_called_once_with("podman")

    def test_container_cli_falls_back_to_podman_without_identifiable_socket(self):
        integration = LocalExecutionIntegration()

        with (
            patch.object(integration, "get_valid_docker_socket", return_value=None),
            patch(
                "tira.local_execution_integration.shutil.which",
                side_effect=[None, "/usr/bin/podman"],
            ) as which,
        ):
            actual = integration.get_container_cli()

        self.assertEqual("podman", actual)
        self.assertEqual([call("docker"), call("podman")], which.call_args_list)

    def test_container_cli_uses_configured_podman_socket(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        client.images.list.return_value = []
        client.containers.list.return_value = []

        with (
            patch.dict(os.environ, {"DOCKER_HOST": "unix:///custom/podman.sock"}, clear=True),
            patch("tira.local_execution_integration.docker.from_env", return_value=client),
            patch("tira.local_execution_integration.shutil.which", return_value="/usr/bin/podman") as which,
        ):
            actual = integration.get_container_cli()

        self.assertEqual("podman", actual)
        self.assertEqual("unix:///custom/podman.sock", integration.docker_socket)
        client.close.assert_called_once_with()
        which.assert_called_once_with("podman")

    def test_build_docker_image_uses_docker_format_with_podman(self):
        integration = LocalExecutionIntegration()
        integration.get_container_cli = Mock(return_value="podman")
        integration.verify_image = Mock()

        with patch("tira.local_execution_integration.subprocess.call", return_value=0) as subprocess_call:
            integration.build_docker_image(".", "test-image", "Dockerfile")

        command = subprocess_call.call_args.args[0]
        self.assertIn("--format", command)
        self.assertEqual("docker", command[command.index("--format") + 1])

    def test_build_docker_image_does_not_pass_format_to_docker(self):
        integration = LocalExecutionIntegration()
        integration.get_container_cli = Mock(return_value="docker")
        integration.verify_image = Mock()

        with patch("tira.local_execution_integration.subprocess.call", return_value=0) as subprocess_call:
            integration.build_docker_image(".", "test-image", "Dockerfile")

        self.assertNotIn("--format", subprocess_call.call_args.args[0])

    def test_push_image_passes_repository_and_tag_separately(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        client.images.push.return_value = []
        image = client.images.get.return_value
        integration._LocalExecutionIntegration__docker_client = Mock(return_value=client)
        integration.docker_client_is_authenticated = Mock(return_value=True)

        actual = integration.push_image(
            "tira-mini",
            required_prefix="registry.webis.de/code-research/tira/tira-user-webis/",
        )

        self.assertEqual(
            "registry.webis.de/code-research/tira/tira-user-webis/tira-mini:latest",
            actual,
        )
        image.tag.assert_called_once_with(
            "registry.webis.de/code-research/tira/tira-user-webis/tira-mini",
            tag="latest",
        )

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

    def test_run_uses_nano_cpus_for_linux_containers(self):
        integration = LocalExecutionIntegration()

        container = Mock()
        container.id = "container-1"
        container.attach.return_value = iter([b"container output\n"])
        container.wait.return_value = {"StatusCode": 0}

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

                integration.run(
                    image="test-image",
                    command="echo hello",
                    input_dir=input_dir,
                    output_dir=output_dir,
                    cpu_count=2,
                    platform="linux/amd64",
                )

        run_kwargs = client.containers.run.call_args.kwargs
        self.assertEqual(2_000_000_000, run_kwargs["nano_cpus"])
        self.assertNotIn("cpu_count", run_kwargs)

    def test_run_keeps_cpu_count_for_non_linux_containers(self):
        integration = LocalExecutionIntegration()

        container = Mock()
        container.id = "container-1"
        container.attach.return_value = iter([b"container output\n"])
        container.wait.return_value = {"StatusCode": 0}

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

                integration.run(
                    image="test-image",
                    command="echo hello",
                    input_dir=input_dir,
                    output_dir=output_dir,
                    cpu_count=2,
                    platform="windows/amd64",
                )

        run_kwargs = client.containers.run.call_args.kwargs
        self.assertEqual(2, run_kwargs["cpu_count"])
        self.assertNotIn("nano_cpus", run_kwargs)

    def test_run_mounts_dict_mount_directory_with_requested_mode(self):
        integration = LocalExecutionIntegration()

        container = Mock()
        container.id = "container-1"
        container.attach.return_value = iter([b"container output\n"])
        container.wait.return_value = {"StatusCode": 0}

        client = Mock()
        client.containers.run.return_value = container

        with (
            tempfile.TemporaryDirectory() as input_dir,
            tempfile.TemporaryDirectory() as output_dir,
            tempfile.TemporaryDirectory() as mount_dir,
        ):
            with patch(
                "tira.local_execution_integration.environment_variables_to_forward",
                return_value={},
            ):
                integration.ensure_image_available_locally = Mock()
                integration.tirex_tracker_available_in_docker_image = Mock(return_value=False)
                integration._LocalExecutionIntegration__docker_client = Mock(return_value=client)

                integration.run(
                    image="test-image",
                    command="echo hello",
                    input_dir=input_dir,
                    output_dir=output_dir,
                    mount_directory={"CACHE_DIR": {"path": mount_dir, "mode": "rw"}},
                )

        run_kwargs = client.containers.run.call_args.kwargs
        self.assertEqual("rw", run_kwargs["volumes"][mount_dir]["mode"])
        self.assertTrue(run_kwargs["network_disabled"])
        self.assertNotIn("network_mode", run_kwargs)

    def test_evaluator_configuration_can_allow_network(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        container = Mock()
        container.attach.return_value = []
        client.containers.run.return_value = container

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            eval_dir = root / "evaluation"
            output_dir = root / "run"
            truths_dir = root / "truths"
            eval_dir.mkdir()
            output_dir.mkdir()
            truths_dir.mkdir()

            integration.evaluate(
                eval_dir,
                output_dir,
                allow_network=False,
                evaluate={
                    "evaluator_id": "evaluator",
                    "evaluator_git_runner_image": "evaluator-image",
                    "evaluator_git_runner_command": "evaluate",
                    "truth_directory": str(truths_dir),
                    "allow_network": True,
                },
                client=client,
            )

        self.assertFalse(client.containers.run.call_args.kwargs["network_disabled"])
