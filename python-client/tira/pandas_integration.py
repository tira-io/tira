from typing import List, Tuple

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

    def __matching_files(self, approach, dataset, file_selection):
        from glob import glob

        from tira.ir_datasets_util import translate_irds_id_to_tirex

        ret = set()

        if type(file_selection) is str:
            file_selection = [file_selection]

        for glob_entry in file_selection:
            glob_entry = self.tira_client.get_run_output(approach, (translate_irds_id_to_tirex(dataset))) + glob_entry
            for i in glob(glob_entry):
                ret.add(i)

        return sorted(list(ret))

    def __extract_task_and_dataset_id(self, task, dataset):
        if dataset is None and task and len(task.split("/")) == 2:
            task, dataset = task.split("/")
        elif dataset is None:
            task, dataset = None, task

        return task, dataset

    def transform_queries(
        self, approach: str, dataset: str, file_selection: Tuple[str, ...] = ("/*.jsonl", "/*.jsonl.gz")
    ):
        """Load and transform the query processing outputs specified by the approach on the dataset for direct re-use
        as a PyTerrier query transformation.

        Args:
            approach str: the approach for which the run should be loaded, in the format 'task/team/software'.
            dataset (str):the dataset id, either an tira or ir_datasets id.
            file_selection (Tuple[str,...], optional): The search glob to outputs specified by the approach on the
                dataset. Defaults to ('/*.jsonl', '/*.jsonl.gz').

        Raises:
            ValueError: If no approach with the identifier 'approach' was found or if there was an error parsing the
            outputs.

        Returns:
            pd.DataFrame: a DataFrame with the parsed query processing outputs compatible with PyTerrier query
            transformations.
        """
        import pandas as pd

        matching_files = self.__matching_files(approach, dataset, file_selection)

        if len(matching_files) == 0:
            raise ValueError(
                f"Could not find a matching query output. Found: {matching_files}. Please specify the file_selection to"
                " resolve this."
            )

        ret = pd.read_json(matching_files[0], lines=True, dtype={"qid": str, "query": str, "query_id": str})
        if "qid" not in ret and "query_id" in ret:
            ret["qid"] = ret["query_id"]
            del ret["query_id"]

        return ret

    def transform_documents(self, approach, dataset, file_selection=("/*.jsonl", "/*.jsonl.gz")):
        """Load and transform the document processing outputs specified by the approach on the dataset for direct
        re-use as a PyTerrier document transformation.

        Args:
            approach str: the approach for which the run should be loaded, in the format 'task/team/software'.
            dataset (str):the dataset id, either an tira or ir_datasets id.
            file_selection (Tuple[str,...], optional): The search glob to outputs specified by the approach on the
                dataset. Defaults to ('/*.jsonl', '/*.jsonl.gz').

        Raises:
            ValueError: If no approach with the identifier 'approach' was found or if there was an error parsing the
            outputs.

        Returns:
            pd.DataFrame: a DataFrame with the parsed document processing outputs compatible with PyTerrier document
            transformations.
        """
        import pandas as pd

        matching_files = self.__matching_files(approach, dataset, file_selection)
        if len(matching_files) == 0:
            raise ValueError(
                "Could not find a matching document output. Used file_selection: "
                + str(file_selection)
                + ". Please specify the file_selection to resolve this."
            )

        ret = pd.read_json(matching_files[0], lines=True, dtype={"docno": str, "doc_id": str})

        if "doc_id" in ret.columns and "docno" not in ret.columns:
            ret["docno"] = ret["doc_id"]
            del ret["doc_id"]
        return ret

    def __matching_dataset_files(self, task, dataset, truth_dataset, file_selection):
        from glob import glob

        ret = []
        local_dir = self.tira_client.download_dataset(task, dataset, truth_dataset)

        for glob_entry in file_selection:
            for i in glob(local_dir + glob_entry):
                ret += [i]

        return ret

    def inputs(self, task, dataset=None, file_selection=("/*.jsonl", "/*.jsonl.gz"), dtype=PANDAS_DTYPES):
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

        task, dataset = self.__extract_task_and_dataset_id(task, dataset)
        matching_files = self.__matching_dataset_files(task, dataset, False, file_selection)

        if len(matching_files) == 0:
            raise ValueError(
                "Could not find a dataset output. Used file_selection: "
                + str(file_selection)
                + ". Please specify the file_selection to resolve this."
            )

        return pd.read_json(matching_files[0], lines=True, dtype=dtype)

    def truths(self, task, dataset=None, file_selection=("/*.jsonl", "/*.jsonl.gz"), dtype=PANDAS_DTYPES):
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

        task, dataset = self.__extract_task_and_dataset_id(task, dataset)
        matching_files = self.__matching_dataset_files(task, dataset, True, file_selection)

        if len(matching_files) == 0:
            raise ValueError(
                "Could not find a dataset output. Used file_selection: "
                + str(file_selection)
                + ". Please specify the file_selection to resolve this."
            )

        return pd.read_json(matching_files[0], lines=True, dtype=dtype)
