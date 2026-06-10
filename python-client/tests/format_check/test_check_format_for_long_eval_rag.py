import tempfile
import unittest
from pathlib import Path
from shutil import copy

import pandas as pd

from tira.check_format import IrMetadataFormat, check_format

from . import _ERROR, _OK, EMPTY_OUTPUT, JSONL_OUTPUT_VALID


def persist_run_to_file(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "generated_responses.jsonl").write_text(
        """{"metadata": {"run_id": "my-system", "type": "automatic", "narrative_id": "aa42e210a361571ff4d1fad892b75d15", "team_id": "my-team"}, "references": ["12"], "answer": [{"text": "I will next answer a query.", "citations": []}, {"text": "Therefore, we have to consider the following aspects.", "citations": []}]}
{"metadata": {"run_id": "my-system", "type": "automatic", "narrative_id": "12", "team_id": "my-team"}, "references": ["12"], "answer": [{"text": "I will next answer a query.", "citations": []}, {"text": "Therefore, we have to consider the following aspects.", "citations": []}]}
{"metadata": {"run_id": "my-system", "type": "automatic", "narrative_id": "123", "team_id": "my-team"}, "references": ["12"], "answer": [{"text": "I will next answer a query.", "citations": []}, {"text": "Therefore, we have to consider the following aspects.", "citations": []}]}"""
    )


from tira.third_party_integrations import temporary_directory


def persist_longeval_data(ir_metadata="longeval-ir-metadata/ir-metadata-rag.yml") -> Path:
    d = temporary_directory()
    copy(JSONL_OUTPUT_VALID.parent / ir_metadata, Path(d) / "ir-metadata.yml")
    persist_run_to_file(Path(d))
    return d


class TestLongEvalRAGFormat(unittest.TestCase):
    def test_error_message_on_empty_output(self):
        actual = check_format(EMPTY_OUTPUT, "LongEvalRAG")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("I expected a file ir-metadata.yml in the directory", actual[1])

    def test_incomplete_ir_metadata_file_run(self):
        input_dir = persist_longeval_data("longeval-ir-metadata/ir-metadata-incomplete.yml")
        actual = check_format(input_dir, "LongEvalRAG")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The required field tag still contains the default value ENTER_VALUE_HERE.", actual[1])
        self.assertIn("The required field actor.team still contains the default value ENTER_VALUE_HERE", actual[1])

    def test_incomplete_ir_metadata_file_run(self):
        input_dir = persist_longeval_data("longeval-ir-metadata/ir-metadata-rag-incomplete.yml")
        actual = check_format(input_dir, "LongEvalRAG")
        self.assertEqual(_ERROR, actual[0])
        self.assertIn("The required field tag still contains the default value ENTER_VALUE_HERE.", actual[1])
        self.assertIn("The required field actor.team still contains the default value ENTER_VALUE_HERE", actual[1])
        self.assertIn(
            "The required field method.retrieval.documents still contains the default value ENTER_VALUE_HERE", actual[1]
        )
        self.assertIn(
            "The required field method.generation.description still contains the default value ENTER_VALUE_HERE",
            actual[1],
        )
        self.assertIn(
            "The required field method.generation.reasoning still contains the default value ENTER_VALUE_HERE",
            actual[1],
        )
        self.assertIn(
            "The required field method.generation.agents still contains the default value ENTER_VALUE_HERE", actual[1]
        )
        self.assertIn(
            "The required field method.generation.prompt still contains the default value ENTER_VALUE_HERE", actual[1]
        )
        self.assertIn(
            "The required field method.retrieval.documents still contains the default value ENTER_VALUE_HERE", actual[1]
        )

    def test_valid_run(self):
        input_dir = persist_longeval_data()
        actual = check_format(input_dir, "LongEvalRAG")
        print(actual[1])
        self.assertEqual(_OK, actual[0])
        self.assertIn("The file ir-metadata.yml is valid.", actual[1])
        self.assertIn("The RAG run is in correct format.", actual[1])
