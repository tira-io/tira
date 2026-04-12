import unittest
import zipfile

from tira.io_utils import sanitize_text, zip_dir

from .format_check import IR_METADATA_MULTIPLE_VALID


class TestIoUtils(unittest.TestCase):
    def test_sanitize_text_keeps_valid_utf8_text(self):
        self.assertEqual("hello äöü 😀", sanitize_text("hello äöü 😀"))

    def test_sanitize_text_removes_lone_high_surrogates(self):
        self.assertEqual("beforeafter", sanitize_text("before\ud83dafter"))

    def test_sanitize_text_removes_lone_low_surrogates(self):
        self.assertEqual("beforeafter", sanitize_text("before\udc00after"))

    def test_sanitize_text_removes_multiple_non_utf8_code_points(self):
        self.assertEqual("ab€c", sanitize_text("a\ud83db\udc00€c"))


    def test_sanitize_text_does_not_remove_umlauts(self):
        self.assertEqual("here are some umlauts äüÄüöÖ#", sanitize_text("here are some umlauts äüÄüöÖ#"))

    def test_sanitize_text_removes_wrong_minus(self):
        inp = """e l s e :
r e l s c o r e = s c o r e s [ 0 ] − 0 . 1 5

5.) Add the recalculated relevance score to the builder to calculate aggregate
scores"""
        exp = """e l s e :
r e l s c o r e = s c o r e s [ 0 ]  0 . 1 5

5.) Add the recalculated relevance score to the builder to calculate aggregate
scores"""

        self.assertEqual(exp, sanitize_text(inp))

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
