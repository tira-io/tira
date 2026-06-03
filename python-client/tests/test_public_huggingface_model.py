import unittest
from unittest.mock import Mock, patch

import httpx
from huggingface_hub.errors import HfHubHTTPError, RepositoryNotFoundError

from tira.third_party_integrations import is_public_huggingface_model


def _hf_error(error_cls, status_code: int):
    request = httpx.Request("GET", "https://huggingface.co/api/models/test")
    response = httpx.Response(status_code=status_code, request=request)
    return error_cls("hf-error", response=response)


class TestPublicHuggingfaceModel(unittest.TestCase):
    @patch("huggingface_hub.HfApi")
    def test_returns_true_for_public_model(self, hf_api):
        hf_api.return_value.model_info.return_value = Mock(private=False, gated=False)

        actual = is_public_huggingface_model("openai-community--gpt2")

        self.assertTrue(actual)
        hf_api.assert_called_once_with(token=False)
        hf_api.return_value.model_info.assert_called_once_with("openai-community/gpt2", token=False)

    @patch("huggingface_hub.HfApi")
    def test_returns_false_when_model_does_not_exist(self, hf_api):
        hf_api.return_value.model_info.side_effect = _hf_error(RepositoryNotFoundError, 404)

        actual = is_public_huggingface_model("does-not-exist/model")

        self.assertFalse(actual)

    @patch("huggingface_hub.HfApi")
    def test_returns_false_for_private_model(self, hf_api):
        hf_api.return_value.model_info.side_effect = _hf_error(HfHubHTTPError, 403)

        actual = is_public_huggingface_model("private/model")

        self.assertFalse(actual)

    @patch("huggingface_hub.HfApi")
    def test_returns_false_for_gated_model(self, hf_api):
        hf_api.return_value.model_info.return_value = Mock(private=False, gated="manual")

        actual = is_public_huggingface_model("meta-llama/Llama-3.1-8B")

        self.assertFalse(actual)

    @patch("huggingface_hub.HfApi")
    def test_returns_false_for_private_flagged_model(self, hf_api):
        hf_api.return_value.model_info.return_value = Mock(private=True, gated=False)

        actual = is_public_huggingface_model("private/model")

        self.assertFalse(actual)

    @patch("huggingface_hub.HfApi")
    def test_raises_for_unexpected_huggingface_error(self, hf_api):
        hf_api.return_value.model_info.side_effect = _hf_error(HfHubHTTPError, 500)

        with self.assertRaises(HfHubHTTPError):
            is_public_huggingface_model("broken/model")
