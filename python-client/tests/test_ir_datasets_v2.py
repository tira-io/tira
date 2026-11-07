"""Integration tests for the ``tira:`` provider of ``ir_datasets``' new (v2)
knowledge-graph API, see :mod:`tira.ir_datasets_v2`.

``ir_datasets.v2`` is, at the time of writing, still an unreleased feature
branch, so :mod:`tira.ir_datasets_v2` purposefully does not import anything
from it (see that module's docstring) -- and neither does this test. Instead,
these tests exercise the ``tira`` provider exactly the way ``ir_datasets.v2``
itself would (through its duck-typed ``Provider``/``Node``/``Table``/
``Benchmark`` contracts -- see upstream's ``ir_datasets/v2/protocols.py``),
using small local assertions/mocks in place of the real graph machinery.

A dedicated, committed ``TIRA_CACHE_DIR`` (``tests/resources/ir_datasets_v2_cache``)
already contains the archived TIRA REST API responses and the extracted
dataset of ``lsr-benchmark/tiny-example-20251002_0-training``, so these tests
run fully offline (no internet access required).
"""

import os
import unittest
from pathlib import Path

from tira.ir_datasets_v2 import TiraProvider

CACHE_DIR = Path(__file__).parent / "resources" / "ir_datasets_v2_cache"


def assert_satisfies_node_protocol(test_case, node):
    """Duck-typed stand-in for ``isinstance(node, ir_datasets.v2.protocols.Node)``
    -- checked by hand (see this package's module docstring for why) rather
    than by importing the real, unreleased ``Protocol``."""
    for attr in ("name", "type", "metadata", "qualified_name", "provider", "defined_in"):
        test_case.assertTrue(hasattr(node, attr), f"node is missing attribute {attr!r}")
    for method in ("structural_edges", "attest", "verify"):
        test_case.assertTrue(callable(getattr(node, method, None)), f"node is missing method {method!r}")
    test_case.assertEqual([], node.structural_edges())
    test_case.assertIsNone(node.attest())
    test_case.assertEqual([], node.verify({}))


def assert_satisfies_table_protocol(test_case, table):
    assert_satisfies_node_protocol(test_case, table)
    for attr in ("entity", "count", "record_type", "lookup"):
        test_case.assertTrue(hasattr(table, attr), f"table is missing attribute {attr!r}")
    test_case.assertEqual(len(table), table.count())
    test_case.assertIsInstance(table.record_type, type)


def assert_satisfies_benchmark_protocol(test_case, benchmark):
    assert_satisfies_node_protocol(test_case, benchmark)
    test_case.assertTrue(benchmark.has("docs"))
    test_case.assertTrue(benchmark.has("queries"))
    test_case.assertTrue(benchmark.has("qrels"))
    test_case.assertFalse(benchmark.has("scoreddocs"))
    test_case.assertIs(benchmark.edge("docs"), benchmark.docs)
    test_case.assertIs(benchmark.edge("queries"), benchmark.queries)
    test_case.assertIs(benchmark.edge("qrels"), benchmark.qrels)


class TestIrDatasetsV2Provider(unittest.TestCase):
    def setUp(self):
        self.previous_cache_dir = os.environ.get("TIRA_CACHE_DIR")
        os.environ["TIRA_CACHE_DIR"] = str(CACHE_DIR)
        # A fresh provider per test -- the real one (``tira.ir_datasets_v2.tira``)
        # is a long-lived singleton (it caches downloaded tables across calls,
        # by design), which would let one test's cache hide another's bugs.
        self.provider = TiraProvider()

    def tearDown(self):
        if self.previous_cache_dir is None:
            del os.environ["TIRA_CACHE_DIR"]
        else:
            os.environ["TIRA_CACHE_DIR"] = self.previous_cache_dir

    def test_provider_satisfies_the_duck_typed_provider_contract(self):
        self.assertEqual("tira", self.provider.prefix)
        self.assertTrue(callable(self.provider.load))
        self.assertEqual([], list(self.provider.discover_edges()))

    def test_full_dataset_is_loadable_via_dataset_id(self):
        dataset = self.provider.load("tira:lsr-benchmark/tiny-example-20251002_0-training")

        assert_satisfies_benchmark_protocol(self, dataset)
        assert_satisfies_table_protocol(self, dataset.docs)
        assert_satisfies_table_protocol(self, dataset.queries)
        assert_satisfies_table_protocol(self, dataset.qrels)
        self.assertEqual(8, len(dataset.docs))
        self.assertEqual(4, len(dataset.queries))
        self.assertEqual(11, len(dataset.qrels))

    def test_full_dataset_is_loadable_via_display_name(self):
        dataset = self.provider.load("tira:lsr-benchmark/tiny-example")

        assert_satisfies_benchmark_protocol(self, dataset)
        self.assertEqual(8, len(dataset.docs))
        self.assertEqual(4, len(dataset.queries))
        self.assertEqual(11, len(dataset.qrels))

    def test_display_name_and_dataset_id_share_the_same_underlying_tables(self):
        via_dataset_id = self.provider.load("tira:lsr-benchmark/tiny-example-20251002_0-training")
        via_display_name = self.provider.load("tira:lsr-benchmark/tiny-example")

        self.assertIs(via_dataset_id.docs, via_display_name.docs)
        self.assertIs(via_dataset_id.queries, via_display_name.queries)
        self.assertIs(via_dataset_id.qrels, via_display_name.qrels)

    def test_docs_facet_is_loadable_on_its_own(self):
        docs = self.provider.load("tira:lsr-benchmark/tiny-example/docs")

        assert_satisfies_table_protocol(self, docs)
        self.assertEqual("docs", docs.entity)
        self.assertEqual(8, len(docs))
        doc = next(iter(docs))
        self.assertTrue(doc.doc_id)
        self.assertTrue(doc.text)
        self.assertEqual(docs.lookup(doc.doc_id), doc)

    def test_queries_facet_is_loadable_on_its_own(self):
        queries = self.provider.load("tira:lsr-benchmark/tiny-example/queries")

        assert_satisfies_table_protocol(self, queries)
        self.assertEqual("queries", queries.entity)
        self.assertEqual(4, len(queries))
        query = next(iter(queries))
        self.assertTrue(query.query_id)
        self.assertTrue(query.text)

    def test_qrels_facet_is_loadable_on_its_own(self):
        qrels = self.provider.load("tira:lsr-benchmark/tiny-example/qrels")

        assert_satisfies_table_protocol(self, qrels)
        self.assertEqual("qrels", qrels.entity)
        self.assertEqual(11, len(qrels))
        qrel = next(iter(qrels))
        self.assertTrue(qrel.query_id)
        self.assertTrue(qrel.doc_id)

    def test_loading_an_unknown_name_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.provider.load("tira:lsr-benchmark/this-dataset-does-not-exist")

    def test_loading_a_malformed_name_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.provider.load("tira:lsr-benchmark/tiny-example/not-a-facet")
