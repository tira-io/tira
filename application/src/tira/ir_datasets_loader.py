import sys
import json
from pathlib import Path
from typing import Iterable


class IrDatasetsLoader(object):
    """ Base class for loading datasets in a standardized format"""

    def load_irds(self, ir_datasets_id):
        import ir_datasets
        try:
            return ir_datasets.load(ir_datasets_id)
        except:
            raise ValueError(f'Could not load the dataset {ir_datasets_id}. Does it exist?')

    def load_dataset_for_fullrank(self, ir_datasets_id: str, output_dataset_path: Path, output_dataset_truth_path: Path,  include_original=False) -> None:
        """ Loads a dataset through the ir_datasets package by the given ir_datasets ID.
        Maps documents, queries, qrels to a standardized format in preparation for full-rank operations with PyTerrier.
        
        @param ir_datasets_id: the dataset ID as of ir_datasets
        @param output_dataset_path: the path to the directory where the output files will be stored
        @param output_dataset_truth_path: the path to the directory where the output files will be stored
        @param include_original {False}: flag which signals if the original data of documents and queries should be included 
        """
        dataset = self.load_irds(ir_datasets_id)
        
        docs_mapped = (self.map_doc(doc, include_original) for doc in dataset.docs_iter())
        queries_mapped = [self.map_query(query, include_original) for query in dataset.queries_iter()]
        qrels_mapped = [self.map_qrel(qrel) for qrel in dataset.qrels_iter()]
        
        self.write_lines_to_file(docs_mapped, output_dataset_path/"documents.jsonl")
        self.write_lines_to_file(queries_mapped, output_dataset_path/"queries.jsonl")
        self.write_lines_to_file(qrels_mapped, output_dataset_truth_path/"qrels.txt")
        self.write_lines_to_file(queries_mapped, output_dataset_truth_path/"queries.jsonl")


    def load_dataset_for_rerank(self, ir_datasets_id: str, output_dataset_path: Path, output_dataset_truth_path: Path, include_original: bool, run_file: Path) -> None:
        """ Loads a dataset through ir_datasets package by the given ir_datasets ID.
        Maps qrels and TREC-run-formatted data by a given file to a format fitted for re-rank operations with PyTerrier.
        
        @param ir_datasets_id: the dataset ID as of ir_datasets
        @param output_dataset_path: the path to the directory where the output files will be stored
        @param output_dataset_truth_path: the path to the directory where the output files will be stored
        @param include_original {False}: flag which signals if the original data of documents and queries should be included
        @param run_file: the path to a file with data in TREC-run format
        """
        dataset = self.load_irds(ir_datasets_id)
        
        id_pairs = self.extract_ids_from_run_file(run_file)
        docs = self.get_docs_by_ids(dataset, [id[1] for id in id_pairs])
        rerank = (self.construct_rerank_row(dataset, docs, id_pair[0], id_pair[1]) for id_pair in id_pairs)
        
        qrels_mapped = (self.map_qrel(qrel) for qrel in dataset.qrels_iter())
        
        self.write_lines_to_file(rerank, output_dataset_path/"rerank.jsonl")
        self.write_lines_to_file(qrels_mapped, output_dataset_truth_path/"qrels.txt")


    def map_doc(self, doc: tuple, include_original=False) -> str:
        """ Maps a document of any dataset (loaded through ir_datasets) to a standarized format
        stores full document data too, if flag 'include_original' is set

        @param doc: the document as a namedtuple
        @param include_original: flag which signals if the original document data should be stored too
        :return ret: the mapped document 
        """
        ret = {
            "docno": doc.doc_id,
            # TODO: change when .default_text() is implemented
            "text":doc.default_text()
        }
        if include_original:
            ret["original_doc"] = doc._asdict()
        return json.dumps(ret)


    def map_query(self, query: tuple, include_original=False) -> str:
        ret = {
            "qid": query.query_id,
            #"query": query.default_text()
            "query": query.text,
        }
        if include_original:
            ret["original_doc"] = query._asdict()
        return json.dumps(ret)


    def map_qrel(self, qrel: tuple) -> str:
        return f"{qrel.query_id} {qrel.iteration} {qrel.doc_id} {qrel.relevance}"


    def extract_ids_from_run_file(self, run_file: Path) -> list:
        with run_file.open('r') as file:
            id_pairs = [line.split()[:3:2] for line in file]
            return id_pairs
        

    def get_docs_by_ids(self, dataset, doc_ids: list) -> dict:
        docstore = dataset.docs_store()
        return docstore.get_many(doc_ids)
        

    def construct_rerank_row(self, dataset, docs: dict, query_id: str, doc_id: str) -> str:
        query = [query for query in dataset.queries_iter() if query.query_id == query_id][0]
        doc = docs[doc_id]     
        ret = {
            "qid": query_id,
            # TODO: change when .default_text() is implemented
            #"query": query.default_text(),
            "query": query.title,
            "original_query": query._asdict(),
            "docno": doc_id,
            # TODO: change when .default_text() is implemented
            #"text": doc.default_text(),
            "text": json.dumps(doc._asdict()),
            "original_doc": doc._asdict(),
        }
        return json.dumps(ret)


    def write_lines_to_file(self, lines: Iterable[str], path: Path) -> None:
        if(path.exists()):
            raise RuntimeError(f"File already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('wt') as file:
            file.writelines('%s\n' % line for line in lines)

