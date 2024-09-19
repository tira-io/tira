import os
import unittest
from pathlib import Path

from tira.io_utils import _ln_huggingface_model_mounts, huggingface_model_mounts


class MountHfModelTest(unittest.TestCase):
    def test_none_returns_empty_dict(self):
        expected = {}
        actual = huggingface_model_mounts(None)
        self.assertEqual(actual, expected)

    def test_empty_list_returns_empty_dict(self):
        expected = {}
        actual = huggingface_model_mounts([])
        self.assertEqual(actual, expected)

    def test_exception_is_thrown_for_non_existing_model(self):
        with self.assertRaises(Exception) as context:
            huggingface_model_mounts(["model-does-not-exist"])
        self.assertTrue("model-does-not-exist" in str(context.exception))

    def test_mounts_for_single_existing_model(self):
        expected = {
            "models--openai-community--gpt2": {
                "bind": "/root/.cache/huggingface/hub/models--openai-community--gpt2",
                "mode": "ro",
            }
        }
        os.environ["HF_HUB_CACHE"] = "tests/resources/hf/hub"
        actual = huggingface_model_mounts(["openai-community/gpt2"])
        actual = {str(k).split("/")[-1]: v for k, v in actual.items()}
        del os.environ["HF_HUB_CACHE"]
        self.assertEqual(actual, expected)

    def test_mounts_for_multiple_existing_model(self):
        expected = {
            "models--openai-community--gpt2": {
                "bind": "/root/.cache/huggingface/hub/models--openai-community--gpt2",
                "mode": "ro",
            },
            "models--openai-community--gpt2-large": {
                "bind": "/root/.cache/huggingface/hub/models--openai-community--gpt2-large",
                "mode": "ro",
            },
        }
        os.environ["HF_HUB_CACHE"] = "tests/resources/hf/hub"
        actual = huggingface_model_mounts(["openai-community/gpt2", "openai-community/gpt2-large"])
        actual = {str(k).split("/")[-1]: v for k, v in actual.items()}
        del os.environ["HF_HUB_CACHE"]
        self.assertEqual(actual, expected)

    def test_mounts_for_multiple_redundant_existing_model(self):
        expected = {
            "models--openai-community--gpt2": {
                "bind": "/root/.cache/huggingface/hub/models--openai-community--gpt2",
                "mode": "ro",
            },
            "models--openai-community--gpt2-large": {
                "bind": "/root/.cache/huggingface/hub/models--openai-community--gpt2-large",
                "mode": "ro",
            },
        }
        os.environ["HF_HUB_CACHE"] = "tests/resources/hf/hub"
        actual = huggingface_model_mounts(
            [
                "openai-community/gpt2",
                "openai-community/gpt2-large",
                "openai-community/gpt2",
                "openai-community/gpt2-large",
            ]
        )
        actual = {str(k).split("/")[-1]: v for k, v in actual.items()}
        del os.environ["HF_HUB_CACHE"]
        self.assertEqual(actual, expected)

    def test_ln_mount_for_none(self):
        expected = ""
        actual = _ln_huggingface_model_mounts(None)
        self.assertEqual(actual, expected)

    def test_ln_mount_for_empty_string(self):
        expected = ""
        actual = _ln_huggingface_model_mounts("")
        self.assertEqual(actual, expected)

    def test_ln_mount_for_empty_string_after_strip(self):
        expected = ""
        actual = _ln_huggingface_model_mounts("    ")
        self.assertEqual(actual, expected)

    def test_ln_mount_for_non_existing_model_throwns_exception(self):
        with self.assertRaises(Exception) as context:
            _ln_huggingface_model_mounts("this-model-does-not-exist")
        self.assertTrue("this-model-does-not-exist" in str(context.exception))

    def test_ln_mounts_for_single_existing_model(self):
        expected = (
            "mkdir -p /root/.cache/huggingface/hub/; rm -Rf"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2; ln -s"
            " <NORMALIZED>/hub/models--openai-community--gpt2"
            ' /root/.cache/huggingface/hub/models--openai-community--gpt2; echo "mounted 1 models"'
        )
        os.environ["HF_HUB_CACHE"] = "tests/resources/hf/hub"
        actual = _ln_huggingface_model_mounts("openai-community/gpt2")
        actual = actual.replace(str(Path("tests/resources/hf").absolute()), "<NORMALIZED>")
        del os.environ["HF_HUB_CACHE"]
        self.assertEqual(actual, expected)

    def test_ln_mounts_for_single_existing_model_redundant(self):
        expected = (
            "mkdir -p /root/.cache/huggingface/hub/; rm -Rf"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2; ln -s"
            " <NORMALIZED>/hub/models--openai-community--gpt2"
            ' /root/.cache/huggingface/hub/models--openai-community--gpt2; echo "mounted 1 models"'
        )
        os.environ["HF_HUB_CACHE"] = "tests/resources/hf/hub"
        actual = _ln_huggingface_model_mounts("openai-community/gpt2 openai-community/gpt2   openai-community/gpt2")
        actual = actual.replace(str(Path("tests/resources/hf").absolute()), "<NORMALIZED>")
        del os.environ["HF_HUB_CACHE"]
        self.assertEqual(actual, expected)

    def test_ln_mounts_for_multiple_existing_models(self):
        expected = (
            "mkdir -p /root/.cache/huggingface/hub/; rm -Rf"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2; ln -s"
            " <NORMALIZED>/hub/models--openai-community--gpt2"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2; rm -Rf"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2-large; ln -s"
            " <NORMALIZED>/hub/models--openai-community--gpt2-large"
            ' /root/.cache/huggingface/hub/models--openai-community--gpt2-large; echo "mounted 2 models"'
        )
        os.environ["HF_HUB_CACHE"] = "tests/resources/hf/hub"
        actual = _ln_huggingface_model_mounts("openai-community/gpt2 openai-community/gpt2-large")
        actual = actual.replace(str(Path("tests/resources/hf").absolute()), "<NORMALIZED>")
        del os.environ["HF_HUB_CACHE"]
        self.assertEqual(actual, expected)

    def test_ln_mounts_for_multiple_existing_models_redundant(self):
        expected = (
            "mkdir -p /root/.cache/huggingface/hub/; rm -Rf"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2; ln -s"
            " <NORMALIZED>/hub/models--openai-community--gpt2"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2; rm -Rf"
            " /root/.cache/huggingface/hub/models--openai-community--gpt2-large; ln -s"
            " <NORMALIZED>/hub/models--openai-community--gpt2-large"
            ' /root/.cache/huggingface/hub/models--openai-community--gpt2-large; echo "mounted 2 models"'
        )
        os.environ["HF_HUB_CACHE"] = "tests/resources/hf/hub"
        actual = _ln_huggingface_model_mounts(
            "openai-community/gpt2 openai-community/gpt2-large openai-community/gpt2 openai-community/gpt2-large"
            " openai-community/gpt2 openai-community/gpt2-large"
        )
        actual = actual.replace(str(Path("tests/resources/hf").absolute()), "<NORMALIZED>")
        del os.environ["HF_HUB_CACHE"]
        self.assertEqual(actual, expected)
