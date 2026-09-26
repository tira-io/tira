import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from tira.rest_api_client import Client


def _write_try_run_metadata_zip(target_zip: Path, submission_uuid: str, source_code_directory: str = ""):
    """Builds a zip that mimics the one served by the anonymous-uploads download endpoint: all
    files nested inside a directory named after the submission uuid, containing a
    submission-metadata.yml plus a nested source-code.zip."""
    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir)
        upload_dir = staging / submission_uuid
        upload_dir.mkdir(parents=True)

        (upload_dir / "submission-metadata.yml").write_text(
            yaml.safe_dump({"source_code_directory": source_code_directory})
        )

        source_code_root = staging / "source-code-content"
        docker_dir = source_code_root / source_code_directory if source_code_directory else source_code_root
        docker_dir.mkdir(parents=True)
        (docker_dir / "Dockerfile").write_text("FROM bash\n")

        source_code_zip = upload_dir / "source-code.zip"
        with zipfile.ZipFile(source_code_zip, "w") as zf:
            for f in source_code_root.rglob("*"):
                if f.is_file():
                    zf.write(f, arcname=str(f.relative_to(source_code_root)))

        with zipfile.ZipFile(target_zip, "w") as zf:
            for f in upload_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, arcname=str(f.relative_to(staging)))


class TestBuildDockerImageFromTryRunMetadata(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

    def _client_with_mocks(self, submission_uuid: str, source_code_directory: str = ""):
        client = Client()

        def fake_download_and_extract_zip(url, target_dir, extract=True):
            zip_file = Path(self.tmp_dir) / f"try-run-metadata-{submission_uuid}.zip"
            _write_try_run_metadata_zip(zip_file, submission_uuid, source_code_directory)
            with zipfile.ZipFile(zip_file) as zf:
                zf.extractall(target_dir)

        client.download_and_extract_zip = MagicMock(side_effect=fake_download_and_extract_zip)
        client.local_execution = MagicMock()
        client.local_execution.build_docker_image = MagicMock()
        return client

    def test_fails_without_try_run_metadata(self):
        client = Client()
        with self.assertRaises(ValueError):
            client.build_docker_image_from_try_run_metadata({}, lambda msg, level: None)

    def test_fails_without_uuid(self):
        client = Client()
        with self.assertRaises(ValueError):
            client.build_docker_image_from_try_run_metadata({"try_run_metadata": {}}, lambda msg, level: None)

    def test_builds_docker_image_from_repository_root_submission(self):
        client = self._client_with_mocks("some-uuid-1")

        docker_tag = client.build_docker_image_from_try_run_metadata(
            {"try_run_metadata": {"uuid": "some-uuid-1"}}, lambda msg, level: None
        )

        self.assertTrue(docker_tag.startswith("compiled-from-code-"))
        client.local_execution.build_docker_image.assert_called_once()
        build_dir, tag, docker_file = client.local_execution.build_docker_image.call_args[0][:3]
        self.assertEqual(tag, docker_tag)
        self.assertTrue(Path(build_dir).is_dir())
        self.assertEqual(Path(docker_file).name, "Dockerfile")
        self.assertTrue((Path(build_dir) / "Dockerfile").exists())

    def test_builds_docker_image_from_submission_in_subdirectory(self):
        client = self._client_with_mocks("some-uuid-2", source_code_directory="some-directory")

        docker_tag = client.build_docker_image_from_try_run_metadata(
            {"try_run_metadata": {"uuid": "some-uuid-2"}}, lambda msg, level: None
        )

        self.assertTrue(docker_tag.startswith("compiled-from-code-"))
        client.local_execution.build_docker_image.assert_called_once()
        build_dir = client.local_execution.build_docker_image.call_args[0][0]
        self.assertEqual(Path(build_dir).name, "some-directory")
        self.assertTrue((Path(build_dir) / "Dockerfile").exists())

    def test_fails_if_submission_metadata_yml_is_missing(self):
        submission_uuid = "some-uuid-3"
        client = Client()
        client.local_execution = MagicMock()

        def fake_download_and_extract_zip(url, target_dir, extract=True):
            upload_dir = Path(target_dir) / submission_uuid
            upload_dir.mkdir(parents=True)

        client.download_and_extract_zip = MagicMock(side_effect=fake_download_and_extract_zip)

        with self.assertRaisesRegex(ValueError, "submission-metadata.yml"):
            client.build_docker_image_from_try_run_metadata(
                {"try_run_metadata": {"uuid": submission_uuid}}, lambda msg, level: None
            )
        client.local_execution.build_docker_image.assert_not_called()

    def test_fails_if_source_code_zip_is_missing(self):
        submission_uuid = "some-uuid-4"
        client = Client()
        client.local_execution = MagicMock()

        def fake_download_and_extract_zip(url, target_dir, extract=True):
            upload_dir = Path(target_dir) / submission_uuid
            upload_dir.mkdir(parents=True)
            (upload_dir / "submission-metadata.yml").write_text(yaml.safe_dump({"source_code_directory": ""}))

        client.download_and_extract_zip = MagicMock(side_effect=fake_download_and_extract_zip)

        with self.assertRaisesRegex(ValueError, "source-code.zip"):
            client.build_docker_image_from_try_run_metadata(
                {"try_run_metadata": {"uuid": submission_uuid}}, lambda msg, level: None
            )
        client.local_execution.build_docker_image.assert_not_called()
