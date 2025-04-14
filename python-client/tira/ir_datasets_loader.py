import copy
import gzip
import json
import os
from base64 import b64encode
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


class IrDatasetsLoader(object):
    """Base class for loading datasets in a standardized format"""

    def load_irds(self, ir_datasets_id):
        from tira.third_party_integrations import ir_datasets

        try:
            return ir_datasets.load(ir_datasets_id)
        except Exception:
            raise ValueError(f"Could not load the dataset {ir_datasets_id}. Does it exist?")

    def yield_docs(self, dataset, include_original, skip_duplicate_ids, allowlist_path_ids):
        already_covered_ids = set()
        allowed_ids = set()
        if allowlist_path_ids:
            with open(allowlist_path_ids, "r") as inp_file:
                for i in inp_file:
                    allowed_ids.add(i.strip())
            print("I use a allow list of size ", len(allowed_ids))

        for doc in tqdm(dataset.docs_iter(), "Load Documents"):
            if skip_duplicate_ids and doc.doc_id in already_covered_ids:
                continue
            if allowlist_path_ids and str(doc.doc_id) not in allowed_ids:
                continue

            yield self.map_doc(doc, include_original)
            if skip_duplicate_ids:
                already_covered_ids.add(doc.doc_id)

    def load_dataset_for_fullrank(
        self,
        ir_datasets_id: str,
        output_dataset_path: Path,
        output_dataset_truth_path: Path,
        include_original=True,
        skip_documents=False,
        skip_qrels=False,
        skip_duplicate_ids=True,
        allowlist_path_ids: "Optional[Path]" = None,
    ) -> None:
        """Loads a dataset through the ir_datasets package by the given ir_datasets ID.
        Maps documents, queries, qrels to a standardized format in preparation for full-rank operations with PyTerrier.

        @param ir_datasets_id: the dataset ID as of ir_datasets
        @param output_dataset_path: the path to the directory where the output files will be stored
        @param output_dataset_truth_path: the path to the directory where the output files will be stored
        @param include_original {False}: flag which signals if the original data of documents and queries should be included
        @param skip_duplicate_ids: Should this pipeline skip duplicate ids?
        @param allowlist_path_ids: skip ids not in the allowlist (e.g., for filtering the subcategories of the ClueWebs)
        """
        dataset = self.load_irds(ir_datasets_id)

        if not skip_documents and output_dataset_path:
            self.write_lines_to_file(
                self.yield_docs(dataset, include_original, skip_duplicate_ids, allowlist_path_ids),
                output_dataset_path / "documents.jsonl",
            )

        queries_mapped_jsonl = [self.map_query_as_jsonl(query, include_original) for query in dataset.queries_iter()]
        queries_mapped_xml = [self.map_query_as_xml(query, include_original) for query in dataset.queries_iter()]

        if not skip_qrels:
            try:
                qrels_mapped = [self.map_qrel(qrel) for qrel in dataset.qrels_iter()]
            except Exception:
                print(
                    'WARNING: I could not load qrels and will skip writing the file "qrels.txt". This is expected if'
                    " your dataset has no qrels yet. If you have qrels, please debug this problem locally on your"
                    " machine."
                )
                qrels_mapped = []

            if len(qrels_mapped) > 0:
                self.write_lines_to_file(qrels_mapped, output_dataset_truth_path / "qrels.txt")

        if output_dataset_path:
            self.write_lines_to_file(queries_mapped_jsonl, output_dataset_path / "queries.jsonl")
            self.write_lines_to_file(
                [json.dumps({"ir_datasets_id": ir_datasets_id})], output_dataset_path / "metadata.json"
            )
            self.write_lines_to_xml_file(ir_datasets_id, queries_mapped_xml, output_dataset_path / "queries.xml")

        if output_dataset_truth_path:
            self.write_lines_to_file(queries_mapped_jsonl, output_dataset_truth_path / "queries.jsonl")
            self.write_lines_to_xml_file(ir_datasets_id, queries_mapped_xml, output_dataset_truth_path / "queries.xml")

    def reformat_to_re_rank_dataset(
        self, run_file: Path, dataset_directory: Path, output_dataset_dir: Path, log_file: Path
    ):
        run_file = Path(run_file).absolute()
        dataset_directory = Path(dataset_directory).absolute()

        if not log_file.exists():
            with open(log_file, "w") as f:
                f.write("")

        with open(log_file, "r") as f:
            for l in f:
                try:
                    l = json.loads(l)
                    if (
                        l["dataset_directory"] == str(dataset_directory)
                        and l["re_rank_file"]
                        and l["run_file"] == str(run_file)
                    ):
                        return str(Path(l["re_rank_dataset_directory"]) / "input-data")
                except:
                    pass

        import ir_datasets

        from tira.ir_datasets_util import static_ir_dataset

        dataset = static_ir_dataset(str(dataset_directory)).load("does-not-matter")
        ir_datasets.registry.register(dataset.dataset_id, dataset)

        self.load_dataset_for_rerank(
            dataset.dataset_id,
            output_dataset_path=output_dataset_dir / "input-data",
            output_dataset_truth_path=None,
            include_original=False,
            run_file=run_file,
        )

        ret = {
            "dataset_directory": str(dataset_directory),
            "re_rank_file": True,
            "run_file": str(run_file),
            "re_rank_dataset_directory": str(output_dataset_dir),
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(ret) + "\n")

        return Path(ret["re_rank_dataset_directory"]) / "input-data"

    def load_dataset_for_rerank(
        self,
        ir_datasets_id: str,
        output_dataset_path: Path,
        output_dataset_truth_path: Path,
        include_original: bool,
        run_file: Path,
    ) -> None:
        """Loads a dataset through ir_datasets package by the given ir_datasets ID.
        Maps qrels and TREC-run-formatted data by a given file to a format fitted for re-rank operations with PyTerrier.

        @param ir_datasets_id: the dataset ID as of ir_datasets
        @param output_dataset_path: the path to the directory where the output files will be stored
        @param output_dataset_truth_path: the path to the directory where the output files will be stored
        @param include_original {False}: flag which signals if the original data of documents and queries should be included
        @param run_file: the path to a file with data in TREC-run format
        """
        dataset = self.load_irds(ir_datasets_id)
        queries = {str(i.query_id): i for i in dataset.queries_iter()}

        run = self.load_run_file(run_file)
        print("Get Documents")
        docs = self.get_docs_by_ids(dataset, set(str(i["docno"]) for i in run))
        print("Produce rerank data.")
        rerank = tqdm(
            (self.construct_rerank_row(docs, queries, i, include_original) for i in run), "Produce Rerank File."
        )
        print("Write rerank data.")
        self.write_lines_to_file(rerank, output_dataset_path / "rerank.jsonl.gz")
        print("Done rerank data was written.")
        if output_dataset_truth_path:
            print("Write qrels data.")
            qrels_mapped = (self.map_qrel(qrel) for qrel in dataset.qrels_iter())
            self.write_lines_to_file(qrels_mapped, output_dataset_truth_path / "qrels.txt")

    def map_doc(self, doc: tuple, include_original=True) -> str:
        """Maps a document of any dataset (loaded through ir_datasets) to a standarized format
        stores full document data too, if flag 'include_original' is set

        @param doc: the document as a namedtuple
        @param include_original: flag which signals if the original document data should be stored too
        :return ret: the mapped document
        """
        ret = {"docno": doc.doc_id, "text": doc.default_text()}
        if include_original:
            ret["original_document"] = self.make_serializable(doc._asdict())
        return json.dumps(ret)

    def map_query_as_jsonl(self, query: tuple, include_original=True) -> str:
        ret = {
            "qid": query.query_id,
            "query": query.default_text(),
        }
        if include_original:
            ret["original_query"] = query._asdict()
        return json.dumps(ret)

    def map_query_as_xml(self, query: tuple, include_original=False) -> str:
        soup = BeautifulSoup()
        soup.append(soup.new_tag("topic", attrs={"number": query.query_id}))
        soup.topic.append(soup.new_tag("query"))
        soup.query.append(soup.new_string(query.default_text()))

        if include_original:
            soup.topic.append(soup.new_tag("original_query"))
            for key, value in query._asdict().items():
                soup.original_query.append(soup.new_tag(str(key)))
                tag = soup.original_query.find(key)
                tag.append(soup.new_string(str(value)))
        return soup

    def map_qrel(self, qrel: tuple) -> str:
        return f"{qrel.query_id} {qrel.iteration} {qrel.doc_id} {qrel.relevance}"

    def load_run_file(self, run_file: Path) -> list:
        if not os.path.abspath(run_file).endswith("run.txt"):
            run_file = run_file / "run.txt"

        run = pd.read_csv(
            os.path.abspath(run_file), sep="\\s+", names=["qid", "Q0", "docno", "rank", "score", "system"]
        )
        run = run.copy().sort_values(["qid", "score", "docno"], ascending=[True, False, False]).reset_index()
        run = run.groupby("qid")[["qid", "Q0", "docno", "rank", "score", "system"]].head(1000)

        # Make sure that rank position starts by 1
        run["rank"] = 1
        run["rank"] = run.groupby("qid")["rank"].cumsum()

        return [i.to_dict() for _, i in run[["qid", "Q0", "docno", "rank", "score", "system"]].iterrows()]

    def get_docs_by_ids(self, dataset, doc_ids: set[str]) -> dict[Any, Any]:
        docstore = dataset.docs_store()
        try:
            ret = {}
            doc_ids = set(doc_ids)
            for doc in tqdm(docstore.get_many_iter(doc_ids), total=len(doc_ids), desc="Get Docs"):
                ret[doc.doc_id] = doc
            return ret
        except Exception:
            ret = {}
            doc_ids = set(doc_ids)
            for doc_id in tqdm(doc_ids, total=len(doc_ids), desc="Get Docs"):
                doc = docstore.get(doc_id)
                ret[doc.doc_id] = doc
            return ret

    def make_serializable(self, o: dict):
        for k in o.keys():
            value = o[k]
            if value and value.__class__ and str(value.__class__.__name__) == "bytes":
                o[k] = b64encode(value).decode("ascii")

        return o

    def construct_rerank_row(
        self, docs: dict, queries: dict, rerank_line: "dict[str, Any]", include_original
    ) -> "Optional[str]":
        query = queries[str(rerank_line["qid"])]
        doc = docs.get(str(rerank_line["docno"]), None)

        if not doc:
            return None

        ret = {
            "qid": query.query_id,
            "query": query.default_text(),
            "original_query": self.make_serializable(query._asdict()),
            "docno": rerank_line["docno"],
            "text": doc.default_text(),
            "original_document": {},
            "rank": rerank_line["rank"],
            "score": rerank_line["score"],
        }

        if include_original:
            ret["original_document"] = (self.make_serializable(doc._asdict()),)

        return json.dumps(ret)

    def write_lines_to_file(self, lines: "Iterable[str]", path: "Path") -> None:
        if path.exists():
            raise RuntimeError(f"File already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)

        if os.path.abspath(path).endswith(".gz"):
            with gzip.open(os.path.abspath(path), "wb") as file:
                for line in lines:
                    if not line:
                        continue
                    file.write((line + "\n").encode("utf-8"))
        else:
            with path.open("wt") as file:
                file.writelines("%s\n" % line for line in lines if line)

    def write_lines_to_xml_file(self, ir_datasets_id: str, lines: "Iterable[str]", path: "Path") -> None:
        if path.exists():
            raise RuntimeError(f"File already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        soup = BeautifulSoup()
        soup.append(soup.new_tag("topics", attrs={"ir-datasets-id": ir_datasets_id}))
        root = soup.find("topics")
        for line in lines:
            root.append(copy.deepcopy(line))
        with path.open("wt") as file:
            file.write(soup.prettify())
