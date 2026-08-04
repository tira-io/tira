import json
import os
from unittest.mock import MagicMock, patch

from tira.rest_api_client import Client


def test_add_docker_software_sends_default_build_environment():
    client = object.__new__(Client)
    client.base_url = "https://example.org"
    client.verify = False
    client.authentication_headers = MagicMock(return_value={})
    client.fail_if_api_key_is_invalid = MagicMock()
    client.local_execution = MagicMock()
    client.local_execution.docker_image_work_dir.return_value = None
    response = MagicMock(status_code=200)
    response.content = json.dumps({"status": 0, "context": {"display_name": "software"}}).encode()
    build_environment = {
        "GITHUB_REPOSITORY": "owner/repository",
        "GITHUB_WORKFLOW": "Upload Docker Software to TIRA",
        "GITHUB_SHA": "abc123",
        "TIRA_DOCKER_PATH": "docker",
    }

    with (
        patch.dict(os.environ, {**build_environment, "SECRET_TOKEN": "do-not-send"}, clear=True),
        patch("tira.rest_api_client.requests.post", return_value=response) as post_mock,
    ):
        client.add_docker_software(
            "registry/image:tag",
            "run",
            "team",
            "task",
            "repository-id",
            previous_stages=["previous-stage"],
            mount_hf_model=["model"],
        )

    request_json = post_mock.call_args.kwargs["json"]
    assert request_json["build_environment"] == build_environment
    assert "SECRET_TOKEN" not in request_json["build_environment"]
    assert request_json["inputJob"] == ["previous-stage"]
    assert request_json["mount_hf_model"] == ["model"]
