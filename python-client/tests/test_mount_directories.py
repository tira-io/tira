import unittest
from pathlib import Path

from tira.io_utils import resolve_mount_directory

CURRENT_DIR = Path(__file__).parent


class TestMountDirectories(unittest.TestCase):
    def test_null_is_valid(self):
        actual = resolve_mount_directory(None, None, None)
        self.assertIsNone(actual)

    def test_empty_list_is_valid(self):
        actual = resolve_mount_directory([], None, None)
        self.assertIsNone(actual)

    def test_local_directory_01(self):
        actual = resolve_mount_directory(["$var1=" + str(CURRENT_DIR)], None, None)
        self.assertEqual(set(["var1"]), actual.keys())
        self.assertTrue((Path(actual["var1"]) / "test_mount_directories.py").exists())

    def test_local_directory_02(self):
        actual = resolve_mount_directory(["var1=" + str(CURRENT_DIR)], None, None)
        self.assertEqual(set(["var1"]), actual.keys())
        self.assertTrue((Path(actual["var1"]) / "test_mount_directories.py").exists())
