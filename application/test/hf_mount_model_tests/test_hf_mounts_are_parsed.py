import unittest

from huggingface_hub import snapshot_download

from tira.huggingface_hub_integration import _hf_repos, huggingface_model_mounts


class TestHfMountsAreParsed(unittest.TestCase):
    def fail_if_hf_is_not_installed(self):
        snapshot_download(repo_id="prajjwal1/bert-tiny")
        self.assertGreater(len(_hf_repos()), 0)

    def test_hf_is_installed(self):
        self.fail_if_hf_is_not_installed()

    def test_none_as_hf_model_mounts(self):
        self.fail_if_hf_is_not_installed()
        expected = []
        actual = huggingface_model_mounts(None)

        self.assertEqual(expected, actual)

    def test_empty_list_as_hf_model_mounts(self):
        self.fail_if_hf_is_not_installed()
        expected = []
        actual = huggingface_model_mounts([])

        self.assertEqual(expected, actual)

    def test_non_existing_hf_models_can_not_be_mounted(self):
        self.fail_if_hf_is_not_installed()
        with self.assertRaises(Exception) as context:
            huggingface_model_mounts(["does-not-exist"])
        self.assertTrue("does-not-exist" in str(context.exception))

    def test_existing_hf_model_can_be_mounted(self):
        self.fail_if_hf_is_not_installed()

        actual = huggingface_model_mounts(["prajjwal1/bert-tiny"])
        self.assertEqual("prajjwal1/bert-tiny", actual["MOUNT_HF_MODEL"])
