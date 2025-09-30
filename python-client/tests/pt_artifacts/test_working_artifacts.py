import os
import tempfile
import unittest
import warnings
from pathlib import Path

import pandas as pd
import pyterrier as pt
import pyterrier_alpha as pta

from tira.pyterrier_util import TiraSourceTransformer

from . import load_artifact


class TestWorkingArtifacts(unittest.TestCase):
    def test_bm25_artifact(self):
        expected = {
            "qid": "51",
            "docno": "S885c6b4f-Ad3259e81",
            "rank": 1,
            "score": 26.07818108898493,
            "name": "pyterrier.default_pipelines.wmodel_batch_retrieve",
        }
        bm25 = load_artifact(
            "tira:argsme/2020-04-01/touche-2021-task-1/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)"
        )

        run = bm25.transform(pd.DataFrame([{"qid": "51"}]))
        actual = run.iloc[0].to_dict()
        self.assertEqual(expected, actual)

    def test_hyb_a_query_segmentation_artifact(self):
        expected = ["should", "blood donations", "be financially compensated"]
        hyb_a = load_artifact("tira:argsme/2020-04-01/touche-2021-task-1/ows/query-segmentation-hyb-a")

        self.assertIsNotNone(hyb_a)
        actual = hyb_a.transform(pd.DataFrame([{"qid": "53"}])).iloc[0].to_dict()
        self.assertIn("segmentation", actual)
        self.assertEqual(expected, actual["segmentation"])

    def test_doc_t5_query_artifact(self):
        expected = "including fluid motion"
        docT5Query = load_artifact("tira:cranfield/seanmacavaney/DocT5Query (Local)")

        self.assertIsNotNone(docT5Query)
        actual = docT5Query.transform(pd.DataFrame([{"docno": "873"}])).iloc[0].to_dict()
        self.assertIn("text", actual)
        self.assertIn(expected, actual["text"])

    def test_index_artifact(self):
        import pyterrier as pt

        index = load_artifact("tira:cranfield/tira-ir-starter/Index (tira-ir-starter-pyterrier)")

        self.assertIn("IndexRef", str(index))
        run = pt.terrier.Retriever(index).search("chemical reactions")
        actual = run.iloc[0].to_dict()
        self.assertIsNotNone(actual)
        self.assertEqual("488", actual["docno"])

    def test_artifact_is_tira_source_transformer(self):
        """Test that retriever-artifacts loaded from TIRA URLs are TiraSourceTransformer instances"""
        # Test with a BM25 artifact
        art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")
        self.assertIsInstance(art, TiraSourceTransformer)

    def test_non_artifact_is_regular_source_transformer(self):
        """Test that local run files create regular SourceTransformer, not TiraSourceTransformer"""
        # Create a temporary run file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write sample TREC run format data
            f.write("1 Q0 doc1 1 10.0 system\n")
            f.write("1 Q0 doc2 2 9.0 system\n")
            f.write("2 Q0 doc3 1 8.0 system\n")
            temp_run_file = f.name

        try:
            # Load as regular PyTerrier dataframe and transformer
            live_df = pt.io.read_results(temp_run_file)
            live_tr = pt.Transformer.from_df(live_df)

            # Should be SourceTransformer but NOT TiraSourceTransformer
            self.assertIsInstance(live_tr, pt.transformer.SourceTransformer)
            self.assertNotIsInstance(live_tr, TiraSourceTransformer)
        finally:
            # Clean up temp file
            os.unlink(temp_run_file)

    def test_on_column_mismatch_warn(self):
        """Test that on_column_mismatch='warn' produces warnings for extra query columns"""
        art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")

        # Create topics with extra query rewrite columns
        topics = pd.DataFrame(
            [{"qid": "1", "query": "test query", "query_0": "rewritten query 1", "query_1": "rewritten query 2"}]
        )

        # Should warn by default
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            art.transform(topics)

            # Check that a warning was issued
            self.assertTrue(len(w) > 0)
            warning_msg = str(w[0].message)
            self.assertIn("cannot process rewritten query columns", warning_msg)
            self.assertIn("will be ignored during retrieval", warning_msg)

    def test_on_column_mismatch_error(self):
        """Test that on_column_mismatch='error' raises an error for extra query columns"""
        # Create artifact with error mode
        art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")
        art.on_column_mismatch = "error"

        # Create topics with extra query rewrite columns
        topics = pd.DataFrame([{"qid": "1", "query": "test query", "query_0": "rewritten query 1"}])

        # Should raise ValueError
        with self.assertRaises(ValueError) as cm:
            art.transform(topics)

        error_msg = str(cm.exception)
        self.assertIn("may not be the intended behavior", error_msg)

    def test_on_column_mismatch_ignore(self):
        """Test that on_column_mismatch='ignore' silently ignores extra query columns"""
        # Create artifact with ignore mode
        art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")
        art.on_column_mismatch = "ignore"

        # Create topics with extra query rewrite columns
        topics = pd.DataFrame([{"qid": "1", "query": "test query", "query_0": "rewritten query 1"}])

        # Should not warn or error
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            art.transform(topics)

            # Check that no warnings were issued about column mismatch
            column_warnings = [warning for warning in w if "ignores rewritten queries" in str(warning.message)]
            self.assertEqual(len(column_warnings), 0)

    def test_on_column_mismatch_default_behavior(self):
        """Test that the default on_column_mismatch behavior is 'warn'"""
        art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")

        # Check that default is 'warn'
        self.assertEqual(art.on_column_mismatch, "warn")

    def test_env_var_changes_default(self):
        """
        If TIRA_ARTIFACT_ON_REWRITE is set, every artifact loaded via pta.Artifact.from_url
        should inherit that mode automatically.
        """
        import os
        from unittest.mock import patch

        # env-var override using patch
        with patch.dict(os.environ, {"TIRA_ARTIFACT_ON_COLUMN_MISMATCH": "error"}):
            # Load artifact - should inherit the environment variable setting
            art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")

            self.assertEqual(art.on_column_mismatch, "error")

    def test_get_metadata_transformer_artifact(self):
        """Test that transformer artifacts have get_metadata() method that returns correct data"""
        art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)")

        # Should have get_metadata method
        self.assertTrue(hasattr(art, "get_metadata"))
        self.assertTrue(callable(art.get_metadata))

        # Should return metadata dict
        metadata = art.get_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("type"), "tira")
        self.assertEqual(metadata.get("format"), "pt_transformer")

    def test_get_metadata_index_artifact(self):
        """Test that index artifacts have get_metadata() method that returns correct data"""
        art = pta.Artifact.from_url("tira:cranfield/tira-ir-starter/Index (tira-ir-starter-pyterrier)")

        # Should have get_metadata method
        self.assertTrue(hasattr(art, "get_metadata"))
        self.assertTrue(callable(art.get_metadata))

        # Should return metadata dict
        metadata = art.get_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("type"), "tira")
        self.assertEqual(metadata.get("format"), "pt_index_transformer")

    def test_get_metadata_query_transformer_artifact(self):
        """Test that query transformer artifacts have get_metadata() method that returns correct data"""
        art = pta.Artifact.from_url("tira:cranfield/qspell/hunspell")

        # Should have get_metadata method
        self.assertTrue(hasattr(art, "get_metadata"))
        self.assertTrue(callable(art.get_metadata))

        # Should return metadata dict
        metadata = art.get_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("type"), "tira")
        self.assertEqual(metadata.get("format"), "pt_query_transformer")

    def test_get_metadata_document_transformer_artifact(self):
        """Test that document transformer artifacts have get_metadata() method that returns correct data"""
        art = pta.Artifact.from_url("tira:cranfield/seanmacavaney/DocT5Query (Local)")

        # Should have get_metadata method
        self.assertTrue(hasattr(art, "get_metadata"))
        self.assertTrue(callable(art.get_metadata))

        # Should return metadata dict
        metadata = art.get_metadata()
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("type"), "tira")
        self.assertEqual(metadata.get("format"), "pt_document_transformer")

    def test_local_bm25_artifact_from_file(self):
        expected = {
            "qid": "3",
            "docno": "doc-3",
            "rank": 1,
            "score": 1.0,
            "name": "tag",
        }
        bm25 = load_artifact(
            "tira:" + str((Path(__file__).parent.parent / "resources" / "ranking-outputs" / "run.txt").absolute())
        )

        run = bm25.transform(pd.DataFrame([{"qid": "3"}]))
        print(run)
        actual = run.iloc[0].to_dict()
        self.assertEqual(expected, actual)

    def test_local_bm25_artifact_from_dir(self):
        expected = {
            "qid": "3",
            "docno": "doc-3",
            "rank": 1,
            "score": 1.0,
            "name": "tag",
        }
        bm25 = load_artifact("tira:" + str((Path(__file__).parent.parent / "resources" / "ranking-outputs").absolute()))

        run = bm25.transform(pd.DataFrame([{"qid": "3"}]))
        print(run)
        actual = run.iloc[0].to_dict()
        self.assertEqual(expected, actual)
