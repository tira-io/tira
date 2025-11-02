import tempfile
import unittest
from typing import Dict

import yaml

from tira.io_utils import patch_ir_metadata


def patch(original_dict: Dict, src_pattern: Dict, target_pattern: Dict):
    with tempfile.TemporaryDirectory() as tmp_dir:
        additional_fields = ["platform", "implementation", "resources"]
        ret = str(tmp_dir) + "/foo.yml"
        original_dict = original_dict.copy()
        for f in additional_fields:
            original_dict[f] = ""
        yaml.safe_dump(original_dict, open(ret, "w"))
        patch_ir_metadata(str(tmp_dir), src_pattern, target_pattern)
        ret = yaml.safe_load(open(ret))
        for f in additional_fields:
            del ret[f]
        return ret


class TestPatchIrMetadata(unittest.TestCase):
    def test_does_nothing_01(self):
        actual = patch(
            {"hello": "world"},
            {"does-not-exist": "a"},
            {"does-not-exist": "b"},
        )
        self.assertEqual({"hello": "world"}, actual)

    def test_does_nothing_02(self):
        src_pattern = {"data": {"test collection": {"name": "foo-1"}}}
        target_pattern = {"data": {"test collection": {"name": "foo-2"}}}

        actual = patch({"hello": "world"}, src_pattern, target_pattern)
        self.assertEqual({"hello": "world"}, actual)

    def test_does_nothing_03(self):
        src_pattern = {"data": {"test collection": {"name": "foo-1"}}}
        target_pattern = {"data": {"test collection": {"name": "foo-2"}}}

        actual = patch(
            {"hello": "world", "data": {"test collection": {"name": "some-test-collection"}}},
            src_pattern,
            target_pattern,
        )
        self.assertEqual(
            {
                "hello": "world",
                "data": {"test collection": {"name": "some-test-collection"}},
            },
            actual,
        )

    def test_patch_works(self):
        src_pattern = {"data": {"test collection": {"name": "foo-1"}}}
        target_pattern = {"data": {"test collection": {"name": "foo-2"}}}

        actual = patch(
            {"hello": "world", "data": {"test collection": {"name": "foo-1"}}},
            src_pattern,
            target_pattern,
        )
        self.assertEqual(
            {
                "hello": "world",
                "data": {"test collection": {"name": "foo-2"}},
            },
            actual,
        )
