import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from tira.tira_run import stage_multiple_input_runs_into_temp_dir


class TestStageMultipleInputRunsIntoTempDir(unittest.TestCase):
    def test_staged_runs_are_copied_numbered_starting_at_one(self):
        with tempfile.TemporaryDirectory() as run_1, tempfile.TemporaryDirectory() as run_2:
            (Path(run_1) / "input.txt").write_text("run-1")
            (Path(run_2) / "input.txt").write_text("run-2")

            tira = Mock()
            tira.get_run_output.side_effect = [run_1, run_2]

            actual = stage_multiple_input_runs_into_temp_dir(tira, ["approach-1", "approach-2"], "dataset")

            self.assertEqual("run-1", (Path(actual) / "1" / "input.txt").read_text())
            self.assertEqual("run-2", (Path(actual) / "2" / "input.txt").read_text())

    def test_staged_runs_are_created_below_tmpdir(self):
        with tempfile.TemporaryDirectory() as run_1, tempfile.TemporaryDirectory() as custom_tmp_dir:
            (Path(run_1) / "input.txt").write_text("run-1")

            tira = Mock()
            tira.get_run_output.side_effect = [run_1]

            previous_tmpdir = os.environ.get("TMPDIR")
            previous_tempfile_tempdir = tempfile.tempdir
            os.environ["TMPDIR"] = custom_tmp_dir
            # tempfile caches the resolved temp dir in tempfile.tempdir after first use, so it has to be
            # reset in order to pick up the TMPDIR change made above.
            tempfile.tempdir = None
            try:
                actual = stage_multiple_input_runs_into_temp_dir(tira, ["approach-1"], "dataset")
            finally:
                if previous_tmpdir is None:
                    os.environ.pop("TMPDIR", None)
                else:
                    os.environ["TMPDIR"] = previous_tmpdir
                tempfile.tempdir = previous_tempfile_tempdir

            self.assertTrue(str(Path(actual).resolve()).startswith(str(Path(custom_tmp_dir).resolve())))

    def test_staged_runs_do_not_hard_code_tmp(self):
        with tempfile.TemporaryDirectory() as run_1:
            (Path(run_1) / "input.txt").write_text("run-1")

            tira = Mock()
            tira.get_run_output.side_effect = [run_1]

            actual = stage_multiple_input_runs_into_temp_dir(tira, ["approach-1"], "dataset")

            # Regression test for a bug where the hard-coded prefix "/tmp/" was prepended to the
            # already-absolute path returned by tempfile.TemporaryDirectory().name, resulting in a
            # broken, doubled path such as "/tmp//tmp/tmpXXXX".
            self.assertNotIn("/tmp//tmp", actual)


if __name__ == "__main__":
    unittest.main()
