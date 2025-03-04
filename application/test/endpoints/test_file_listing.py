import tempfile
import unittest
from pathlib import Path

from tira_app.endpoints.admin_api import file_listing


class TestFileListing(unittest.TestCase):
    def test_with_few_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i in range(0, 2):
                (Path(tmp_dir) / "foo").mkdir(parents=True, exist_ok=True)
                with open(Path(tmp_dir) / "foo" / f"{i}-foo", "w") as f:
                    f.write("foo")

            actual = file_listing(tmp_dir, "tmp_dir")

        self.assertEqual("tmp_dir", actual["title"])
        self.assertEqual(2, len(actual["children"][0]["children"]))

    def test_with_many_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i in range(0, 10):
                (Path(tmp_dir) / "foo").mkdir(parents=True, exist_ok=True)
                with open(Path(tmp_dir) / "foo" / f"{i}-foo", "w") as f:
                    f.write("foo")

            actual = file_listing(tmp_dir, "tmp_dir")

        self.assertEqual("tmp_dir", actual["title"])
        self.assertEqual(7, len(actual["children"][0]["children"]))
        self.assertEqual({"title": "..."}, actual["children"][0]["children"][6])
