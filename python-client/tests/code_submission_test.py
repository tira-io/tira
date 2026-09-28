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

    def test_code_submission_zip_contains_tracked_files_when_submitting_from_repository_root(self):
        """When the submission path is the git repository root itself (i.e., not a subdirectory of the
        repository), the produced source-code.zip must still contain all git-tracked files.

        This used to be a bug: `directory_in_path` was (incorrectly) computed as the repository's own
        directory name instead of the empty string, so no tracked file matched the
        `startswith(f"{directory}/")` filter used in `TiraClient._zip_tracked_files`, and the zip ended
        up empty.
        """
        import git

        tira = Client(tira_cache_dir="./tests/resources/local_cached_zip")

        with tempfile.TemporaryDirectory() as tmp_file:
            repo_dir = Path(tmp_file) / "repo-at-root"
            repo_dir.mkdir()
            (repo_dir / "Dockerfile").write_text(
                'FROM bash\n\nADD script.sh /script.sh\n\nENTRYPOINT [ "./script.sh" ]\n'
            )
            (repo_dir / "script.sh").write_text(
                "#!/usr/bin/env bash\n"
                'echo \'{"id": "foo-1", "text": "a"}\' > ${TIRA_OUTPUT_DIR}/preds.jsonl\n'
                'echo \'{"id": "foo-2", "text": "a"}\' >> ${TIRA_OUTPUT_DIR}/preds.jsonl\n'
                'echo \'{"id": "foo-3", "text": "a"}\' >> ${TIRA_OUTPUT_DIR}/preds.jsonl\n'
                'echo \'{"id": "foo-4", "text": "a"}\' >> ${TIRA_OUTPUT_DIR}/preds.jsonl\n'
            )
            os.chmod(str(repo_dir / "script.sh"), 0o0766)

            repo = git.Repo.init(repo_dir, initial_branch="main")
            repo.create_remote("origin", "foo")
            repo.git.add(A=True)
            repo.index.commit("init")

            actual = tira.submit_code(repo_dir, "task-does-not-exist", dry_run=True)

        zipObj = ZipFile(actual["code"])
        files_in_zip = [i.filename for i in zipObj.infolist()]

        self.assertEqual(sorted(files_in_zip), ["Dockerfile", "script.sh"])
        self.assertEqual({"origin": "foo"}, actual["remotes"])
        self.assertEqual("main", actual["active_branch"])
