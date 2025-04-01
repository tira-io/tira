import tempfile
import unittest
from pathlib import Path

from tira_app.endpoints.vm_api import _parse_metadata_from_upload


class TestFileListing(unittest.TestCase):
    def test_for_empty_upload(self):
        expected = {
            "has_metadata": False,
            "metadata_git_repo": None,
            "metadata_has_notebook": False,
            "valid_formats": None,
        }
        with tempfile.TemporaryDirectory() as f:
            actual = _parse_metadata_from_upload(f)
        self.assertEqual(expected, actual)

    def test_for_upload_without_script(self):
        expected = {
            "has_metadata": True,
            "metadata_git_repo": "https://github.com/chatnoir-eu/chatnoir-ir-datasets-indexer/tree/86555193e9bc890c6614559c63f899ada9969b9d",
            "metadata_has_notebook": False,
            "valid_formats": '{"ir_metadata": ["metadata.yml"]}',
        }
        upload_dir = Path(__file__).parent.parent / "resources" / "ir-metadata-no-script"
        actual = _parse_metadata_from_upload(upload_dir)
        self.assertEqual(expected, actual)

    def test_for_upload_with_script(self):
        expected = {
            "has_metadata": True,
            "metadata_git_repo": "https://github.com/chatnoir-eu/chatnoir-ir-datasets-indexer/tree/86555193e9bc890c6614559c63f899ada9969b9d/chatnoir_ir_datasets_indexer/__main__.py",
            "metadata_has_notebook": False,
            "valid_formats": '{"ir_metadata": ["metadata.yml"]}',
        }
        upload_dir = Path(__file__).parent.parent / "resources" / "ir-metadata-with-script"
        actual = _parse_metadata_from_upload(upload_dir)
        self.assertEqual(expected, actual)

    def test_for_upload_with_script_and_notebook(self):
        expected = {
            "has_metadata": True,
            "metadata_git_repo": "https://github.com/chatnoir-eu/chatnoir-ir-datasets-indexer/tree/86555193e9bc890c6614559c63f899ada9969b9d/chatnoir_ir_datasets_indexer/__main__.py",
            "metadata_has_notebook": True,
            "valid_formats": '{"ir_metadata": ["metadata.yml"]}',
        }
        upload_dir = Path(__file__).parent.parent / "resources" / "ir-metadata-with-script-and-notebook"
        actual = _parse_metadata_from_upload(upload_dir)
        self.assertEqual(expected, actual)
