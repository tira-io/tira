from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import pandas as pd

PANDAS_DTYPES = {
    "docno": str,
    "doc_id": str,
    "id": str,
    "qid": str,
    "query_id": str,
    "queryid": str,
    "docno": str,
    "doc_id": str,
    "docid": str,
}


class PandasIntegration:
    """Handling of inputs/outputs in TIRA with pandas. All methods here work in the TIRA sandbox without internet
    connection (when the data is mounted read-only)."""

    def __init__(self, tira_client):
        self.tira_client = tira_client

    def from_retriever_submission(
        self,
        approach: str,
        dataset: str,
        previous_stage: str = None,
        datasets: List[str] = None,
        for_ir_measures: bool = False,
    ):
        """Load a run file as pandas dataframe from tira. Compatible with PyTerrier.

        Args:
            approach (str): the approach for which the run should be loaded, in the format 'task/team/software'.
            dataset (str): the dataset id, either an tira or ir_datasets id.
            previous_stage (str, optional): The previous stage, in case the approach itself is ambigious. Defaults to
                None.
            datasets (List[str], optional): list of datasets to concat. Defaults to None.
            for_ir_measures (bool, optional): rename columns qid and docid to query_id respectively doc_id for direct
                re-use within ir-measures.

        Returns:
            pd.DataFrame: The run file parsed to a pandas DataFrame.
        """
        import pandas as pd

        from tira.ir_datasets_util import translate_irds_id_to_tirex

        task, team, software = approach.split("/")

        if dataset and datasets:
            raise ValueError(
                f"You can not pass both, dataset and datasets. Got dataset = {dataset} and datasets= {datasets}"
            )

        if not datasets:
            datasets = [dataset]

        df_ret = []
        for dataset in datasets:
            ret, run_id = self.tira_client.download_run(
                task, translate_irds_id_to_tirex(dataset), software, team, previous_stage, return_metadata=True
            )
            ret["qid"] = ret["query"].astype(str)
            ret["docno"] = ret["docid"].astype(str)
            del ret["query"]
            del ret["docid"]

            if for_ir_measures:
                ret["query_id"] = ret["qid"]
                ret["doc_id"] = ret["docno"]
                del ret["qid"]
                del ret["docno"]

            ret["tira_task"] = task
            ret["tira_dataset"] = dataset
            ret["tira_first_stage_run_id"] = run_id
            df_ret += [ret]

        return pd.concat(df_ret)

    def transform_queries(self, approach: str, dataset: "Optional[str]", format: str = "query-processor"):
        """Load and transform the query processing outputs specified by the approach on the dataset for direct re-use
        as a PyTerrier query transformation.

        Args:
            approach str: the approach for which the run should be loaded, in the format 'task/team/software'.
            dataset (str):the dataset id, either an tira or ir_datasets id.
            format (str, optional):  The format in which the queries are loaded.

        Raises:
            ValueError: If no approach with the identifier 'approach' was found or if there was an error parsing the
            outputs.

        Returns:
            pd.DataFrame: a DataFrame with the parsed query processing outputs compatible with PyTerrier query
            transformations.
        """
        import pandas as pd

        items = self.tira_client.iter_run_output(approach, dataset, format)

        return pd.DataFrame(items)

    def transform_documents(
        self, approach: str, dataset: "Optional[str]", format: str = "document-processor"
    ) -> "pd.DataFrame":
        """Load and transform the document processing outputs specified by the approach on the dataset for direct
        re-use as a PyTerrier document transformation.

        Args:
            approach str: the approach for which the run should be loaded, in the format 'task/team/software'.
            dataset (str):the dataset id, either an tira or ir_datasets id.
            format (str, optional): The format in which the documents are available.

        Raises:
            ValueError: If no approach with the identifier 'approach' was found or if there was an error parsing the
            outputs.

        Returns:
            pd.DataFrame: a DataFrame with the parsed document processing outputs compatible with PyTerrier document
            transformations.
        """
        import pandas as pd

        items = self.tira_client.iter_run_output(approach, dataset, format)

        return pd.DataFrame(items)

    def inputs(self, task, dataset=None, formats=("*.jsonl")):
        """Load the inputs to systems for a task from tira.

        Args:
            approach str: the approach for which the run should be loaded, in the format 'task/team/software'.
            dataset (str):the dataset id, either an tira or ir_datasets id.
            file_selection (Tuple[str,...], optional): The search glob to outputs specified by the approach on the
                dataset. Defaults to ('/*.jsonl', '/*.jsonl.gz').
            dtype (Tuple[str,...], optional): Transformations of the data types while loading with pandas. Defaults to
                PANDAS_DTYPES.

        Raises:
            ValueError: If the dataset is not public or does not exist.

        Returns:
            pd.DataFrame: A DataFrame with all inputs to systems.
        """
        import pandas as pd

        dataset_items = self.tira_client.iter_dataset(task, dataset, False, formats)

        return pd.DataFrame(dataset_items)

    def truths(self, task, dataset=None, formats=("*.jsonl")):
        """Load the truths, i.e., ground truth labels, for a task from tira.

        Args:
            approach str: the approach for which the run should be loaded, in the format 'task/team/software'.
            dataset (str):the dataset id, either an tira or ir_datasets id.
            file_selection (Tuple[str,...], optional): The search glob to outputs specified by the approach on the
                dataset. Defaults to ('/*.jsonl', '/*.jsonl.gz').
            dtype (Tuple[str,...], optional): Transformations of the data types while loading with pandas. Defaults to
                PANDAS_DTYPES.

        Raises:
            ValueError: If the truth is not public or does not exist.

        Returns:
            pd.DataFrame: A DataFrame with all the ground truth labels.
        """
        import pandas as pd

        dataset_items = self.tira_client.iter_dataset(task, dataset, True, formats)

        return pd.DataFrame(dataset_items)
