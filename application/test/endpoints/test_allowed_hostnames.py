import ast
import json
import unittest
from pathlib import Path
from typing import Any, List, Optional


def _load_function(path: Path, function_name: str, namespace: dict[str, Any]):
    module = ast.parse(path.read_text())
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == function_name)
    function_module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(function_module)
    exec(compile(function_module, str(path), "exec"), namespace)
    return namespace[function_name]


model_path = Path(__file__).resolve().parents[2] / "src" / "tira_app" / "model.py"
normalize_allowed_hostnames = _load_function(
    model_path,
    "normalize_allowed_hostnames",
    {"Any": Any, "List": List, "Optional": Optional, "json": json},
)

vm_api_path = Path(__file__).resolve().parents[2] / "src" / "tira_app" / "endpoints" / "vm_api.py"
_disallowed_hostnames = _load_function(
    vm_api_path,
    "_disallowed_hostnames",
    {"List": List, "Optional": Optional},
)


class TestNormalizeAllowedHostnames(unittest.TestCase):
    def test_returns_none_for_none(self):
        self.assertIsNone(normalize_allowed_hostnames(None))

    def test_returns_none_for_empty_string(self):
        self.assertIsNone(normalize_allowed_hostnames(""))

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(normalize_allowed_hostnames("not-valid-json"))

    def test_returns_none_for_non_list_json(self):
        self.assertIsNone(normalize_allowed_hostnames('{"a": "b"}'))

    def test_returns_none_for_list_with_non_string_entries(self):
        self.assertIsNone(normalize_allowed_hostnames(["api.openai.com", 42]))

    def test_returns_none_for_list_with_blank_entries(self):
        self.assertIsNone(normalize_allowed_hostnames(["api.openai.com", "  "]))

    def test_returns_none_for_empty_list(self):
        self.assertIsNone(normalize_allowed_hostnames([]))

    def test_normalizes_hostnames_from_list(self):
        self.assertEqual(
            ["api.openai.com", "example.com"], normalize_allowed_hostnames(["api.openai.com", "example.com"])
        )

    def test_strips_whitespace_from_hostnames(self):
        self.assertEqual(["api.openai.com"], normalize_allowed_hostnames([" api.openai.com "]))

    def test_normalizes_hostnames_from_json_string(self):
        self.assertEqual(["api.openai.com"], normalize_allowed_hostnames('["api.openai.com"]'))


class TestDisallowedHostnames(unittest.TestCase):
    def test_no_hostnames_required_passes_with_no_allowlist(self):
        self.assertEqual([], _disallowed_hostnames([], None))

    def test_no_hostnames_required_passes_with_empty_allowlist(self):
        self.assertEqual([], _disallowed_hostnames(None, []))

    def test_required_hostname_missing_when_allowlist_is_none(self):
        self.assertEqual(["api.openai.com"], _disallowed_hostnames(["api.openai.com"], None))

    def test_required_hostname_missing_when_allowlist_is_empty(self):
        self.assertEqual(["api.openai.com"], _disallowed_hostnames(["api.openai.com"], []))

    def test_required_hostname_present_in_allowlist(self):
        self.assertEqual([], _disallowed_hostnames(["api.openai.com"], ["api.openai.com", "example.com"]))

    def test_required_hostname_not_in_allowlist(self):
        self.assertEqual(["evil.example.com"], _disallowed_hostnames(["evil.example.com"], ["api.openai.com"]))

    def test_multiple_required_hostnames_partially_allowed(self):
        self.assertEqual(
            ["evil.example.com"],
            _disallowed_hostnames(["api.openai.com", "evil.example.com"], ["api.openai.com"]),
        )


if __name__ == "__main__":
    unittest.main()
