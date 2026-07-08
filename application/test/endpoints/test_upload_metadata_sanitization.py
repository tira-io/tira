import ast
import json
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

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
normalize_upload_form_fields = _load_function(
    model_path,
    "normalize_upload_form_fields",
    {"Any": Any, "Dict": Dict, "List": List, "Optional": Optional, "json": json},
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


class TestUploadFormFieldNormalization(unittest.TestCase):
    def test_normalizes_select_upload_field_options(self):
        actual = normalize_upload_form_fields(
            [
                {
                    "name": "track",
                    "display_name": "Track",
                    "type": "select",
                    "options": [
                        {"id": " main ", "display_value": " Main Track "},
                        {"id": "bio", "display_value": "Biomedical Track"},
                    ],
                }
            ]
        )

        self.assertEqual(
            [
                {
                    "name": "track",
                    "display_name": "Track",
                    "type": "select",
                    "options": [
                        {"id": "main", "display_value": "Main Track"},
                        {"id": "bio", "display_value": "Biomedical Track"},
                    ],
                }
            ],
            actual,
        )

    def test_rejects_select_upload_fields_without_options(self):
        actual = normalize_upload_form_fields(
            [{"name": "track", "display_name": "Track", "type": "select", "options": []}]
        )

        self.assertIsNone(actual)
