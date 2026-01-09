import tempfile
import unittest
from pathlib import Path

from tira.tira_run import guess_dataset


class TestGuessDataset(unittest.TestCase):
    def test_empty_dir_does_not_yield_dataset(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            actual = guess_dataset(tmp_dir)
            self.assertIsNone(actual)

    def test_ambiguous_dataset_does_not_yield_guess(self):
        guess_from_dir = Path(__file__).parent.parent / "resources" / "valid-ir-metadata-multiple-datasets-ambiguous"
        actual = guess_dataset(guess_from_dir)
        self.assertIsNone(actual)

    def test_non_ambiguous_dataset_does_yield_guess(self):
        expected = "learned-sparse-retrieval-20250926-training"
        guess_from_dir = Path(__file__).parent.parent / "resources" / "valid-ir-metadata-multiple-datasets"
        actual = guess_dataset(guess_from_dir)
        self.assertEqual(actual, expected)

    def test_non_ambiguous_dataset_does_yield_guess_hidden(self):
        expected = "other-dataset"
        guess_from_dir = Path(__file__).parent.parent / "resources" / "valid-ir-metadata-multiple-datasets-hidden"
        actual = guess_dataset(guess_from_dir)
        self.assertEqual(actual, expected)
