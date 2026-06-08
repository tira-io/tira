import ast
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch

from tira.check_format import _fmt
from tira.io_utils import _md5_of_file, resolve_mirrored_resources, sanitize_text, verify_tirex_tracker, zip_dir

from .format_check import IR_METADATA_MULTIPLE_VALID

RESOURCE_LOADING_FROM_WEBIS = Path(__file__).parent / "resources" / "resource-loading-from-webis"
TRUTHS_ZIP_URL = "https://files.webis.de/data-in-progress/data-research/web-search/reneuir-25/truths.zip"
TRUTHS_ZIP_MD5 = "f28e36759760c9520e7831aba86c4d23"


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

    @patch("tira.io_utils.find_tirex_tracker_executable_or_none", return_value=Path("/tmp/tracked"))
    @patch(
        "tira.io_utils.check_output",
        return_value=b"Measures runtime, energy, and many other metrics of a specifed command.\n",
    )
    def test_verify_tirex_tracker_reports_ok_for_valid_help_output(self, _check_output, _tracker_path):
        self.assertEqual(
            (_fmt.OK, "The tirex-tracker works and will track experimental metadata."),
            verify_tirex_tracker(),
        )

    @patch("tira.io_utils.find_tirex_tracker_executable_or_none", return_value=None)
    def test_verify_tirex_tracker_warns_when_tracker_is_missing(self, _tracker_path):
        self.assertEqual(
            (_fmt.WARN, "The tirex-tracker is not available. Experimental metadata will not be tracked."),
            verify_tirex_tracker(),
        )

    @patch("tira.io_utils.find_tirex_tracker_executable_or_none", return_value=Path("/tmp/tracked"))
    @patch("tira.io_utils.check_output", side_effect=CalledProcessError(1, ["/tmp/tracked", "--help"]))
    def test_verify_tirex_tracker_warns_when_tracker_execution_fails(self, _check_output, _tracker_path):
        self.assertEqual(
            (_fmt.WARN, "The tirex-tracker is not working. Experimental metadata will not be tracked."),
            verify_tirex_tracker(),
        )

    def test_resolve_mirrored_resources_skips_download_for_matching_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resource_dir = self._copy_resource_directory(tmp_dir)
            original_example_file = (resource_dir / "example-file").read_bytes()
            (resource_dir / "truths.zip").write_text("already present", encoding="utf-8")

            with (
                patch("tira.io_utils._md5_of_file", return_value=TRUTHS_ZIP_MD5),
                patch("tira.io_utils._download_file_with_md5") as download_file,
            ):
                actual = resolve_mirrored_resources(resource_dir)

            self.assertEqual(resource_dir, actual)
            download_file.assert_not_called()
            self.assertEqual(original_example_file, (resource_dir / "example-file").read_bytes())

    def test_resolve_mirrored_resources_downloads_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resource_dir = self._copy_resource_directory(tmp_dir)
            original_example_file = (resource_dir / "example-file").read_bytes()
            target_file = resource_dir / "truths.zip"

            with patch("tira.io_utils._download_file_with_md5", side_effect=self._download_to(target_file)) as download_file:
                resolve_mirrored_resources(resource_dir)

            download_file.assert_called_once_with(TRUTHS_ZIP_URL, target_file, TRUTHS_ZIP_MD5)
            self.assertEqual(b"downloaded truths.zip", target_file.read_bytes())
            self.assertEqual(original_example_file, (resource_dir / "example-file").read_bytes())

    def test_resolve_mirrored_resources_downloads_when_md5_does_not_match(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resource_dir = self._copy_resource_directory(tmp_dir)
            original_example_file = (resource_dir / "example-file").read_bytes()
            target_file = resource_dir / "truths.zip"
            target_file.write_text("corrupted", encoding="utf-8")

            with (
                patch("tira.io_utils._md5_of_file", return_value="does-not-match"),
                patch("tira.io_utils._download_file_with_md5", side_effect=self._download_to(target_file)) as download_file,
            ):
                resolve_mirrored_resources(resource_dir)

            download_file.assert_called_once_with(TRUTHS_ZIP_URL, target_file, TRUTHS_ZIP_MD5)
            self.assertEqual(b"downloaded truths.zip", target_file.read_bytes())
            self.assertEqual(original_example_file, (resource_dir / "example-file").read_bytes())

    def test_resolve_mirrored_resources_raises_for_unexpected_download_md5(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resource_dir = self._copy_resource_directory(tmp_dir)
            original_example_file = (resource_dir / "example-file").read_bytes()

            with patch("tira.io_utils._download_file_with_md5", side_effect=ValueError("MD5 is unexpected")):
                with self.assertRaises(ValueError) as exc:
                    resolve_mirrored_resources(resource_dir)

            self.assertIn("MD5 is unexpected", str(exc.exception))
            self.assertFalse((resource_dir / "truths.zip").exists())
            self.assertEqual(original_example_file, (resource_dir / "example-file").read_bytes())

    def test_resolve_mirrored_resources_example_01(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resource_dir = self._copy_resource_directory(tmp_dir)
            md5_example_file = "34c96b1fdd79dc2c69a396f4c9935f9c"
            md5_truth_file = "f28e36759760c9520e7831aba86c4d23"

            self.assertFalse((resource_dir / "truths.zip").exists())
            resolve_mirrored_resources(resource_dir)
            self.assertTrue((resource_dir / "truths.zip").exists())
            self.assertEqual(md5_truth_file, _md5_of_file(resource_dir / "truths.zip"))
            self.assertEqual(md5_example_file, _md5_of_file(resource_dir / "example-file"))


    def test_resolve_mirrored_resources_example_02(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resource_dir = self._copy_resource_directory(tmp_dir)
            md5_example_file = "34c96b1fdd79dc2c69a396f4c9935f9c"
            md5_truth_file = "f28e36759760c9520e7831aba86c4d23"

            self.assertFalse((resource_dir / "truths.zip").exists())
            resolve_mirrored_resources(resource_dir)
            self.assertTrue((resource_dir / "truths.zip").exists())
            self.assertEqual(md5_truth_file, _md5_of_file(resource_dir / "truths.zip"))
            self.assertEqual(md5_example_file, _md5_of_file(resource_dir / "example-file"))

            with patch("tira.io_utils._download_file_with_md5", side_effect=ValueError("MD5 is unexpected")) as download_file:
                resolve_mirrored_resources(resource_dir)
                self.assertTrue((resource_dir / "truths.zip").exists())
                self.assertEqual(md5_truth_file, _md5_of_file(resource_dir / "truths.zip"))
                self.assertEqual(md5_example_file, _md5_of_file(resource_dir / "example-file"))

            download_file.assert_not_called()

    def _copy_resource_directory(self, tmp_dir: str) -> Path:
        target_dir = Path(tmp_dir) / "resource-loading-from-webis"
        shutil.copytree(RESOURCE_LOADING_FROM_WEBIS, target_dir)
        self.assertEqual(
            ast.literal_eval((target_dir / ".mirrored-resources.json").read_text(encoding="utf-8"))["truths.zip"]["url"],
            TRUTHS_ZIP_URL,
        )
        return target_dir

    def _download_to(self, target_file: Path):
        def side_effect(_url: str, _target_file: Path, _expected_md5: str):
            target_file.write_bytes(b"downloaded truths.zip")

        return side_effect
