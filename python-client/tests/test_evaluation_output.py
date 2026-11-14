import tempfile
import unittest
from pathlib import Path

from tira.evaluation_output import (
    SUPPORTED_OUTPUT_FORMATS,
    parse_evaluation_output,
    validate_output_format,
    write_evaluation_output,
)

EVALUATION = {"Ndcg": 0.5, "Queries": 3, "Name": "abc"}


class TestEvaluationOutput(unittest.TestCase):
    def test_round_trip_for_all_formats(self):
        evaluation = {"Ndcg": 0.5, "Queries": 3}
        for output_format in SUPPORTED_OUTPUT_FORMATS:
            with self.subTest(output_format), tempfile.TemporaryDirectory() as d:
                write_evaluation_output(evaluation, Path(d), output_format)
                self.assertEqual(evaluation, parse_evaluation_output(Path(d), output_format))
                self.assertEqual(evaluation, parse_evaluation_output(Path(d)))

    def test_default_is_prototext(self):
        with tempfile.TemporaryDirectory() as d:
            target = write_evaluation_output(EVALUATION, Path(d))
            self.assertEqual("evaluation.prototext", target.name)
            self.assertEqual(EVALUATION, parse_evaluation_output(Path(d)))

    def test_trec_eval_leaderboard_uses_aggregate_query(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "results.txt").write_text("run q1 ndcg 0.1\nrun all ndcg 0.5\nrun all P@10 0.25\n")
            self.assertEqual({"ndcg": 0.5, "P@10": 0.25}, parse_evaluation_output(Path(d), "trec-eval-leaderboard"))

    def test_trec_eval_leaderboard_rejects_measures_with_whitespace(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_evaluation_output({"Docs Per Query": 1}, Path(d), "trec-eval-leaderboard")

    def test_invalid_format_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_output_format("not-a-format")


class TestEvaluateWithOutputFormat(unittest.TestCase):
    def test_evaluate_writes_configured_output_format_from_trusted_eval(self):
        import pandas as pd
        from tira.evaluators import evaluate

        config = {
            "run_format": "*.jsonl",
            "run_format_configuration": {"required_field": ["id", "response"], "id_field": "id", "value_field": "response"},
            "truth_format": None,
            "measures": ["Words (Min)"],
            "trusted_eval": {"output_format": "json"},
        }
        with tempfile.TemporaryDirectory() as d:
            run, out = Path(d) / "run", Path(d) / "out"
            run.mkdir()
            out.mkdir()
            pd.DataFrame([{"id": "1", "response": "a b c"}, {"id": "2", "response": "d"}]).to_json(run / "run.jsonl", lines=True, orient="records")
            expected = evaluate(run, Path(d), config, out)

            self.assertEqual(["evaluation.json"], [i.name for i in out.iterdir()])
            self.assertEqual(expected, parse_evaluation_output(out, "json"))


class TestForwardEnvironmentVariablesOfEvaluator(unittest.TestCase):
    CONFIG = {
        "run_format": "*.jsonl",
        "run_format_configuration": {"required_field": ["id", "response"], "id_field": "id", "value_field": "response"},
        "truth_format": None,
        "measures": ["Words (Min)"],
        "trusted_eval": {"forward_environment_variable": ["TIRA_TEST_EVALUATOR_VARIABLE"]},
    }

    def test_evaluate_fails_if_forwarded_variable_is_missing(self):
        import os

        from tira.evaluators import evaluate

        os.environ.pop("TIRA_TEST_EVALUATOR_VARIABLE", None)
        with self.assertRaises(ValueError):
            evaluate(Path("."), Path("."), self.CONFIG)
