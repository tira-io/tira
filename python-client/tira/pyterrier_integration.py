import os
import uuid
from pathlib import Path

from tira.tirex import IRDS_TO_TIREX_DATASET


class PyTerrierIntegration:
    def __init__(self, tira_client):
        self.tira_client = tira_client
        self.pd = tira_client.pd
        self.irds_docker_image = "webis/tira-application:0.0.36"

    def retriever(self, approach, dataset=None):
        from tira.pyterrier_util import TiraFullRankTransformer

        input_dir = self.ensure_dataset_is_cached(dataset, dataset)
        return TiraFullRankTransformer(approach, self.tira_client, input_dir)

    def ensure_dataset_is_cached(self, irds_dataset_id, dataset):
        import os
        from pathlib import Path

        from tira.io_utils import run_cmd

        cache_dir = self.tira_client.tira_cache_dir + "/pyterrier/" + irds_dataset_id
        full_rank_data = cache_dir + "/full-rank/"
        truth_data = cache_dir + "/truth-data/"
        irds_cache = cache_dir + "/irds-cache/"

        if os.path.isfile(full_rank_data + "/documents.jsonl"):
            return full_rank_data

        Path(full_rank_data).mkdir(parents=True, exist_ok=True)
        Path(truth_data).mkdir(parents=True, exist_ok=True)
        Path(irds_cache).mkdir(parents=True, exist_ok=True)

        run_cmd(
            [
                "docker",
                "run",
                "-v",
                irds_cache + ":/root/.ir_datasets/:rw",
                "-v",
                full_rank_data + ":/output/:rw",
                "-v",
                truth_data + ":/truth/:rw",
                "--entrypoint",
                "/irds_cli.sh",
                self.irds_docker_image,
                "--output_dataset_path",
                "/output",
                "--ir_datasets_id",
                irds_dataset_id,
                "--output_dataset_truth_path",
                "/truth",
            ]
        )

        return full_rank_data

    def create_rerank_file(self, run_df=None, run_file=None, irds_dataset_id=None):
        import gzip
        import json
        import tempfile
        from pathlib import Path

        from tira.io_utils import run_cmd
        from tira.third_party_integrations import persist_and_normalize_run

        if run_df is None and run_file is None:
            raise ValueError("Please pass either run_df or run_file")

        if run_file is not None:
            return run_file

        run_file = tempfile.TemporaryDirectory("-rerank-run").name
        Path(run_file).mkdir(parents=True, exist_ok=True)

        if "text" not in run_df.columns and "body" not in run_df.columns:
            if not irds_dataset_id:
                raise ValueError(f"Please pass a irds_dataset_id. Got {irds_dataset_id}.")
            persist_and_normalize_run(run_df, "system-is-ignored", run_file)

            cache_dir = self.tira_client.tira_cache_dir + "/pyterrier/" + irds_dataset_id
            irds_cache = cache_dir + "/irds-cache/"

            run_cmd(
                [
                    "docker",
                    "run",
                    "-v",
                    irds_cache + ":/root/.ir_datasets/:rw",
                    "-v",
                    run_file + ":/output/:rw",
                    "--entrypoint",
                    "/irds_cli.sh",
                    self.irds_docker_image,
                    "--output_dataset_path",
                    "/output",
                    "--ir_datasets_id",
                    irds_dataset_id,
                    "--rerank",
                    "/output",
                ]
            )
        else:
            with gzip.open(run_file + "/rerank.jsonl.gz", "wt") as f:
                for _, i in run_df.iterrows():
                    i = i.to_dict()

                    for k in ["original_query", "original_document"]:
                        if k not in i:
                            i[k] = {}

                    if "text" not in i and "body" in i:
                        i["text"] = i["body"]

                    if "text" not in i:
                        raise ValueError(f'I expect a field "text", but only found fields {i.keys()}.')

                    f.write(json.dumps(i) + "\n")

        return run_file

    def index(self, approach, dataset):
        """
        Load an PyTerrier index from TIRA.
        """
        import pyterrier as pt

        from tira.ir_datasets_util import translate_irds_id_to_tirex

        ret = self.tira_client.get_run_output(approach, translate_irds_id_to_tirex(dataset)) + "/index"
        return pt.IndexFactory.of(os.path.abspath(ret))

    def from_submission(self, approach, dataset=None, datasets=None, file_to_re_rank=None):
        if self.__is_re_ranker(approach):
            return self.from_retriever_submission(approach, dataset, datasets=datasets, file_to_re_rank=file_to_re_rank)
        else:
            from tira.pyterrier_util import TiraRerankingTransformer

            return TiraRerankingTransformer(approach, self.tira_client, dataset, datasets)

    def __is_re_ranker(self, approach):
        if self.tira_client.input_run_in_sandbox(approach):
            # If the input run is in the sandbox, everything behaves as a re-ranker
            return True

        _, team, software = approach.split("/")
        software = self.tira_client.public_system_details(team, software)
        return software.get("ir_re_ranker", False)

    def from_retriever_submission(self, approach, dataset, previous_stage=None, datasets=None, file_to_re_rank=None):
        from tira.ir_datasets_loader import IrDatasetsLoader
        from tira.pyterrier_util import TiraSourceTransformer

        if file_to_re_rank:
            re_rank_dir = Path(self.tira_client.tira_cache_dir) / "extracted_datasets" / str(uuid.uuid4())
            log_file = Path(f"{self.tira_client.tira_cache_dir}/.archived/local-executions.jsonl")
            re_rank_dir = IrDatasetsLoader().reformat_to_re_rank_dataset(
                Path(file_to_re_rank), dataset, re_rank_dir, log_file
            )
            dataset = str(Path(re_rank_dir))

        ret = self.pd.from_retriever_submission(approach, dataset, previous_stage, datasets)
        return TiraSourceTransformer(ret)

    def transform_queries(self, approach, dataset, file_selection=("/*.jsonl", "/*.jsonl.gz"), prefix=""):
        from pyterrier.apply import generic

        ret = self.pd.transform_queries(approach, dataset, file_selection)
        cols = [i for i in ret.columns if i not in ["qid"]]
        ret = {str(i["qid"]): i for _, i in ret.iterrows()}

        def __transform_df(df):
            df = df.copy()
            for col in cols:
                df[prefix + col] = df["qid"].apply(lambda i: ret[str(i)][col])
            return df

        return generic(__transform_df)

    def transform_documents(self, approach, dataset, file_selection=("/*.jsonl", "/*.jsonl.gz"), prefix=""):
        from pyterrier.apply import generic

        ret = self.pd.transform_documents(approach, dataset, file_selection)
        cols = [i for i in ret.columns if i not in ["docno"]]
        ret = {str(i["docno"]): i for _, i in ret.iterrows()}

        def __transform_df(df):
            for col in cols:
                df[prefix + col] = df["docno"].apply(lambda i: ret[str(i)][col])
            return df

        return generic(__transform_df)

    @staticmethod
    def _get_features_from_row(row, cols, map_features=None):
        import numpy as np

        res = []

        for c in cols:
            if map_features is not None and c in map_features:
                f = map_features[c](row[c])
            else:
                f = row[c]

            if isinstance(f, (list, np.ndarray)):
                res.extend(f)
            else:
                res.append(f)

        return np.array(res)

    def _features_transformer(self, run, id_col, name, feature_selection=None, map_features=None):
        from tira.pyterrier_util import TiraApplyFeatureTransformer

        cols = [col for col in run.columns if col != id_col]
        if feature_selection is not None:
            cols = [col for col in cols if col in feature_selection]

        mapping = {str(row[id_col]): self._get_features_from_row(row, cols, map_features) for _, row in run.iterrows()}

        return TiraApplyFeatureTransformer(mapping, (id_col,), name)

    def doc_features(
        self, approach, dataset, file_selection=("/*.jsonl", "/*.jsonl.gz"), feature_selection=None, map_features=None
    ):
        run = self.pd.transform_documents(approach, dataset, file_selection)

        return self._features_transformer(run, "docno", "doc_features", feature_selection, map_features)

    def query_features(
        self, approach, dataset, file_selection=("/*.jsonl", "/*.jsonl.gz"), feature_selection=None, map_features=None
    ):
        run = self.pd.transform_queries(approach, dataset, file_selection)

        return self._features_transformer(run, "qid", "query_features", feature_selection, map_features)

    def reranker(self, approach, irds_id=None):
        from tira.pyterrier_util import TiraLocalExecutionRerankingTransformer

        return TiraLocalExecutionRerankingTransformer(approach, self.tira_client, irds_id=irds_id)


class PyTerrierAnceIntegration:
    """
    The pyterrier_ance integration to re-use cached ANCE indices. Wraps https://github.com/terrierteam/pyterrier_ance
    """

    def __init__(self, tira_client):
        self.tira_client = tira_client

    def ance_retrieval(self, dataset: str):
        """Load a cached pyterrier_ance.ANCEIndexer submitted as workshop-on-open-web-search/ows/pyterrier-anceindex
        from tira.

        References (for citation):
            https://arxiv.org/pdf/2007.00808.pdf
            https://github.com/microsoft/ANCE/

        Args:
            dataset (str): the dataset id, either an tira or ir_datasets id.

        Returns:
            pyterrier_ance.ANCERetrieval: the ANCE index.
        """
        from tira.ir_datasets_util import translate_irds_id_to_tirex

        ance_index = (
            Path(
                self.tira_client.get_run_output(
                    "ir-lab-sose-2024/ows/pyterrier-anceindex", translate_irds_id_to_tirex(dataset)
                )
            )
            / "anceindex"
        )
        ance_checkpoint = self.tira_client.load_resource("Passage_ANCE_FirstP_Checkpoint.zip")
        import pyterrier_ance

        return pyterrier_ance.ANCERetrieval(ance_checkpoint, ance_index)


class PyTerrierSpladeIntegration:
    """The pyt_splade integration to re-use cached Splade indices. Wraps https://github.com/cmacdonald/pyt_splade"""

    def __init__(self, tira_client):
        self.tira_client = tira_client

    def splade_index(self, dataset: str, approach: str = "workshop-on-open-web-search/naverlabseurope/Splade (Index)"):
        """
        Load a cached pyt_splade index submitted as the passed approach (default
        'workshop-on-open-web-search/naverlabseurope/Splade (Index)') from tira.

        References (for citation):
            https://github.com/naver/splade?tab=readme-ov-file#cite-scroll
            ToDo: Ask Thibault what to cite.

        Args:
            dataset (str): the dataset id, either an tira or ir_datasets id.
            approach (str, optional): the approach id, defaults
                'workshop-on-open-web-search/naverlabseurope/Splade (Index)'.

        Returns:
            The PyTerrier index suitable for retrieval.
        """
        import pyterrier as pt

        from tira.ir_datasets_util import translate_irds_id_to_tirex

        ret = (
            Path(
                self.tira_client.get_run_output(
                    "ir-lab-sose-2024/naverlabseurope/Splade (Index)", translate_irds_id_to_tirex(dataset)
                )
            )
            / "spladeindex"
        )
        return pt.IndexFactory.of(os.path.abspath(ret))


def pt_transformer(path):
    import pyterrier as pt

    if not pt.started():
        pt.init()
    # TODO hacked for the moment, in reality, we must delegate to the classes above.
    return pt.transformer.get_transformer(pt.io.read_results(path + "/output/run.txt"))
