import unittest
import zipfile

from tira.io_utils import zip_dir

from .format_check import IR_METADATA_MULTIPLE_VALID


class TestIoUtils(unittest.TestCase):
    def test_zipping_of_directory_01(self):
        expected = [
            "metadata.yaml",
            ".ir-metadata.yml",
            "foo-1/m.yaml",
            "foo-1/foo-metadata.yml",
            "foo-1/foo-2/m.yaml",
            "foo-1/foo-2/foo-metadata.yml",
        ]
        zipped = zip_dir(IR_METADATA_MULTIPLE_VALID)
        actual = zipfile.ZipFile(zipped).namelist()
        self.assertEqual(sorted(expected), sorted(actual))

    def test_zipping_of_directory_02(self):
        expected = ["foo-metadata.yml"]
        zipped = zip_dir(IR_METADATA_MULTIPLE_VALID / "foo-1" / "foo-2" / "foo-metadata.yml")
        actual = zipfile.ZipFile(zipped).namelist()
        self.assertEqual(sorted(expected), sorted(actual))

    def test_zipping_of_directory_03(self):
        expected = ["m.yaml"]
        zipped = zip_dir(IR_METADATA_MULTIPLE_VALID / "foo-1" / "foo-2" / "m.yaml")
        actual = zipfile.ZipFile(zipped).namelist()
        self.assertEqual(sorted(expected), sorted(actual))

    def test_zipping_of_directory_04(self):
        expected = ["metadata.yaml"]
        zipped = zip_dir(IR_METADATA_MULTIPLE_VALID / "metadata.yaml")
        actual = zipfile.ZipFile(zipped).namelist()
        self.assertEqual(sorted(expected), sorted(actual))
