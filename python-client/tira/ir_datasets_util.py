from copy import deepcopy
from typing import NamedTuple
from tira.io_utils import all_lines_to_pandas
import os


def register_dataset_from_re_rank_file(ir_dataset_id, df_re_rank, original_ir_datasets_id=None):
    """
    Load a dynamic ir_datasets integration from a given re_rank_file.
    The dataset will be registered for the id ir_dataset_id.
    The original_ir_datasets_id is used to infer the class of documents, qrels, and queries.
    """
    import ir_datasets
    from ir_datasets.datasets.base import Dataset
    original_dataset = ir_datasets.load(original_ir_datasets_id) if original_ir_datasets_id else None

    docs = __docs(df_re_rank, original_dataset)
    queries = __queries(df_re_rank, original_dataset)
    qrels = __qrels(df_re_rank, original_dataset)
    scoreddocs = __scored_docs(df_re_rank, original_dataset)

    dataset = Dataset(docs, queries, qrels, scoreddocs)
    ir_datasets.registry.register(ir_dataset_id, dataset)
    
    __check_registration_was_successful(ir_dataset_id)


def __docs(df, original_dataset):
    from ir_datasets.formats import BaseDocs, GenericDoc

    class DynamicDocs(BaseDocs):
        def __init__(self, docs):
            self.docs = deepcopy(docs)

        def docs_iter(self):
            return deepcopy(docs).values().__iter__()

        def docs_count(self):
           return len(self.docs)

        def docs_store(self):
            return deepcopy(docs)

    docs = {}
    for _, i in df.iterrows():
        docs[i['docno']] = GenericDoc(doc_id=i['docno'], text= i['text'])

    return DynamicDocs(docs)


def __queries(df, original_dataset):
    from ir_datasets.formats import BaseQueries, GenericQuery

    class DynamicQueries(BaseQueries):
        def __init__(self, queries):
            self.docs = deepcopy(queries)

        def queries_iter(self):
            return deepcopy(queries).values().__iter__()

    queries = {}
    for _, i in df.iterrows():
        queries[i['qid']] = GenericQuery(query_id=i['qid'], text= i['query'])

    return DynamicQueries(queries)



def __qrels(path_to_re_rank_file, original_dataset):
    from ir_datasets.formats import BaseQrels

    if not original_dataset:
        return None

    class DynamicQrels(BaseQrels):
        def __init__(self, qrels):
            self.qrels = list(original_dataset.qrels.qrels_iter())
        
        def qrels_iter(self):
            return self.qrels.__iter__()

    return DynamicQrels


def __scored_docs(df, original_dataset):
    from ir_datasets.formats import BaseScoredDocs
    
    class GenericScoredDocWithRank(NamedTuple):
        query_id: str
        doc_id: str
        score: float
        rank: int

    class DynamicScoredDocs(BaseScoredDocs):
        def __init__(self, docs):
            self.docs = docs

        def scoreddocs_iter(self):
            return deepcopy(self.docs).__iter__()

    docs = []

    for _, i in df.iterrows():
        docs += [GenericScoredDocWithRank(i['qid'], i['docno'], i['score'], i['rank'])]
    
    return DynamicScoredDocs(docs)


def static_ir_datasets_from_directory(directory):
    from ir_datasets.datasets.base import Dataset
    queries_file = directory + '/queries.jsonl'
    docs_file = directory
    if os.path.isfile(docs_file + '/documents.jsonl.gz'):
        docs_file = docs_file + '/documents.jsonl.gz'
    else:
        docs_file = docs_file + '/documents.jsonl'

    docs = __docs(all_lines_to_pandas(docs_file, False), None)
    queries = __queries(all_lines_to_pandas(queries_file, False), None)

    class IrDatasetsFromDirectoryOnly():
        def load(self, dataset_id):
            print(f'Load ir_dataset from "{directory}" instead of "{dataset_id}" because code is executed in TIRA.')
            return Dataset(docs, queries)
    
    return IrDatasetsFromDirectoryOnly()

def __check_registration_was_successful(ir_dataset_id):
    import ir_datasets
    dataset = ir_datasets.load(ir_dataset_id)

    assert dataset.has_docs(), "dataset has no documents"
    assert dataset.has_queries(), "dataset has no queries"
    assert dataset.has_qrels(), "dataset has no qrels"
    assert dataset.has_scoreddocs(), "dataset has no scored_docs"

