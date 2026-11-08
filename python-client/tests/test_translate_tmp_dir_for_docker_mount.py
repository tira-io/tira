"""Simple, self-contained examples of how translate_tmp_dir_for_docker_mount() behaves.

This is intended as a minimal demonstration of the TIRA_DOCKER_TMPDIR environment variable: it
translates the local temporary directory (tempfile.gettempdir(), i.e., normally '/tmp' unless TMPDIR is
configured differently) into a different path before it is used as the *source* of a Docker/Podman bind
mount. This is needed when tira-run itself runs inside a container (e.g., "Docker outside of Docker",
where the host's Docker socket is bind-mounted into the tira-run container): the Docker/Podman daemon
then runs on the outer host and can only mount paths that exist on that outer host, not paths inside the
tira-run container.
"""

import os
import unittest
from unittest.mock import patch

from tira.local_execution_integration import translate_tmp_dir_for_docker_mount


class TestTranslateTmpDirForDockerMount(unittest.TestCase):
    def test_path_is_unchanged_when_tira_docker_tmpdir_is_not_set(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TIRA_DOCKER_TMPDIR", None)

            actual = translate_tmp_dir_for_docker_mount("/tmp/tira-abc123")

        self.assertEqual("/tmp/tira-abc123", actual)

    def test_tmp_prefix_is_replaced_when_tira_docker_tmpdir_is_set(self):
        with (
            patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
            patch("tira.local_execution_integration.tempfile.gettempdir", return_value="/tmp"),
        ):
            actual = translate_tmp_dir_for_docker_mount("/tmp/tira-abc123")

        self.assertEqual("/host-tmp/tira-abc123", actual)

    def test_nested_paths_below_tmp_are_translated(self):
        with (
            patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
            patch("tira.local_execution_integration.tempfile.gettempdir", return_value="/tmp"),
        ):
            actual = translate_tmp_dir_for_docker_mount("/tmp/tira-abc123/nested/dir")

        self.assertEqual("/host-tmp/tira-abc123/nested/dir", actual)

    def test_path_outside_of_tmp_is_left_unchanged(self):
        with (
            patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
            patch("tira.local_execution_integration.tempfile.gettempdir", return_value="/tmp"),
        ):
            actual = translate_tmp_dir_for_docker_mount("/srv/other-dir")

        self.assertEqual("/srv/other-dir", actual)

    def test_path_that_only_shares_a_prefix_with_tmp_is_left_unchanged(self):
        # "/tmporary-data" is not below "/tmp", it just happens to start with the same characters.
        with (
            patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
            patch("tira.local_execution_integration.tempfile.gettempdir", return_value="/tmp"),
        ):
            actual = translate_tmp_dir_for_docker_mount("/tmporary-data/file.txt")

        self.assertEqual("/tmporary-data/file.txt", actual)

    def test_path_exactly_equal_to_tmp_dir_is_translated(self):
        with (
            patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
            patch("tira.local_execution_integration.tempfile.gettempdir", return_value="/tmp"),
        ):
            actual = translate_tmp_dir_for_docker_mount("/tmp")

        self.assertEqual("/host-tmp", actual)

    def test_custom_tmpdir_is_respected_via_tempfile_gettempdir(self):
        # If TMPDIR is configured to something other than '/tmp', translation is based on that value.
        with (
            patch.dict(os.environ, {"TIRA_DOCKER_TMPDIR": "/host-tmp"}),
            patch("tira.local_execution_integration.tempfile.gettempdir", return_value="/custom/tmp"),
        ):
            actual = translate_tmp_dir_for_docker_mount("/custom/tmp/tira-abc123")

        self.assertEqual("/host-tmp/tira-abc123", actual)


if __name__ == "__main__":
    unittest.main()
