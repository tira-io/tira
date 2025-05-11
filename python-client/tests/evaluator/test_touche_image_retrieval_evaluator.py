import tempfile
import unittest
from os import listdir
from pathlib import Path
from shutil import copy

from tests.format_check import EMPTY_OUTPUT, TOUCHE_IMAGE_RETRIEVAL
from tira.evaluators import evaluate as _eval


class TestToucheImageRetrievalEvaluators(unittest.TestCase):

    def test_evaluate_docs_per_query_01(self):
        expected = {
            "Docs Per Query (Avg)": 1,
            "Docs Per Query (Min)": 1,
            "Docs Per Query (Max)": 1,
            "NumQueries": 3,
        }
        actual = _eval(
            TOUCHE_IMAGE_RETRIEVAL,
            EMPTY_OUTPUT,
            {
                "run_format": "touche-image-retrieval",
                "truth_format": None,
                "measures": ["Docs Per Query (Avg)", "Docs Per Query (Min)", "Docs Per Query (Max)", "NumQueries"],
            },
        )

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)

    def test_evaluate_docs_per_query_02(self):
        expected = {
            "Docs Per Query (Avg)": 1,
            "Docs Per Query (Min)": 1,
            "Docs Per Query (Max)": 1,
            "NumQueries": 3,
        }
        actual = _eval(
            TOUCHE_IMAGE_RETRIEVAL,
            EMPTY_OUTPUT,
            {
                "run_format": ["touche-image-retrieval"],
                "truth_format": None,
                "measures": ["Docs Per Query (Avg)", "Docs Per Query (Min)", "Docs Per Query (Max)", "NumQueries"],
            },
        )

        self.assertEqual(expected.keys(), actual.keys())
        for k, v in expected.items():
            self.assertAlmostEqual(v, actual[k], delta=0.0001)
