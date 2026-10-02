import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tira.tira_cli import run_local


class TestRunLocalCompileFromCode(unittest.TestCase):
    def test_compile_from_code_requires_admin_role(self):
        client = MagicMock()
        client.json_response.return_value = {"context": {"role": "guest"}}

        with patch("tira.tira_cli.RestClient", return_value=client):
            with self.assertRaisesRegex(ValueError, "--compile-from-code requires admin access"):
                run_local(
                    input="does-not-matter",
                    approach="task/team/software",
                    cpus=None,
                    memory=None,
                    out=None,
                    forward_environment_variable=None,
                    mount_directory=None,
                    mount_cache=None,
                    compile_from_code=True,
                )

        client.private_system_details.assert_not_called()
        client.build_docker_image_from_try_run_metadata.assert_not_called()

    def test_compile_from_code_uses_compiled_image_for_admin(self):
        client = MagicMock()
        client.json_response.return_value = {"context": {"role": "admin"}}
        client.private_system_details.return_value = {
            "docker_software_id": 1,
            "tira_image_name": "some/original-image:latest",
            "command": "run.sh",
            "forward_environment_variable": [],
            "try_run_metadata": {"uuid": "some-uuid"},
        }
        client.build_docker_image_from_try_run_metadata.return_value = "compiled-from-code-abcde"

        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            client.datasets.return_value = {input_dir: {"run_format": [], "format_configuration": None}}
            client.local_execution.run.return_value = Path(output_dir)

            with patch("tira.tira_cli.RestClient", return_value=client), patch(
                "tira.check_format.check_format", return_value=(0, "ok")
            ):
                run_local(
                    input=input_dir,
                    approach="task/team/software",
                    cpus=None,
                    memory=None,
                    out=None,
                    forward_environment_variable=None,
                    mount_directory=None,
                    mount_cache=None,
                    compile_from_code=True,
                )

        client.private_system_details.assert_called_once_with("task/team/software")
        client.build_docker_image_from_try_run_metadata.assert_called_once()
        called_system_details = client.build_docker_image_from_try_run_metadata.call_args[0][0]
        self.assertEqual(called_system_details["try_run_metadata"]["uuid"], "some-uuid")

        client.local_execution.run.assert_called_once()
        self.assertEqual(client.local_execution.run.call_args.kwargs["image"], "compiled-from-code-abcde")
