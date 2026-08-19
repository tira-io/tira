import unittest

from tira.tira_cli import requires_mount_workflow


class TestRequiresMountWorkflow(unittest.TestCase):
    def test_non_cache_dir_mount_requires_mount_workflow(self):
        self.assertTrue(requires_mount_workflow({"mount_config": {"NUGGETS": "ro"}}))

    def test_cache_dir_mount_requires_mount_workflow(self):
        self.assertTrue(requires_mount_workflow({"mount_config": {"CACHE_DIR": "rw"}}))

    def test_cache_behaviour_requires_mount_workflow(self):
        self.assertTrue(requires_mount_workflow({"cache_behaviour": "deterministic"}))

    def test_system_without_mounts_uses_direct_execution(self):
        self.assertFalse(requires_mount_workflow({}))
        self.assertFalse(requires_mount_workflow({"mount_config": {}}))
