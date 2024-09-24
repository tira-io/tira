import logging
import os
from copy import deepcopy
from typing import TYPE_CHECKING, NamedTuple

from tira.io_utils import stream_all_lines
from tira.tirex import IRDS_TO_TIREX_DATASET

original_ir_datasets_load = None
try:
    import ir_datasets as original_ir_datasets

    original_ir_datasets_load = original_ir_datasets.load
except ImportError:
    pass

if TYPE_CHECKING:
    from .tira_client import TiraClient


class TirexQuery(NamedTuple):
    query_id: str
    text: str
    title: str
    query: str
    description: str
    narrative: str

    def default_text(self):
        """
        title
        """
        return self.title


class DictDocsstore:
    def __init__(self, docs):
        self.docs = docs

    def __getitem__(self, item):
        return self.docs[item]

    def get(self, item):
        return self.docs.get(item)

    def __iter__(self):
        return self.docs.__iter__()

    def __len__(self):
        return len(self.docs)

    def get_many_iter(self, docids):
        for docid in docids:
            yield self.get(docid)


def register_dataset_from_re_rank_file(ir_dataset_id, df_re_rank, original_ir_datasets_id=None):
    """
    Load a dynamic ir_datasets integration from a given re_rank_file.
    The dataset will be registered for the id ir_dataset_id.
    The original_ir_datasets_id is used to infer the class of documents, qrels, and queries.
    """
    import ir_datasets
    from ir_datasets.datasets.base import Dataset

    original_dataset = ir_datasets.load(original_ir_datasets_id) if original_ir_datasets_id else None

    docs = __docs(df_re_rank, original_dataset, True)
    queries = __queries(df_re_rank, original_dataset)
    qrels = __lazy_qrels(None, original_dataset)
    scoreddocs = __scored_docs(df_re_rank, original_dataset)

    dataset = Dataset(docs, queries, qrels, scoreddocs)
    dataset.metadata = None
    ir_datasets.registry._allow_overwrite = True
    ir_datasets.registry.register(ir_dataset_id, dataset)

    __check_registration_was_successful(ir_dataset_id, original_ir_datasets_id is None)


def translate_irds_id_to_tirex(dataset):
    if type(dataset) is not str:
        if hasattr(dataset, "irds_ref"):
            return translate_irds_id_to_tirex(dataset.irds_ref().dataset_id())
        else:
            raise ValueError(f"I can not handle {dataset}.")
    return IRDS_TO_TIREX_DATASET.get(dataset, dataset)


def __docs(input_file, original_dataset, load_default_text):
    from ir_datasets.formats import BaseDocs, GenericDoc

    class DynamicDocs(BaseDocs):
        def __init__(self, input_file, load_default_text):
            self.docs = None
            self.input_file = input_file
            self.load_default_text = load_default_text

        def docs_iter(self):
            return self.stream_docs()

        def docs_count(self):
            return sum(1 for _ in self.stream_docs())

        def docs_store(self):
            return DictDocsstore(self.__parsed_docs())

        def __parsed_docs(self):
            if self.docs is None:
                d = {}
                for i in self.stream_docs():
                    d[i.doc_id] = i

                self.docs = d

            return self.docs

        def stream_docs(self):
            already_covered = set()
            for i in stream_all_lines(self.get_input_file(), self.load_default_text):
                if i["docno"] not in already_covered:
                    already_covered.add(i["docno"])
                    yield GenericDoc(doc_id=i["docno"], text=i["text"])

        def get_input_file(self):
            if type(self.input_file) is str:
                return self.input_file

            ret = self.input_file()
            if os.path.isfile(ret + "/documents.jsonl.gz"):
                return ret + "/documents.jsonl.gz"
            else:
                return ret + "/documents.jsonl"

    return DynamicDocs(input_file, load_default_text)


def __lazy_qrels(input_file, original_qrels):
    from ir_datasets.formats import BaseQrels, TrecQrel, TrecQrels
    from ir_datasets.util.download import LocalDownload

    if input_file is None and original_qrels is None:
        return

    class QrelsFromTira(BaseQrels):
        def __init__(self, input_file, original_qrels):
            self.qrels = None if not original_qrels else original_qrels
            self.input_file = input_file
            self.original_qrels = original_qrels

        def qrels_cls(self):
            return TrecQrel if not self.original_qrels else self.original_qrels.qrels_cls()

        def qrels_iter(self):
            if not self.qrels:
                qrels_file = self.input_file() + "/qrels.txt"

                self.qrels = TrecQrels(LocalDownload(qrels_file), {})

            return self.qrels.qrels_iter()

        def qrels_defs(self):
            self.qrels_iter()
            return self.qrels.qrels_defs()

    return QrelsFromTira(input_file, original_qrels)


def __queries(input_file, original_dataset):
    from ir_datasets.formats import BaseQueries

    class DynamicQueries(BaseQueries):
        def __init__(self, input_file):
            self.queries = None
            self.input_file = input_file

        def queries_iter(self):
            return deepcopy(self.__get_queries()).values().__iter__()

        def queries_cls(self):
            return TirexQuery

        def get_input_file(self):
            if type(self.input_file) is str:
                return self.input_file

            return self.input_file() + "/queries.jsonl"

        def __get_queries(self):
            if self.queries is None:
                ret = {}
                for i in stream_all_lines(self.get_input_file(), False):
                    orig_query = None if "original_query" not in i else i["original_query"]
                    description = (
                        None
                        if (not orig_query or type(orig_query) is not dict or "description" not in orig_query)
                        else orig_query["description"]
                    )
                    narrative = (
                        None
                        if (not orig_query or type(orig_query) is not dict or "narrative" not in orig_query)
                        else orig_query["narrative"]
                    )
                    if i["qid"] not in ret:
                        ret[i["qid"]] = TirexQuery(
                            query_id=i["qid"],
                            text=i["query"],
                            query=i["query"],
                            title=i["query"],
                            description=description,
                            narrative=narrative,
                        )

                self.queries = ret

            return self.queries

    return DynamicQueries(input_file)


def __scored_docs(input_file, original_dataset):
    from ir_datasets.formats import BaseScoredDocs, GenericDoc, GenericQuery

    class GenericScoredDocWithRank(NamedTuple):
        query_id: str
        doc_id: str
        score: float
        rank: int
        document: GenericDoc
        query: GenericQuery

    class DynamicScoredDocs(BaseScoredDocs):
        def __init__(self, docs):
            self.docs = docs

        def scoreddocs_iter(self):
            return deepcopy(self.docs).__iter__()

        def scoreddocs_count(self) -> int:
            return len(docs)

    docs = []

    if not os.path.isfile(input_file) and os.path.isfile(os.path.join(input_file, "rerank.jsonl.gz")):
        input_file = os.path.join(input_file, "rerank.jsonl.gz")
    elif not os.path.isfile(input_file) and os.path.isfile(os.path.join(input_file, "rerank.jsonl")):
        input_file = os.path.join(input_file, "rerank.jsonl")

    for i in stream_all_lines(input_file, True):
        d, q = None, None

        if "query" in i and "text" in i:
            d = GenericDoc(doc_id=i["docno"], text=i["text"])
            q = GenericQuery(query_id=i["qid"], text=i["query"])

        doc = GenericScoredDocWithRank(i["qid"], i["docno"], i["score"], i["rank"], d, q)

        docs += [doc]

    return DynamicScoredDocs(docs)


def static_ir_dataset(directory, existing_ir_dataset=None):
    from ir_datasets.datasets.base import Dataset

    if existing_ir_dataset is None:
        queries_file = directory + "/queries.jsonl"
        docs_file = directory
        if os.path.isfile(docs_file + "/documents.jsonl.gz"):
            docs_file = docs_file + "/documents.jsonl.gz"
        else:
            docs_file = docs_file + "/documents.jsonl"

        docs = __docs(docs_file, None, True)
        queries = __queries(queries_file, None)
        ret = Dataset(docs, queries)
        ret.dataset_id = lambda: f"static_ir_dataset-{directory}"
        return static_ir_dataset(directory, ret)

    class StaticIrDatasets:
        def load(self, dataset_id):
            print(f'Load ir_dataset from "{directory}" instead of "{dataset_id}" because code is executed in TIRA.')
            return existing_ir_dataset

        def topics_file(self, dataset_id):
            return directory + "/queries.xml"

    return StaticIrDatasets()


def ir_dataset_from_tira_fallback_to_original_ir_datasets():
    from ir_datasets.datasets.base import Dataset

    def get_download_dir_from_tira(tira_path, truth_dataset) -> "TiraClient":
        if len(tira_path.split("/")) != 2:
            logging.info(f"Please pass tira_path as <task>/<tira-dataset>. Got {tira_path}")
            raise ValueError(f"Please pass tira_path as <task>/<tira-dataset>. Got {tira_path}")

        from tira.rest_api_client import Client as RestClient

        task, dataset = tira_path.split("/")
        return RestClient().download_dataset(task, dataset, truth_dataset=truth_dataset)

    class IrDatasetsFromTira:
        def load(self, dataset_id):
            try:
                return original_ir_datasets_load(dataset_id)
            except Exception:
                logging.info(f'Load ir_dataset "{dataset_id}" from tira.')
                docs = self.lazy_docs(lambda: get_download_dir_from_tira(dataset_id, False), None, True)
                queries = self.lazy_queries(lambda: get_download_dir_from_tira(dataset_id, True), None)
                qrels = self.lazy_qrels(lambda: get_download_dir_from_tira(dataset_id, True), None)

                ret = Dataset(docs, queries, qrels)
                ret.dataset_id = lambda: dataset_id
                ret.scoreddocs_iter = lambda: self._load_scored_docs(
                    get_download_dir_from_tira(dataset_id, False), None
                ).scoreddocs_iter()
                return ret

        def topics_file(self, tira_path):
            return get_download_dir_from_tira(tira_path, True) + "/queries.xml"

    ret = IrDatasetsFromTira()
    ret.lazy_docs = __docs
    ret.lazy_queries = __queries
    ret.lazy_qrels = __lazy_qrels
    ret._load_scored_docs = __scored_docs

    return ret


def __check_registration_was_successful(ir_dataset_id, ignore_qrels=True):
    import ir_datasets

    dataset = ir_datasets.load(ir_dataset_id)

    assert dataset.has_docs(), "dataset has no documents"
    assert dataset.has_queries(), "dataset has no queries"
    assert ignore_qrels or dataset.has_qrels(), "dataset has no qrels"
    assert dataset.has_scoreddocs(), "dataset has no scored_docs"
