import os
import stat
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, call, patch

from tira.check_format import _fmt
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

    def test_run_translates_volume_sources_via_tira_docker_tmpdir(self):
        integration = LocalExecutionIntegration()

        container = Mock()
        container.id = "container-1"
        container.attach = lambda **_kwargs: iter([b""])
        container.wait = lambda: {"StatusCode": 0}

        client = Mock()
        client.containers.run.return_value = container

        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            with (
                patch(
                    "tira.local_execution_integration.environment_variables_to_forward",
                    return_value={},
                ),
                patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
                patch("tira.local_execution_integration.tempfile.gettempdir", return_value=tempfile.gettempdir()),
            ):
                integration.ensure_image_available_locally = Mock()
                integration.tirex_tracker_available_in_docker_image = Mock(return_value=False)
                integration._LocalExecutionIntegration__docker_client = Mock(return_value=client)

                integration.run(
                    image="test-image",
                    command="echo hello",
                    input_dir=input_dir,
                    output_dir=output_dir,
                )

        actual_volumes = client.containers.run.call_args.kwargs["volumes"]
        real_tmp_dir = tempfile.gettempdir()
        expected_input = "/host-tmp" + input_dir[len(real_tmp_dir) :]
        expected_output = "/host-tmp" + output_dir[len(real_tmp_dir) :]

        self.assertIn(expected_input, actual_volumes)
        self.assertIn(expected_output, actual_volumes)
        self.assertNotIn(input_dir, actual_volumes)
        self.assertNotIn(output_dir, actual_volumes)

    def test_evaluate_translates_volume_sources_via_tira_docker_tmpdir(self):
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

            with (
                patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
                patch("tira.local_execution_integration.tempfile.gettempdir", return_value=str(root)),
            ):
                integration.evaluate(
                    eval_dir,
                    output_dir,
                    allow_network=False,
                    evaluate={
                        "evaluator_id": "evaluator",
                        "evaluator_git_runner_image": "evaluator-image",
                        "evaluator_git_runner_command": "evaluate",
                        "truth_directory": str(truths_dir),
                    },
                    client=client,
                )

        actual_volumes = client.containers.run.call_args.kwargs["volumes"]
        expected_eval_dir = "/host-tmp" + str(eval_dir)[len(str(root)) :]
        expected_output_dir = "/host-tmp" + str(output_dir)[len(str(root)) :]
        expected_truths_dir = "/host-tmp" + str(truths_dir)[len(str(root)) :]

        self.assertIn(expected_eval_dir, actual_volumes)
        self.assertIn(expected_output_dir, actual_volumes)
        self.assertIn(expected_truths_dir, actual_volumes)
        self.assertNotIn(str(eval_dir), actual_volumes)
        self.assertNotIn(str(output_dir), actual_volumes)
        self.assertNotIn(str(truths_dir), actual_volumes)

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

    def test_run_workflow_copies_network_access_log_next_to_output_dir(self):
        from tira.workflows import WorkflowResult

        integration = LocalExecutionIntegration()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "output"
            output_dir.mkdir()

            execution_dir = root / "execution"
            execution_dir.mkdir()
            (execution_dir / "output").mkdir()
            (execution_dir / "output" / "run.txt").write_text("some-prediction")
            (execution_dir / "network-access.log").write_text("example.com\t3\n")

            workflow_result = WorkflowResult(_fmt.OK, "ok", execution_dir)

            with patch("tira.workflows.run_workflow", return_value=workflow_result) as run_workflow_mock:
                integration.run_workflow(
                    image="some-image",
                    command="some-command",
                    input_dir=str(root / "input"),
                    output_dir=output_dir,
                    task_workflow_configuration={"name": "cached-execution"},
                    software_workflow_configuration={},
                )

            run_workflow_mock.assert_called_once()
            self.assertEqual("some-prediction", (output_dir / "run.txt").read_text())
            copied_log = output_dir.parent / "network-access.log"
            self.assertTrue(copied_log.is_file())
            self.assertEqual("example.com\t3\n", copied_log.read_text())

    def test_run_workflow_does_not_fail_without_network_access_log(self):
        from tira.workflows import WorkflowResult

        integration = LocalExecutionIntegration()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_dir = root / "output"
            output_dir.mkdir()

            execution_dir = root / "execution"
            execution_dir.mkdir()
            (execution_dir / "output").mkdir()
            (execution_dir / "output" / "run.txt").write_text("some-prediction")

            workflow_result = WorkflowResult(_fmt.OK, "ok", execution_dir)

            with patch("tira.workflows.run_workflow", return_value=workflow_result):
                integration.run_workflow(
                    image="some-image",
                    command="some-command",
                    input_dir=str(root / "input"),
                    output_dir=output_dir,
                    task_workflow_configuration={"name": "cached-execution"},
                    software_workflow_configuration={},
                )

            self.assertEqual("some-prediction", (output_dir / "run.txt").read_text())
            self.assertFalse((output_dir.parent / "network-access.log").is_file())

    def __simulate_container_appending_input_to_output(self, *_args, **run_kwargs):
        volumes = run_kwargs["volumes"]
        input_dir = next(Path(k) for k, v in volumes.items() if v["bind"] == "/tira-data/input")
        output_dir = next(Path(k) for k, v in volumes.items() if v["bind"] == "/tira-data/output")

        content = (input_dir / "input.txt").read_text()
        (output_dir / "output.txt").write_text(content + "-appended")

    def test_verify_tmp_directory_is_usable_by_docker_succeeds_for_working_tmp_dir(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        client.containers.run.side_effect = self.__simulate_container_appending_input_to_output
        integration._LocalExecutionIntegration__docker_client = Mock(return_value=client)
        integration.ensure_image_available_locally = Mock()
        integration.get_container_cli = Mock(return_value="docker")

        # Should not raise.
        integration.verify_tmp_directory_is_usable_by_docker()

        client.containers.run.assert_called_once()

    def test_verify_tmp_directory_is_usable_by_docker_raises_if_container_run_fails(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        client.containers.run.side_effect = ConnectionError("no permission to mount /tmp")
        integration._LocalExecutionIntegration__docker_client = Mock(return_value=client)
        integration.ensure_image_available_locally = Mock()
        integration.get_container_cli = Mock(return_value="docker")

        with self.assertRaises(ValueError) as cm:
            integration.verify_tmp_directory_is_usable_by_docker()

        self.assertIn("TMPDIR", str(cm.exception))
        self.assertIn("no permission to mount /tmp", str(cm.exception))

    def test_verify_tmp_directory_is_usable_by_docker_raises_if_output_is_not_as_expected(self):
        integration = LocalExecutionIntegration()
        client = Mock()
        # The container does not write the expected output (e.g., because the mounted directory was
        # actually empty due to a misconfigured TMPDIR).
        client.containers.run.return_value = Mock()
        integration._LocalExecutionIntegration__docker_client = Mock(return_value=client)
        integration.ensure_image_available_locally = Mock()
        integration.get_container_cli = Mock(return_value="docker")

        with self.assertRaises(ValueError) as cm:
            integration.verify_tmp_directory_is_usable_by_docker()

        self.assertIn("TMPDIR", str(cm.exception))
