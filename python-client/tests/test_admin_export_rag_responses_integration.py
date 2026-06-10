import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tira.admin_rag_export import build_rag_responses_aggregated_results, export_rag_responses
from tira.check_format import _fmt, check_format


class TestAdminExportRagResponsesIntegration(unittest.TestCase):
    def test_builds_expected_table_from_auto_judge_resources(self):
        resource_root = Path(__file__).parent / "resources" / "auto-judge"
        aggregated_results = build_rag_responses_aggregated_results(
            resource_root / "kiddy-rag" / "runs",
            resource_root / "kiddy-rag-evaluations",
        )

        self.assertEqual(4, len(aggregated_results["lines"]))
        self.assertEqual(
            ["teamA", "teamB", "teamC", "teamD"], [line["team_id"] for line in aggregated_results["lines"]]
        )
        self.assertEqual(["run1", "run2", "run3", "run4"], [line["run_id"] for line in aggregated_results["lines"]])

        run1 = aggregated_results["lines"][0]
        run4 = aggregated_results["lines"][-1]
        self.assertEqual(0.4, run1["ir_axioms__gen_tfc1"])
        self.assertEqual(3.52, run1["prefnugget_grounded__llama_3_1_8b_instant__avg_grade"])
        self.assertEqual(3.387857142857143, run1["prefnugget_queryonly__llama_3_1_8b_instant__avg_grade"])
        self.assertEqual(-0.45, run4["ir_axioms__gen_tfc1"])
        self.assertEqual(0.36, run4["prefnugget_grounded__llama_3_1_8b_instant__avg_grade"])

    def test_writes_valid_output_from_auto_judge_resources(self):
        resource_root = Path(__file__).parent / "resources" / "auto-judge"

        with TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            output_file = export_rag_responses(
                resource_root / "kiddy-rag" / "runs",
                resource_root / "kiddy-rag-evaluations",
                output_dir,
            )
            actual = json.loads(output_file.read_text())
            validation = check_format(output_dir, "aggregated-results.json")

        self.assertEqual(output_dir / "aggregated-results.json", output_file)
        self.assertEqual([_fmt.OK, "The agregated-results.json file has the correct format."], validation)
        self.assertEqual("RAG Response Evaluations", actual["title"])
        self.assertEqual(3, len(actual["table_headers"]) - 2)
