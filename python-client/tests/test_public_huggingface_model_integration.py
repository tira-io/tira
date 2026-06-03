import unittest

from tira.third_party_integrations import is_public_huggingface_model


class TestPublicHuggingfaceModelIntegration(unittest.TestCase):
    def test_detects_known_public_model(self):
        self.assertTrue(is_public_huggingface_model("openai-community/gpt2"))

    def test_rejects_missing_model(self):
        self.assertFalse(is_public_huggingface_model("tira-io/zzz-does-not-exist-7f9ab4a7b9144e51b7ea0e2c8b1d78cc"))

    def test_rejects_private_model(self):
        self.assertFalse(is_public_huggingface_model("meta-llama/Llama-3.1-8B"))
