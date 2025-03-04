import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tira.rest_api_client import Client


class CodeSubmissionTest(unittest.TestCase):
    def test_code_submission_fails_if_code_not_in_version_control(self):
        tira = Client()
        with tempfile.TemporaryDirectory() as tmp_file:
            with self.assertRaises(ValueError):
                tira.submit_code(Path(tmp_file), "wows-eval")

    def test_code_submission_fails_for_dirty_git_repo(self):
        tira = Client()
        with self.assertRaises(ValueError):
            tira.submit_code(Path("tests") / "resources" / "git-repo-dirty" / "some-directory", "wows-eval")

    def test_code_submission_works(self):
        tira = Client()
        expected_code_files = ["some-directory/.gitignore", "some-directory/Dockerfile", "some-directory/script.sh"]
        actual = tira.submit_code(Path("tests") / "resources" / "git-repo-clean" / "some-directory", "wows-eval")
        zipObj = ZipFile(actual["code"])
        files_in_zip = [i.filename for i in zipObj.infolist()]
        self.assertEqual(files_in_zip, expected_code_files)
