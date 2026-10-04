"""A ``tira:`` provider for ``ir_datasets``' new (v2) knowledge-graph API
(``ir_datasets.v2.load``), see <https://github.com/allenai/ir_datasets>
(``ir_datasets/v2``) for that API's own design (``Node``/``Table``/
``Benchmark``/``Provider``).

Importantly, this module does **not** import anything from ``ir_datasets.v2``
itself: that API is, at the time of writing, still an unreleased feature
branch, so this module must keep working (and must be importable) whether or
not an ``ir_datasets`` with a ``v2`` subpackage is installed at all. Instead,
the classes below satisfy v2's node/provider contracts purely by duck typing
-- see ``ir_datasets/v2/protocols.py`` upstream: a ``Node``/``Table``/
``Benchmark``/``Provider`` is *any* object with the right attributes and
methods, never a required base class. ``ir_datasets.v2`` only ever touches a
provider/node through that shape (plus, for entry-point discovery, through
``importlib.metadata`` loading the ``tira`` object below -- see the
``ir_datasets.providers`` entry point in ``setup.cfg``), so this still joins
its graph like any in-tree provider, without this package needing to import
or depend on it.

Naming mirrors TIRA's own ``<task>/<dataset>`` identifiers, with an optional
``/docs``, ``/queries`` or ``/qrels`` suffix for one facet on its own::

    tira:lsr-benchmark/tiny-example-20251002_0-training          a Benchmark
    tira:lsr-benchmark/tiny-example-20251002_0-training/docs     its docs Table
    tira:lsr-benchmark/tiny-example-20251002_0-training/queries  its queries Table
    tira:lsr-benchmark/tiny-example-20251002_0-training/qrels    its qrels Table

A dataset's TIRA ``display_name`` (the stable, date-suffix-free name shown on
tira.io) is also accepted in place of its full ``dataset_id`` -- so
``tira:lsr-benchmark/tiny-example`` resolves to whichever dataset in the
``lsr-benchmark`` task currently has ``display_name == 'tiny-example'`` (the
most recently created one, if more than one ever matches), sharing the same
underlying docs/queries/qrels (downloaded/parsed only once) as its full
dataset id.

Downloads go through :class:`tira.rest_api_client.Client`, so they honor
``TIRA_CACHE_DIR`` (and its offline-replay cache, ``.archived/...`` under it)
exactly like every other TIRA integration. Record parsing reuses the existing
v1-style handlers already built in :mod:`tira.ir_datasets_util`
(``DynamicDocs``/``DynamicQueries``/``QrelsFromTira``), which do depend on
``ir_datasets`` itself (the released, v1 package) -- just not on its v2
subpackage.
"""

import itertools

from tira.ir_datasets_util import ir_dataset_from_tira_fallback_to_original_ir_datasets
from tira.rest_api_client import Client as RestClient

#: v1-style doc/query/qrels handler builders (``lazy_docs``/``lazy_queries``/
#: ``lazy_qrels``), already built in ``ir_datasets_util.py`` -- reused as-is,
#: wrapped below into the duck-typed v2 node shape.
_loader = ir_dataset_from_tira_fallback_to_original_ir_datasets()

#: The id field each facet's records carry, used by ``_Table.lookup``.
_ID_FIELD = {"docs": "doc_id", "queries": "query_id", "qrels": "query_id"}


class _Node:
    """The minimal shape ``ir_datasets.v2`` expects of every graph node (see
    ``ir_datasets/v2/protocols.py::Node`` upstream) -- plain attributes plus
    three methods, none of which this (live, not frozen/verifiable) provider
    has anything useful to say about beyond these no-op defaults."""

    def __init__(self, name, type, metadata=None):
        self.name = name
        self.type = type
        self.metadata = metadata or {}
        # Assigned by a real ir_datasets.v2 Provider.register(), if this node
        # is ever handed to one; left unset (None) otherwise.
        self.qualified_name = None
        self.provider = None
        self.defined_in = None

    def structural_edges(self):
        # No frozen Resource this table/benchmark was built from -- it comes
        # from a live API call instead, like ir_datasets.v2's own "hf"/
        # "clirmatrix" providers.
        return []

    def attest(self, *, verify=False, **options):
        return None

    def verify(self, frozen, **options):
        return []


class _Table(_Node):
    """Duck-typed ``ir_datasets.v2`` ``Table`` (see
    ``ir_datasets/v2/protocols.py::Table`` upstream), wrapping one of
    :mod:`tira.ir_datasets_util`'s v1-style handler objects (``DynamicDocs``,
    ``DynamicQueries``, ``QrelsFromTira``)."""

    def __init__(self, name, entity, handler, desc=None):
        super().__init__(name, type=f"tira:{entity}", metadata={"desc": desc} if desc else {})
        self.entity = entity
        self._handler = handler

    def __getattr__(self, attr):
        # `table.docs is table` (for whichever entity this table itself is)
        # -- so a bare Table is a drop-in wherever a Benchmark facet
        # (`.docs`, `.queries`, `.qrels`) is expected, mirroring upstream's
        # own Table.__getattr__.
        if attr == self.__dict__.get("entity"):
            return self
        raise AttributeError(attr)

    def _iter(self):
        return getattr(self._handler, f"{self.entity}_iter")()

    def __iter__(self):
        return iter(self._iter())

    def __len__(self):
        return self.count()

    def __getitem__(self, key):
        if isinstance(key, slice):
            return list(itertools.islice(self._iter(), key.start, key.stop, key.step))
        if key < 0:
            raise IndexError(key)
        try:
            return next(itertools.islice(self._iter(), key, key + 1))
        except StopIteration:
            raise IndexError(key) from None

    def count(self):
        count_method = getattr(self._handler, f"{self.entity}_count", None)
        if count_method is not None:
            value = count_method()
            if value is not None:
                return value
        return sum(1 for _ in self._iter())

    @property
    def record_type(self):
        return getattr(self._handler, f"{self.entity}_cls")()

    def lookup(self, ids):
        """Look up records by id. A single id returns one record (or None);
        an iterable of ids returns a dict."""
        id_field = _ID_FIELD[self.entity]
        if isinstance(ids, str):
            for record in self._iter():
                if getattr(record, id_field) == ids:
                    return record
            return None
        wanted = set(ids)
        found = {}
        for record in self._iter():
            rid = getattr(record, id_field)
            if rid in wanted:
                found[rid] = record
        return found


class _Benchmark(_Node):
    """Duck-typed ``ir_datasets.v2`` ``Benchmark`` (see
    ``ir_datasets/v2/protocols.py::Benchmark`` upstream): docs/queries/qrels
    bundled into one evaluable task."""

    def __init__(self, name, docs, queries, qrels, desc=None):
        super().__init__(name, type="tira:benchmark", metadata={"desc": desc} if desc else {})
        self._facets = {"docs": docs, "queries": queries, "qrels": qrels}

    def __getattr__(self, attr):
        facets = self.__dict__.get("_facets") or {}
        if attr in facets:
            return facets[attr]
        raise AttributeError(attr)

    def edge(self, entity):
        return self._facets.get(entity)

    def has(self, entity):
        return entity in self._facets


class TiraProvider:
    """The ``tira`` provider itself -- a duck-typed ``ir_datasets.v2``
    ``Provider`` (see ``ir_datasets/v2/protocols.py::Provider`` upstream):
    a ``prefix``, a ``load(name)``, and a ``discover_edges()``. Everything is
    resolved dynamically (TIRA's dataset catalog is live and can't be frozen
    ahead of time, exactly like ``hf:``/``clirmatrix:`` upstream), so
    ``discover_edges()`` -- the cheap, no-download listing upstream otherwise
    uses for browsing/validation -- has nothing to report without hitting the
    network itself; it yields nothing, which upstream's own ``Provider``
    docstring explicitly allows."""

    prefix = "tira"

    def __init__(self):
        self._client = None
        #: (task, resolved dataset_id) -> {'docs': Table, 'queries': Table, 'qrels': Table},
        #: shared across every name (dataset_id or display_name alias)
        #: resolving to it, so the underlying data is downloaded/parsed once.
        self._tables_cache = {}
        #: (task, name) -> Benchmark (keyed by the raw, possibly-aliased name,
        #: so the alias and the canonical dataset_id get distinct Benchmark
        #: objects, but always share the same facet Tables above).
        self._benchmark_cache = {}

    def _rest_client(self):
        if self._client is None:
            self._client = RestClient()
        return self._client

    def _resolve_dataset_id(self, task, name):
        """A TIRA dataset's own ``dataset_id`` (passed through unchanged), or
        the ``dataset_id`` of whichever dataset in ``task`` has
        ``display_name == name`` -- TIRA's stable, date-suffix-free name for
        a dataset (e.g. ``tiny-example`` for
        ``tiny-example-20251002_0-training``). Raises KeyError if neither
        matches."""
        datasets = self._rest_client().datasets(task)
        if name in datasets:
            return name
        matches = [d for d, meta in datasets.items() if meta.get("display_name") == name]
        if not matches:
            raise KeyError(f"No dataset named {name!r} for task {task!r} is known to TIRA.")
        # Prefer the most recently created dataset if a display_name is reused.
        matches.sort(key=lambda d: datasets[d].get("created", ""), reverse=True)
        return matches[0]

    def _tables(self, task, name):
        client = self._rest_client()
        dataset_id = self._resolve_dataset_id(task, name)
        key = (task, dataset_id)
        if key not in self._tables_cache:
            base_name = f"{self.prefix}:{task}/{dataset_id}"

            def input_dir():
                return client.download_dataset(task, dataset_id, truth_dataset=False)

            def truth_dir():
                return client.download_dataset(task, dataset_id, truth_dataset=True)

            docs_handler = _loader.lazy_docs(input_dir, None, True)
            queries_handler = _loader.lazy_queries(truth_dir, None)
            qrels_handler = _loader.lazy_qrels(truth_dir, None)

            self._tables_cache[key] = {
                "docs": _Table(
                    f"{base_name}/docs",
                    "docs",
                    docs_handler,
                    desc=f"Documents of the TIRA dataset {task}/{dataset_id}.",
                ),
                "queries": _Table(
                    f"{base_name}/queries",
                    "queries",
                    queries_handler,
                    desc=f"Queries of the TIRA dataset {task}/{dataset_id}.",
                ),
                "qrels": _Table(
                    f"{base_name}/qrels", "qrels", qrels_handler, desc=f"Qrels of the TIRA dataset {task}/{dataset_id}."
                ),
            }
        return self._tables_cache[key]

    def _benchmark(self, task, name):
        key = (task, name)
        if key not in self._benchmark_cache:
            tables = self._tables(task, name)
            self._benchmark_cache[key] = _Benchmark(
                f"{self.prefix}:{task}/{name}",
                docs=tables["docs"],
                queries=tables["queries"],
                qrels=tables["qrels"],
                desc=f"The TIRA dataset {task}/{name}, loaded live from the TIRA REST API.",
            )
        return self._benchmark_cache[key]

    def load(self, name):
        """Resolve one (already-qualified, i.e. possibly ``tira:``-prefixed)
        name to a node. KeyError if this provider has nothing by that name."""
        if name.startswith(f"{self.prefix}:"):
            name = name[len(self.prefix) + 1 :]
        parts = name.split("/")
        if len(parts) == 2:
            task, dataset_name = parts
            return self._benchmark(task, dataset_name)
        if len(parts) == 3 and parts[2] in ("docs", "queries", "qrels"):
            task, dataset_name, facet = parts
            return self._tables(task, dataset_name)[facet]
        raise KeyError(f"{name!r} is not a valid tira: name (expected task/dataset[/docs|queries|qrels]).")

    def discover_edges(self):
        """TIRA's catalog is live and arbitrarily large -- see the class
        docstring; there is nothing to report here without hitting the
        network, so (as upstream's own ``Provider`` protocol explicitly
        allows) this yields nothing."""
        return []


#: The provider instance itself, loaded by ``importlib.metadata`` through the
#: ``ir_datasets.providers`` entry point declared in ``setup.cfg`` -- the only
#: way anything in ``ir_datasets.v2`` ever touches this module.
tira = TiraProvider()
