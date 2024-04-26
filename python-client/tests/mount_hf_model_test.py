from tira.io_utils import huggingface_model_mounts
import unittest
import os

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
            huggingface_model_mounts(['model-does-not-exist'])
        self.assertTrue('model-does-not-exist' in str(context.exception))

    def test_mounts_for_single_existing_model(self):
        expected = {'models--openai-community--gpt2': {'bind': '/root/.cache/huggingface/hub/models--openai-community--gpt2', 'mode': 'ro'}}
        os.environ['HF_HUB_CACHE'] = 'tests/resources/hf/hub'
        actual = huggingface_model_mounts(['openai-community/gpt2'])
        actual = {str(k).split('/')[-1]: v for k, v in actual.items()}
        del os.environ['HF_HUB_CACHE']
        self.assertEqual(actual, expected)

    def test_mounts_for_multiple_existing_model(self):
        expected = {
            'models--openai-community--gpt2': {'bind': '/root/.cache/huggingface/hub/models--openai-community--gpt2', 'mode': 'ro'},
            'models--openai-community--gpt2-large': {'bind': '/root/.cache/huggingface/hub/models--openai-community--gpt2-large', 'mode': 'ro'},
            }
        os.environ['HF_HUB_CACHE'] = 'tests/resources/hf/hub'
        actual = huggingface_model_mounts(['openai-community/gpt2', 'openai-community/gpt2-large'])
        actual = {str(k).split('/')[-1]: v for k, v in actual.items()}
        del os.environ['HF_HUB_CACHE']
        self.assertEqual(actual, expected)

    def test_mounts_for_multiple_redundant_existing_model(self):
        expected = {
            'models--openai-community--gpt2': {'bind': '/root/.cache/huggingface/hub/models--openai-community--gpt2', 'mode': 'ro'},
            'models--openai-community--gpt2-large': {'bind': '/root/.cache/huggingface/hub/models--openai-community--gpt2-large', 'mode': 'ro'},
            }
        os.environ['HF_HUB_CACHE'] = 'tests/resources/hf/hub'
        actual = huggingface_model_mounts(['openai-community/gpt2', 'openai-community/gpt2-large', 'openai-community/gpt2', 'openai-community/gpt2-large'])
        actual = {str(k).split('/')[-1]: v for k, v in actual.items()}
        del os.environ['HF_HUB_CACHE']
        self.assertEqual(actual, expected)