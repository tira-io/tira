import tempfile
import unittest
from pathlib import Path

import pandas as pd


def evaluate(predictions, truth_data):
    from tira.evaluators import evaluate as _eval

    config = {
        "run_format": "*.jsonl",
        "truth_format": "*.jsonl",
        "measures": ["tau_ap", "kendall", "pearson", "spearman"],
    }

    with tempfile.TemporaryDirectory() as d:
        pred_dir = Path(d) / "preds" / "preds.jsonl"
        truth_dir = Path(d) / "truth" / "truth.jsonl"

        pred_dir.parent.mkdir()
        truth_dir.parent.mkdir()

        pd.DataFrame(predictions).to_json(pred_dir, lines=True, orient="records")
        pd.DataFrame(truth_data).to_json(truth_dir, lines=True, orient="records")
        return _eval(pred_dir.parent, truth_dir.parent, config)


class TestRegressionEvaluator(unittest.TestCase):
    def test_perfect_correlation_01(self):
        expected = {"tau_ap": 1.0, "kendall": 1.0, "pearson": 1.0, "spearman": 1.0}

        predictions = [
            {"id": "1", "probability_relevant": 2},
            {"id": "2", "probability_relevant": 1},
            {"id": "3", "probability_relevant": 3},
            {"id": "4", "probability_relevant": 1},
            {"id": "5", "probability_relevant": 1},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "unknown_doc_id": "d-2", "qrel_unknown_doc": 1},
            {"id": "3", "query_id": "qid-1", "unknown_doc_id": "d-3", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "unknown_doc_id": "d-4", "qrel_unknown_doc": 1},
            {"id": "5", "query_id": "qid-1", "unknown_doc_id": "d-5", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_perfect_correlation_01_for_df(self):
        expected = {"tau_ap": 1.0, "kendall": 1.0, "pearson": 1.0, "spearman": 1.0}

        predictions = pd.DataFrame(
            [
                {"id": "1", "probability_relevant": 2},
                {"id": "2", "probability_relevant": 1},
                {"id": "3", "probability_relevant": 3},
                {"id": "4", "probability_relevant": 1},
                {"id": "5", "probability_relevant": 1},
            ]
        )
        truth_data = [
            {"id": "1", "query_id": "qid-1", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "unknown_doc_id": "d-2", "qrel_unknown_doc": 1},
            {"id": "3", "query_id": "qid-1", "unknown_doc_id": "d-3", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "unknown_doc_id": "d-4", "qrel_unknown_doc": 1},
            {"id": "5", "query_id": "qid-1", "unknown_doc_id": "d-5", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_perfect_correlation_02(self):
        expected = {"tau_ap": 1.0, "kendall": 1.0, "pearson": 1.0, "spearman": 1.0}

        predictions = [
            {"id": "1", "probability_relevant": 0.2},
            {"id": "2", "probability_relevant": 0.1},
            {"id": "3", "probability_relevant": 0.3},
            {"id": "4", "probability_relevant": 0.1},
            {"id": "5", "probability_relevant": 0.1},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "unknown_doc_id": "d-2", "qrel_unknown_doc": 1},
            {"id": "3", "query_id": "qid-1", "unknown_doc_id": "d-3", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "unknown_doc_id": "d-4", "qrel_unknown_doc": 1},
            {"id": "5", "query_id": "qid-1", "unknown_doc_id": "d-5", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_perfect_correlation_03(self):
        expected = {"tau_ap": 1.0, "kendall": 1.0, "pearson": 1.0, "spearman": 1.0}

        predictions = [
            {"id": "1", "probability_relevant": 10.2},
            {"id": "2", "probability_relevant": 10.1},
            {"id": "3", "probability_relevant": 10.3},
            {"id": "4", "probability_relevant": 10.1},
            {"id": "5", "probability_relevant": 10.1},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "unknown_doc_id": "d-2", "qrel_unknown_doc": 1},
            {"id": "3", "query_id": "qid-1", "unknown_doc_id": "d-3", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "unknown_doc_id": "d-4", "qrel_unknown_doc": 1},
            {"id": "5", "query_id": "qid-1", "unknown_doc_id": "d-5", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_perfect_inverse_correlation_01(self):
        expected = {"tau_ap": 0.0, "kendall": -0.39999999, "pearson": -0.6, "spearman": -0.6}

        predictions = [
            {"id": "1", "probability_relevant": -2},
            {"id": "2", "probability_relevant": -1},
            {"id": "3", "probability_relevant": -3},
            {"id": "4", "probability_relevant": -1},
            {"id": "5", "probability_relevant": -1},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "unknown_doc_id": "d-2", "qrel_unknown_doc": 1},
            {"id": "3", "query_id": "qid-1", "unknown_doc_id": "d-3", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "unknown_doc_id": "d-4", "qrel_unknown_doc": 1},
            {"id": "5", "query_id": "qid-1", "unknown_doc_id": "d-5", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_perfect_inverse_correlation_02(self):
        expected = {"tau_ap": 0.0, "kendall": -0.39999999, "pearson": -0.6, "spearman": -0.6}

        predictions = [
            {"id": "1", "probability_relevant": -0.2},
            {"id": "2", "probability_relevant": -0.1},
            {"id": "3", "probability_relevant": -0.3},
            {"id": "4", "probability_relevant": -0.1},
            {"id": "5", "probability_relevant": -0.1},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "unknown_doc_id": "d-2", "qrel_unknown_doc": 1},
            {"id": "3", "query_id": "qid-1", "unknown_doc_id": "d-3", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "unknown_doc_id": "d-4", "qrel_unknown_doc": 1},
            {"id": "5", "query_id": "qid-1", "unknown_doc_id": "d-5", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_pairwise_perfect_correlation_01(self):
        expected = {"tau_ap": 1.0, "kendall": 1.0, "pearson": 1.0, "spearman": 1.0}

        predictions = [
            {"id": "1", "probability_relevant": 2},
            {"id": "2", "probability_relevant": 2},
            {"id": "3", "probability_relevant": 3},
            {"id": "4", "probability_relevant": 3},
            {"id": "5", "probability_relevant": 1},
            {"id": "6", "probability_relevant": 1},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "3", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "5", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
            {"id": "6", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_pairwise_perfect_correlation_02(self):
        expected = {"tau_ap": 1.0, "kendall": 1.0, "pearson": 1.0, "spearman": 1.0}

        predictions = [
            {"id": "1", "probability_relevant": 20},
            {"id": "2", "probability_relevant": 20},
            {"id": "3", "probability_relevant": 30},
            {"id": "4", "probability_relevant": 30},
            {"id": "5", "probability_relevant": 10},
            {"id": "6", "probability_relevant": 10},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "3", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "5", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
            {"id": "6", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_pairwise_non_perfect_correlation_01(self):
        expected = {"tau_ap": 0.5, "kendall": 0.33333333333, "pearson": 0.5, "spearman": 0.5}

        predictions = [
            {"id": "1", "probability_relevant": 20},
            {"id": "2", "probability_relevant": 20},
            {"id": "3", "probability_relevant": 30},
            {"id": "4", "probability_relevant": 30},
            {"id": "5", "probability_relevant": 21},
            {"id": "6", "probability_relevant": 21},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "3", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "5", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
            {"id": "6", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_pairwise_non_perfect_correlation_02(self):
        expected = {"tau_ap": 0.5, "kendall": 0.33333333333, "pearson": 0.5, "spearman": 0.5}

        predictions = [
            {"id": "1", "probability_relevant": 1},
            {"id": "2", "probability_relevant": 1},
            {"id": "3", "probability_relevant": 3},
            {"id": "4", "probability_relevant": 3},
            {"id": "5", "probability_relevant": 2},
            {"id": "6", "probability_relevant": 2},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "3", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "5", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
            {"id": "6", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)

    def test_least_non_perfect_correlation_01(self):
        expected = {"tau_ap": -0.5, "kendall": -0.33333333333, "pearson": -0.5, "spearman": -0.5}

        predictions = [
            {"id": "1", "probability_relevant": 1},
            {"id": "2", "probability_relevant": 1},
            {"id": "3", "probability_relevant": 2},
            {"id": "4", "probability_relevant": 2},
            {"id": "5", "probability_relevant": 3},
            {"id": "6", "probability_relevant": 3},
        ]
        truth_data = [
            {"id": "1", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "2", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-1", "qrel_unknown_doc": 2},
            {"id": "3", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "4", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-2", "qrel_unknown_doc": 3},
            {"id": "5", "query_id": "qid-1", "relevant_doc_id": "a", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
            {"id": "6", "query_id": "qid-1", "relevant_doc_id": "b", "unknown_doc_id": "d-3", "qrel_unknown_doc": 1},
        ]

        actual = evaluate(predictions, truth_data)
        for k in expected:
            self.assertAlmostEqual(expected[k], actual[k], delta=0.00001, msg=k)
