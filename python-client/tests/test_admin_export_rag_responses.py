import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tira.admin_rag_export import build_rag_responses_aggregated_results, export_rag_responses
from tira.check_format import _fmt, check_format
from tira.tira_cli import parse_args


def write_run(run_file: Path, team_id: str, run_id: str, topics):
    with open(run_file, "w") as f:
        for topic_id in topics:
            f.write(
                json.dumps(
                    {
                        "metadata": {"team_id": team_id, "run_id": run_id, "topic_id": topic_id},
                        "responses": [{"text": f"response for {topic_id}", "citations": ["doc-1"]}],
                        "documents": {
                            "doc-1": {"id": "doc-1", "text": "doc", "title": "Doc", "url": "https://example.org"}
                        },
                    }
                )
                + "\n"
            )


def write_eval(eval_file: Path, lines):
    eval_file.parent.mkdir(parents=True, exist_ok=True)
    eval_file.write_text("\n".join(lines) + "\n")


class TestAdminExportRagResponses(unittest.TestCase):
    def test_parse_args_registers_export_rag_responses_command(self):
        original_argv = list(sys.argv)
        try:
            sys.argv = [
                "tira-cli",
                "admin",
                "export-rag-responses",
                "--runs",
                "runs",
                "--evals",
                "evals",
                "--output",
                "output",
            ]
            args = parse_args()
        finally:
            sys.argv = original_argv

        self.assertEqual("runs", args.runs)
        self.assertEqual("evals", args.evals)
        self.assertEqual("output", args.output)

    def test_builds_aggregated_results_from_independent_fixture(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            runs_dir = tmp / "runs"
            evals_dir = tmp / "evals"
            (runs_dir / "system-a").mkdir(parents=True)
            (runs_dir / "system-b").mkdir(parents=True)

            write_run(runs_dir / "system-a" / "run-a.jsonl", "team-a", "run-a", ["q1", "q2"])
            write_run(runs_dir / "system-b" / "run-b.jsonl", "team-b", "run-b", ["q1", "q2"])

            write_eval(
                evals_dir / "judge-one" / "results" / "scores.eval.txt",
                [
                    "run_id query_id measure value",
                    "run-a all SCORE 0.5",
                    "run-a all ALT_SCORE 0.2",
                    "run-a all THIRD_SCORE 0.15",
                    "run-b all SCORE 0.3",
                    "run-b all ALT_SCORE 0.1",
                    "run-b all THIRD_SCORE 0.05",
                ],
            )
            write_eval(
                evals_dir / "judge-two" / "results" / "second.eval.txt",
                [
                    "run_id query_id measure value",
                    "run-a all QUALITY 0.8",
                    "run-a all COVERAGE 0.4",
                    "run-a all DEPTH 0.9",
                    "run-b all QUALITY 0.7",
                    "run-b all COVERAGE 0.35",
                    "run-b all DEPTH 0.85",
                ],
            )

            actual = build_rag_responses_aggregated_results(runs_dir, evals_dir)

        self.assertEqual(
            [
                "judge_one__score",
                "judge_one__alt_score",
                "judge_one__third_score",
                "judge_two__quality",
                "judge_two__coverage",
                "judge_two__depth",
            ],
            actual["ev_keys"],
        )
        self.assertEqual(
            [
                {
                    "team_id": "team-a",
                    "run_id": "run-a",
                    "judge_one__score": 0.5,
                    "judge_one__alt_score": 0.2,
                    "judge_one__third_score": 0.15,
                    "judge_two__quality": 0.8,
                    "judge_two__coverage": 0.4,
                    "judge_two__depth": 0.9,
                },
                {
                    "team_id": "team-b",
                    "run_id": "run-b",
                    "judge_one__score": 0.3,
                    "judge_one__alt_score": 0.1,
                    "judge_one__third_score": 0.05,
                    "judge_two__quality": 0.7,
                    "judge_two__coverage": 0.35,
                    "judge_two__depth": 0.85,
                },
            ],
            actual["lines"],
        )
        self.assertEqual("RAG Response Evaluations", actual["title"])

    def test_export_rag_responses_writes_valid_aggregated_results(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            runs_dir = tmp / "runs"
            evals_dir = tmp / "evals"
            output_dir = tmp / "output"
            (runs_dir / "system-a").mkdir(parents=True)
            (runs_dir / "system-b").mkdir(parents=True)

            write_run(runs_dir / "system-a" / "run-a.jsonl", "team-a", "run-a", ["q1", "q2"])
            write_run(runs_dir / "system-b" / "run-b.jsonl", "team-b", "run-b", ["q1", "q2"])
            write_eval(
                evals_dir / "judge-one" / "results" / "scores.eval.txt",
                [
                    "run_id query_id measure value",
                    "run-a all SCORE 0.5",
                    "run-a all ALT_SCORE 0.2",
                    "run-a all THIRD_SCORE 0.15",
                    "run-b all SCORE 0.3",
                    "run-b all ALT_SCORE 0.1",
                    "run-b all THIRD_SCORE 0.05",
                ],
            )

            output_file = export_rag_responses(runs_dir, evals_dir, output_dir)
            validation = check_format(output_dir, "aggregated-results.json")

        self.assertEqual(output_dir / "aggregated-results.json", output_file)
        self.assertEqual([_fmt.OK, "The agregated-results.json file has the correct format."], validation)

    def test_raises_if_an_evaluation_misses_a_run(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            runs_dir = tmp / "runs"
            evals_dir = tmp / "evals"
            (runs_dir / "system-a").mkdir(parents=True)
            (runs_dir / "system-b").mkdir(parents=True)

            write_run(runs_dir / "system-a" / "run-a.jsonl", "team-a", "run-a", ["q1", "q2"])
            write_run(runs_dir / "system-b" / "run-b.jsonl", "team-b", "run-b", ["q1", "q2"])
            write_eval(
                evals_dir / "judge-one" / "results" / "scores.eval.txt",
                [
                    "run_id query_id measure value",
                    "run-a all SCORE 0.5",
                    "run-a all ALT_SCORE 0.2",
                    "run-a all THIRD_SCORE 0.15",
                    "run-c all SCORE 0.4",
                    "run-c all ALT_SCORE 0.25",
                    "run-c all THIRD_SCORE 0.2",
                ],
            )

            with self.assertRaises(ValueError) as ctx:
                build_rag_responses_aggregated_results(runs_dir, evals_dir)

        self.assertIn("misses ALL scores for runs ['run-b']", str(ctx.exception))
