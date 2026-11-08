"""End-to-end check that the ``tira`` provider is actually discoverable and
loadable through a *real* ``ir_datasets.v2`` installation, via the
``ir_datasets.providers`` entry point declared in ``setup.cfg``.

Unlike ``tests/test_ir_datasets_v2.py`` (which deliberately never imports
``ir_datasets.v2`` -- see that module's docstring, and
:mod:`tira.ir_datasets_v2`'s), this test does import it, so it only runs when
an ``ir_datasets`` with a ``v2`` subpackage is actually installed (still an
unreleased feature branch at the time of writing -- see
``.github/workflows/ir-datasets-v2.yml``, which installs it from
``ir-datasets/ir-datasets@v2`` to run this). It is skipped otherwise, so a
regular install (plain, released ``ir_datasets``) is unaffected.
"""

import os
import unittest
from pathlib import Path

try:
    import ir_datasets.v2 as ir_datasets_v2

    IR_DATASETS_V2_AVAILABLE = True
except ImportError:
    IR_DATASETS_V2_AVAILABLE = False

CACHE_DIR = Path(__file__).parent / "resources" / "ir_datasets_v2_cache"


@unittest.skipUnless(IR_DATASETS_V2_AVAILABLE, "needs an ir_datasets with a v2 subpackage installed")
class TestIrDatasetsV2Entrypoint(unittest.TestCase):
    def setUp(self):
        self.previous_cache_dir = os.environ.get("TIRA_CACHE_DIR")
        os.environ["TIRA_CACHE_DIR"] = str(CACHE_DIR)

    def tearDown(self):
        if self.previous_cache_dir is None:
            del os.environ["TIRA_CACHE_DIR"]
        else:
            os.environ["TIRA_CACHE_DIR"] = self.previous_cache_dir

    def test_tira_provider_is_discovered_via_the_entry_point(self):
        self.assertIn("tira", ir_datasets_v2.default_graph().providers)

    def test_full_dataset_is_loadable_via_dataset_id(self):
        dataset = ir_datasets_v2.load("tira:lsr-benchmark/tiny-example-20251002_0-training")

        self.assertEqual(8, len(dataset.docs))
        self.assertEqual(4, len(dataset.queries))
        self.assertEqual(11, len(dataset.qrels))

    def test_full_dataset_is_loadable_via_display_name(self):
        dataset = ir_datasets_v2.load("tira:lsr-benchmark/tiny-example")

        self.assertEqual(8, len(dataset.docs))
        self.assertEqual(4, len(dataset.queries))
        self.assertEqual(11, len(dataset.qrels))

    def test_docs_facet_is_loadable_on_its_own(self):
        self.assertEqual(8, len(ir_datasets_v2.load("tira:lsr-benchmark/tiny-example/docs")))

    def test_queries_facet_is_loadable_on_its_own(self):
        self.assertEqual(4, len(ir_datasets_v2.load("tira:lsr-benchmark/tiny-example/queries")))

    def test_qrels_facet_is_loadable_on_its_own(self):
        self.assertEqual(11, len(ir_datasets_v2.load("tira:lsr-benchmark/tiny-example/qrels")))
