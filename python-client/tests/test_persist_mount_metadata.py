import tempfile
import unittest
from pathlib import Path

import yaml

from tira.check_format import IrMetadataFormat, _fmt
from tira.io_utils import MOUNTED_DIRECTORIES_METADATA_FILE_NAME, persist_mount_metadata, read_mount_metadata


class TestPersistMountMetadata(unittest.TestCase):
    def test_no_file_is_written_without_dynamic_mounts(self):
        with tempfile.TemporaryDirectory() as run_dir:
            ret = persist_mount_metadata(run_dir, None, software_id="docker-software-1")

            self.assertIsNone(ret)
            self.assertEqual([], list(Path(run_dir).iterdir()))

    def test_no_file_is_written_for_empty_dynamic_mounts(self):
        with tempfile.TemporaryDirectory() as run_dir:
            ret = persist_mount_metadata(run_dir, {}, software_id="docker-software-1")

            self.assertIsNone(ret)
            self.assertEqual([], list(Path(run_dir).iterdir()))

    def test_metadata_file_is_written_next_to_the_output_directory(self):
        with tempfile.TemporaryDirectory() as run_dir:
            run_dir = Path(run_dir)
            (run_dir / "output").mkdir()
            dynamic_mounts = {
                "NUGGETS": {"source": "OUTPUT_OF_OTHER_EXECUTION", "mode": "ro", "run_id": "the-run-id"},
            }

            ret = persist_mount_metadata(run_dir, dynamic_mounts, software_id="docker-software-42")

            self.assertEqual(run_dir / MOUNTED_DIRECTORIES_METADATA_FILE_NAME, ret)
            self.assertTrue(ret.is_file())
            self.assertFalse((run_dir / "output" / MOUNTED_DIRECTORIES_METADATA_FILE_NAME).exists())

    def test_metadata_contains_environment_variable_run_id_and_software_id(self):
        with tempfile.TemporaryDirectory() as run_dir:
            dynamic_mounts = {
                "NUGGETS": {"source": "OUTPUT_OF_OTHER_EXECUTION", "mode": "ro", "run_id": "the-run-id"},
                "CACHE_DIR": {"source": "EMPTY_DIR", "mode": "rw"},
            }

            ret = persist_mount_metadata(run_dir, dynamic_mounts, software_id="docker-software-42")
            content = yaml.safe_load(ret.read_text())

            self.assertEqual("docker-software-42", content["resources"]["software"])
            mounted_directories = {i["environment variable"]: i for i in content["resources"]["mounted directories"]}

            self.assertEqual(
                {"environment variable": "NUGGETS", "source": "OUTPUT_OF_OTHER_EXECUTION", "mode": "ro", "run_id": "the-run-id"},
                mounted_directories["NUGGETS"],
            )
            self.assertEqual(
                {"environment variable": "CACHE_DIR", "source": "EMPTY_DIR", "mode": "rw"},
                mounted_directories["CACHE_DIR"],
            )

    def test_metadata_drops_unexpected_fields_from_mount_configuration(self):
        with tempfile.TemporaryDirectory() as run_dir:
            dynamic_mounts = {"NUGGETS": {"source": "EMPTY_DIR", "mode": "rw", "unexpected-field": "should-be-dropped"}}

            ret = persist_mount_metadata(run_dir, dynamic_mounts, software_id="docker-software-42")
            content = yaml.safe_load(ret.read_text())

            self.assertEqual(
                {"environment variable": "NUGGETS", "source": "EMPTY_DIR", "mode": "rw"},
                content["resources"]["mounted directories"][0],
            )

    def test_metadata_handles_non_dict_mount_configuration(self):
        with tempfile.TemporaryDirectory() as run_dir:
            dynamic_mounts = {"NUGGETS": "/some/local/path"}

            ret = persist_mount_metadata(run_dir, dynamic_mounts, software_id="docker-software-42")
            content = yaml.safe_load(ret.read_text())

            self.assertEqual(
                {"environment variable": "NUGGETS", "source": "/some/local/path"},
                content["resources"]["mounted directories"][0],
            )

    def test_metadata_is_valid_ir_metadata(self):
        with tempfile.TemporaryDirectory() as run_dir:
            dynamic_mounts = {"NUGGETS": {"source": "EMPTY_DIR", "mode": "rw"}}

            persist_mount_metadata(run_dir, dynamic_mounts, software_id="docker-software-42")

            fmt = IrMetadataFormat()
            fmt.apply_configuration_and_throw_if_invalid({})
            status, _ = fmt.check_format(Path(run_dir))

            self.assertEqual(_fmt.OK, status)

    def test_software_id_is_optional(self):
        with tempfile.TemporaryDirectory() as run_dir:
            dynamic_mounts = {"NUGGETS": {"source": "EMPTY_DIR", "mode": "rw"}}

            ret = persist_mount_metadata(run_dir, dynamic_mounts)
            content = yaml.safe_load(ret.read_text())

            self.assertIsNone(content["resources"]["software"])


class TestReadMountMetadata(unittest.TestCase):
    def test_returns_empty_dict_without_a_metadata_file(self):
        with tempfile.TemporaryDirectory() as run_dir:
            self.assertEqual({}, read_mount_metadata(run_dir))

    def test_reads_back_run_ids_written_by_persist_mount_metadata(self):
        with tempfile.TemporaryDirectory() as run_dir:
            dynamic_mounts = {
                "NUGGETS": {"source": "OUTPUT_OF_OTHER_EXECUTION", "mode": "ro", "run_id": "the-run-id"},
                "OTHER": {"source": "OUTPUT_OF_OTHER_EXECUTION", "mode": "ro", "run_id": "other-run-id"},
            }
            persist_mount_metadata(run_dir, dynamic_mounts, software_id="docker-software-42")

            self.assertEqual(
                {"NUGGETS": "the-run-id", "OTHER": "other-run-id"},
                read_mount_metadata(run_dir),
            )

    def test_mounts_without_a_run_id_are_not_part_of_the_result(self):
        with tempfile.TemporaryDirectory() as run_dir:
            dynamic_mounts = {"CACHE_DIR": {"source": "EMPTY_DIR", "mode": "rw"}}
            persist_mount_metadata(run_dir, dynamic_mounts, software_id="docker-software-42")

            self.assertEqual({}, read_mount_metadata(run_dir))

    def test_returns_empty_dict_for_malformed_yaml(self):
        with tempfile.TemporaryDirectory() as run_dir:
            (Path(run_dir) / MOUNTED_DIRECTORIES_METADATA_FILE_NAME).write_text("not: valid: yaml: [")

            self.assertEqual({}, read_mount_metadata(run_dir))


if __name__ == "__main__":
    unittest.main()
