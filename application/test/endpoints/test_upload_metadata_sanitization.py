import ast
import json
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

from tira.io_utils import sanitize_text


def _load_function(path: Path, function_name: str, namespace: dict[str, Any]):
    module = ast.parse(path.read_text())
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == function_name)
    function_module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(function_module)
    exec(compile(function_module, str(path), "exec"), namespace)
    return namespace[function_name]


model_path = Path(__file__).resolve().parents[2] / "src" / "tira_app" / "model.py"
normalize_upload_metadata = _load_function(
    model_path,
    "normalize_upload_metadata",
    {"Any": Any, "Dict": Dict, "Optional": Optional, "json": json},
)

vm_api_path = Path(__file__).resolve().parents[2] / "src" / "tira_app" / "endpoints" / "vm_api.py"
_sanitize_upload_metadata = _load_function(
    vm_api_path,
    "_sanitize_upload_metadata",
    {
        "Any": Any,
        "Optional": Optional,
        "normalize_upload_metadata": normalize_upload_metadata,
        "sanitize_text": sanitize_text,
    },
)


class TestUploadMetadataSanitization(unittest.TestCase):
    def test_returns_none_for_empty_upload_metadata(self):
        self.assertIsNone(_sanitize_upload_metadata(None))

    def test_sanitizes_upload_metadata_values_from_json(self):
        actual = _sanitize_upload_metadata('{"run_id": "hello ∑ world", "description": "hello world"}')

        self.assertEqual({"run_id": "hello  world", "description": "hello world"}, actual)
