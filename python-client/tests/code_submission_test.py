import os
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
                tira.submit_code(Path(tmp_file), "wows-eval", dry_run=True)

    def test_code_submission_fails_for_dirty_git_repo(self):
        tira = Client()
        with tempfile.TemporaryDirectory() as tmp_file:
            with ZipFile(Path("tests") / "resources" / "example-git-repositories.zip", "r") as zip_ref:
                zip_ref.extractall(tmp_file)
            with self.assertRaises(ValueError):
                tira.submit_code(Path(tmp_file) / "git-repo-dirty" / "some-directory", "wows-eval", dry_run=True)

    def test_code_submission_works(self):
        tira = Client(tira_cache_dir="./tests/resources/local_cached_zip")
        expected_code_files = ["some-directory/.gitignore", "some-directory/Dockerfile", "some-directory/script.sh"]

        with tempfile.TemporaryDirectory() as tmp_file:
            with ZipFile(Path("tests") / "resources" / "example-git-repositories.zip", "r") as zip_ref:
                zip_ref.extractall(tmp_file)

            os.chmod(str(Path(tmp_file) / "git-repo-clean" / "some-directory" / "script.sh"), 0o0766)
            actual = tira.submit_code(
                Path(tmp_file) / "git-repo-clean" / "some-directory", "task-does-not-exist", dry_run=True
            )

        zipObj = ZipFile(actual["code"])
        files_in_zip = [i.filename for i in zipObj.infolist()]

        self.assertEqual({"origin": "foo"}, actual["remotes"])
        self.assertEqual("976c6949b9992aabc785ccb8544652dc3b149fb5", actual["commit"])
        self.assertEqual("main", actual["active_branch"])
        self.assertTrue(actual["image"].startswith("some-directory"))

        self.assertEqual(files_in_zip, expected_code_files)
