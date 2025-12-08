import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from tira.tira_cli import upload_command


def upl(
    dataset: "Optional[str]",
    directory: Path,
    system: str,
    default_task: "Optional[str]" = None,
    tira_vm_id: "Optional[str]" = None,
    anonymous: "Optional[bool]" = False,
):
    os.environ["TIRA_CACHE_DIR"] = str(Path(__file__).parent / "resources" / "local_tira_without_internet")
    stdout = StringIO()
    stderr = StringIO()

    with redirect_stdout(stdout), redirect_stderr(stderr):
        actual = upload_command(dataset, directory, True, system, default_task, tira_vm_id, anonymous)

    del os.environ["TIRA_CACHE_DIR"]

    return actual, stdout.getvalue() + "\n" + stderr.getvalue()


class TestRunUploadDryRun(unittest.TestCase):
    def test_on_non_existing_directory(self):
        ret_code, outp = upl(None, "/this-directory/does-not-exist", None)

        self.assertEqual(1, ret_code)
        self.assertIn("The directory passed via --directory does not exist. Got /this-directory/does-not-exist", outp)

    def test_on_empty_directory_no_dataset(self):
        with TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            p.mkdir(parents=True, exist_ok=True)
            ret_code, outp = upl(None, str(p), None)

            self.assertEqual(1, ret_code)
            self.assertIn(
                "The dataset is not defined. Please either define a it in a ir-metadata.yml (data: test collection: name: ...) or pass --dataset",
                outp,
            )

    def test_on_empty_directory_with_dataset(self):
        with TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            p.mkdir(parents=True, exist_ok=True)
            ret_code, outp = upl("dataset-does-not-exist-20241201-training", str(p), None)

            self.assertEqual(1, ret_code)
            self.assertIn(
                "I expected a file ir-metadata.yml in the directory",
                outp,
            )

    def test_on_incomplete_submission(self):
        p = Path(__file__).parent / "resources" / "wows26" / "incomplete"
        ret_code, outp = upl(None, str(p), None)

        self.assertEqual(1, ret_code)
        self.assertIn(
            "is still set to the default value ENTER_VALUE_HERE. Please replace this.",
            outp,
        )

    def test_on_complete_submission_inconsistent_dataset_id(self):
        p = Path(__file__).parent / "resources" / "wows26" / "complete"
        ret_code, outp = upl("dataset-does-not-exist-20241201-training", str(p), None)

        self.assertIn(
            "The dataset for the submission is inconsistent. I got",
            outp,
        )
        self.assertIn(
            "but the metadata of the directory",
            outp,
        )
        self.assertEqual(1, ret_code)

    def test_on_complete_submission_with_inconsistent_team(self):
        p = Path(__file__).parent / "resources" / "wows26" / "complete"
        ret_code, outp = upl(None, str(p), None, tira_vm_id="inconsistent-team")

        self.assertIn(
            "The team for which the submission is to be uploaded is inconsistent. I got inconsistent-team from the --tira-vm-id command line but the metadata of",
            outp,
        )
        self.assertEqual(1, ret_code)

    def test_on_complete_submission_with_consistent_team(self):
        p = Path(__file__).parent / "resources" / "wows26" / "complete"
        ret_code, outp = upl(None, str(p), None, tira_vm_id="some-name")

        self.assertIn(
            "The run is valid. I skip upload to TIRA as --dry-run was passed.",
            outp,
        )
        self.assertEqual(0, ret_code)

    def test_on_complete_submission_withoutdataset_id(self):
        p = Path(__file__).parent / "resources" / "wows26" / "complete"
        ret_code, outp = upl(None, str(p), None)

        self.assertIn(
            "The run is valid. I skip upload to TIRA as --dry-run was passed.",
            outp,
        )
        self.assertEqual(0, ret_code)
