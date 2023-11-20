from copy import deepcopy
from typing import NamedTuple
from tira.io_utils import all_lines_to_pandas
from tira.tirex import IRDS_TO_TIREX_DATASET, TIREX_DATASETS
import os

original_ir_datasets_load = None
try:
    import ir_datasets as original_ir_datasets
    original_ir_datasets_load = original_ir_datasets.load
except:
    pass


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
    
    __check_registration_was_successful(ir_dataset_id, original_ir_datasets_id is None)


def translate_irds_id_to_tirex(dataset):
    if type(dataset) != str:
        if hasattr(dataset, 'irds_ref'):
            return translate_irds_id_to_tirex(dataset.irds_ref().dataset_id())
        else:
            raise ValueError(f'I can not handle {dataset}.')
    
    return IRDS_TO_TIREX_DATASET[dataset] if dataset in IRDS_TO_TIREX_DATASET else dataset


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


def __lazy_docs(tira_path):
    from ir_datasets.formats import BaseDocs, GenericDoc

    class DocumentsFromTira(BaseDocs):
        def __init__(self):
            self.docs = None
            if len(tira_path.split('/')) != 2:
                print(f'Please pass tira_path as <task>/<tira-dataset>. Got {tira_path}')
                return

            self.task, self.dataset = tira_path.split('/')

        def docs_iter(self):
            return self.get_docs().values().__iter__()

        def docs_count(self):
           return len(self.get_docs())

        def docs_store(self):
            return self.get_docs()

        def get_docs(self):
            if not self.docs:
                from tira.rest_api_client import Client as RestClient
                docs_file = RestClient().download_dataset(self.task, self.dataset)
                if os.path.isfile(docs_file + '/documents.jsonl.gz'):
                    docs_file = docs_file + '/documents.jsonl.gz'
                else:
                    docs_file = docs_file + '/documents.jsonl'
            
                self.docs = {}

                for _, i in all_lines_to_pandas(docs_file, False).iterrows():
                    self.docs[i['docno']] = GenericDoc(doc_id=i['docno'], text= i['text'])
                
            return self.docs

    ret = DocumentsFromTira()
    
    return ret


def __lazy_qrels(tira_path):
    from ir_datasets.formats import BaseQrels, TrecQrel, TrecQrels
    from ir_datasets.util.download import LocalDownload

    class QrelsFromTira(BaseQrels):
        def __init__(self):
            self.qrels = None
            if len(tira_path.split('/')) != 2:
                print(f'Please pass tira_path as <task>/<tira-dataset>. Got {tira_path}')
                return

            self.task, self.dataset = tira_path.split('/')

        def qrels_cls(self):
            return TrecQrel
        
        def qrels_iter(self):
            if not self.qrels:
                from tira.rest_api_client import Client as RestClient
                qrels_file = RestClient().download_dataset(self.task, self.dataset, truth_dataset=True) + '/qrels.txt'

                self.qrels = TrecQrels(LocalDownload(qrels_file), {})

            return self.qrels.qrels_iter()

        def qrels_defs(self):
            self.qrels_iter()
            return self.qrels.qrels_defs()

    return QrelsFromTira()


def __lazy_queries(tira_path):
    from ir_datasets.formats import BaseQueries

    class QueriesFromTira(BaseQueries):
        def __init__(self):
            self.queries = None
            if len(tira_path.split('/')) != 2:
                print(f'Please pass tira_path as <task>/<tira-dataset>. Got {tira_path}')
                return

            self.task, self.dataset = tira_path.split('/')

        def queries_cls(self):
            return TirexQuery
        
        def queries_iter(self):
            if not self.queries:
                from tira.rest_api_client import Client as RestClient
                queries_file = RestClient().download_dataset(self.task, self.dataset, truth_dataset=True) + '/queries.jsonl'

                self.queries = {}
                for _, i in all_lines_to_pandas(queries_file, False).iterrows():
                    orig_query = None if 'original_query' not in i else i['original_query']
                    
                    description = None if (not orig_query or type(orig_query) != dict or 'description' not in orig_query) else orig_query['description']
                    narrative = None if (not orig_query or type(orig_query) != dict or 'narrative' not in orig_query) else orig_query['narrative']
                    self.queries[i['qid']] = TirexQuery(query_id=i['qid'], text=i['query'], query=i['query'], title=i['query'], description=description, narrative=narrative)

            return deepcopy(self.queries).values().__iter__()
    
    return QueriesFromTira()

def __queries(df, original_dataset):
    from ir_datasets.formats import BaseQueries

    class DynamicQueries(BaseQueries):
        def __init__(self, queries):
            self.queries = deepcopy(queries)

        def queries_iter(self):
            return deepcopy(self.queries).values().__iter__()

        def queries_cls(self):
            return TirexQuery

    queries = {}
    for _, i in df.iterrows():
        i = i.to_dict()
        orig_query = None if 'original_query' not in i else i['original_query']
        description = None if (not orig_query or type(orig_query) != dict or 'description' not in orig_query) else orig_query['description']
        narrative = None if (not orig_query or type(orig_query) != dict or 'narrative' not in orig_query) else orig_query['narrative']
        queries[i['qid']] = TirexQuery(query_id=i['qid'],  text=i['query'], query=i['query'], title=i['query'], description=description, narrative=narrative)

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


def static_ir_dataset(directory, existing_ir_dataset=None):
    from ir_datasets.datasets.base import Dataset
    import pandas as pd
    if existing_ir_dataset is None:
        queries_file = directory + '/queries.jsonl'
        docs_file = directory
        if os.path.isfile(docs_file + '/documents.jsonl.gz'):
            docs_file = docs_file + '/documents.jsonl.gz'
        else:
            docs_file = docs_file + '/documents.jsonl'

        docs = __docs(all_lines_to_pandas(docs_file, False) if os.path.isfile(docs_file) else pd.DataFrame([]), None)
        queries = __queries(all_lines_to_pandas(queries_file, False), None)
        return static_ir_dataset(directory, Dataset(docs, queries))

    class StaticIrDatasets():
        def load(self, dataset_id):
            print(f'Load ir_dataset from "{directory}" instead of "{dataset_id}" because code is executed in TIRA.')
            return existing_ir_dataset
        def topics_file(self, dataset_id):
            return directory + '/queries.xml'
    
    return StaticIrDatasets()


def ir_dataset_from_tira_fallback_to_original_ir_datasets():
    from ir_datasets.datasets.base import Dataset

    class IrDatasetsFromTira():
        def load(self, dataset_id):
            try:
                return original_ir_datasets_load(dataset_id)
            except:
                print(f'Load ir_dataset "{dataset_id}" from tira.')
                docs = self.lazy_docs(dataset_id)
                queries = self.lazy_queries(dataset_id)
                qrels = self.lazy_qrels(dataset_id)
                return Dataset(docs, queries, qrels)

        def topics_file(self, tira_path):
            from tira.rest_api_client import Client as RestClient
            task, dataset = tira_path.split('/')
            return RestClient().download_dataset(task, dataset, truth_dataset=True) + '/queries.xml'

    ret = IrDatasetsFromTira()
    ret.lazy_docs = __lazy_docs
    ret.lazy_queries = __lazy_queries
    ret.lazy_qrels = __lazy_qrels

    return ret

def __check_registration_was_successful(ir_dataset_id, ignore_qrels=True):
    import ir_datasets
    dataset = ir_datasets.load(ir_dataset_id)

    assert dataset.has_docs(), "dataset has no documents"
    assert dataset.has_queries(), "dataset has no queries"
    assert ignore_qrels or dataset.has_qrels(), "dataset has no qrels"
    assert dataset.has_scoreddocs(), "dataset has no scored_docs"

