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


def test_update_upload_metadata_posts_to_save_software_upload_endpoint():
    client = object.__new__(Client)
    client.base_url = "https://example.org"
    client.verify = False
    client.failsave_retries = 1
    client.failsave_max_delay = 1
    client.authentication_headers = MagicMock(return_value={})
    client.get_csrf_token = MagicMock(return_value="csrf-token")
    response = MagicMock(status_code=200)
    response.json.return_value = {"status": 0, "message": "Software edited successfully"}

    with patch("tira.rest_api_client.requests.post", return_value=response) as post_mock:
        result = client.update_upload_metadata(
            "some-task", "some-team", "42", "my-system", "a description", {"track": "main"}
        )

    assert result == {"status": 0, "message": "Software edited successfully"}
    assert post_mock.call_args.kwargs["url"] == "https://example.org/task/some-task/vm/some-team/save_software/upload/42"
    assert post_mock.call_args.kwargs["json"] == {
        "display_name": "my-system",
        "description": "a description",
        "paper_link": "",
        "upload_metadata": {"track": "main"},
    }


def test_validate_upload_metadata_passes_through_without_configured_fields():
    client = object.__new__(Client)
    client.upload_form_fields_for_task = MagicMock(return_value=None)

    result = client.validate_upload_metadata("some-task", {"track": "main"})

    assert result == {"track": "main"}


def test_validate_upload_metadata_drops_unknown_field_after_cache_refresh():
    client = object.__new__(Client)
    fields = [{"name": "track", "display_name": "Track", "type": "text"}]
    client.upload_form_fields_for_task = MagicMock(return_value=fields)

    result = client.validate_upload_metadata("some-task", {"track": "main", "unknown_field": "x"})

    assert result == {"track": "main"}
    # Once for the initial (cached) lookup, once for the force_reload retry on mismatch.
    assert client.upload_form_fields_for_task.call_count == 2
    client.upload_form_fields_for_task.assert_any_call("some-task", force_reload=False)
    client.upload_form_fields_for_task.assert_any_call("some-task", force_reload=True)


def test_validate_upload_metadata_drops_invalid_select_option():
    client = object.__new__(Client)
    fields = [
        {
            "name": "track",
            "display_name": "Track",
            "type": "select",
            "options": [{"id": "main", "display_value": "Main"}],
        }
    ]
    client.upload_form_fields_for_task = MagicMock(return_value=fields)

    result = client.validate_upload_metadata("some-task", {"track": "not-an-option"})

    assert result == {}


def test_validate_upload_metadata_keeps_description_field_always():
    client = object.__new__(Client)
    fields = [{"name": "track", "display_name": "Track", "type": "text"}]
    client.upload_form_fields_for_task = MagicMock(return_value=fields)

    result = client.validate_upload_metadata("some-task", {"track": "main", "description": "some notes"})

    assert result == {"track": "main", "description": "some notes"}
