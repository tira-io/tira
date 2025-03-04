from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Union, overload

if TYPE_CHECKING:
    import io
    from typing import Any, Dict, Optional

    import pandas as pd

# .. todo:: this file needs further documentation


class TiraClient(ABC):
    def all_datasets(self) -> "pd.DataFrame":
        pass

    def all_softwares(self) -> "pd.DataFrame":
        pass

    def print_overview_of_all_software(self) -> None:
        pass

    def all_evaluators(self) -> "pd.DataFrame":
        pass

    def all_evaluated_appraoches(self) -> "pd.DataFrame":
        pass

    def docker_software() -> "Any":
        # .. todo:: typehint
        pass

    def run_was_already_executed_on_dataset(self, approach, dataset) -> bool:
        # .. todo:: typehint
        pass

    def get_run_output(self, approach, dataset, allow_without_evaluation=False) -> str:
        # .. todo:: typehint
        pass

    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None) -> "Optional[Dict[str, str]]":
        # .. todo:: typehint
        pass

    def docker_registry(self):
        return "registry.webis.de"

    def modify_task(self, task_id: str, to_rename: "Dict[str, Any]"):
        # .. todo:: typehint
        pass

    @overload
    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: bool = False,
    ) -> "tuple[pd.DataFrame, str]":
        # .. todo:: typehint
        ...

    @overload
    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: bool = False,
    ) -> "pd.DataFrame":
        # .. todo:: typehint
        ...

    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: bool = False,
    ) -> "Union[pd.DataFrame, tuple[pd.DataFrame, str]]":
        # .. todo:: typehint
        pass

    def create_new_upload(self, task_id: str, vm_id: str) -> "Optional[str]":
        """
        Creates a new upload and returns the newly created id. Returns None on failure.
        """
        pass

    def submit_run(self, task_id: str, vm_id: str, dataset_id: str, upload_id: str, run: "io.IOBase") -> bool:
        """
        Submits the runfile located at `run` for the given task and vm for the given upload id. Returns true on success,
        false  otherwise.
        """
        pass

    def submit_code(
        self,
        path: Path,
        task_id: str,
        dataset_id: "Optional[str]" = None,
        user_id: "Optional[str]" = None,
        docker_file: "Optional[Path]" = None,
    ):
        """Build a tira submission from a git repository.

        Args:
            path (Path): The path to the directory that contains the submission. The path points to the directory used as root for the docker build and must be in a git repository.
            task_id (str): The ID of the TIRA task to which the submissions should be made.
            dataset_id (str, optional): The ID of the TIRA dataset on which the submission is to be tested. If no dataset is passed, the submission will be tested on a small publicly available smoke test dataset for the task.
            user_id (str, optional): The ID of the TIRA team that makes the submission. Is only required if a user has multiple teams.
            docker_file (Path, optional): The Dockerfile to build the submission within the repository. Defaults to None to use path/Dockerfile.
        """
        raise ValueError("no git repository....")

    def __extract_dataset_identifier(self, dataset: any):
        """Extract the dataset identifier from a passed object.

        Args:
            dataset (any): Some representation of dataset.

        Returns:
            Optional[dict]: The dataset identifier if available.
        """
        if hasattr(dataset, "irds_ref"):
            return self.__extract_dataset_identifier(dataset.irds_ref())
        if hasattr(dataset, "dataset_id"):
            return dataset.dataset_id()
        return dataset

    def __matching_dataset(self, datasets, dataset_identifier) -> "Optional[dict]":
        """Find the dataset identified by the passed dataset_identifier in all passed datasets.

        Args:
            datasets (List[dict]): TIRA representations of datasets.
            dataset_identifier (_type_): identifier of the dataset to be found.

        Returns:
            Optional[dict]: The TIRA representation of the dataset if found in the datasets.
        """
        datasets = [i for i in datasets if "id" in i and len(i["id"]) > 2]

        for dataset in datasets:
            if dataset_identifier and dataset["id"] == dataset_identifier:
                return dataset

        if len(dataset_identifier.split("/")) == 2:
            task_identifier, dataset_in_task = dataset_identifier.split("/")

            for dataset in datasets:
                if "default_task" not in dataset or not dataset["default_task"]:
                    continue

                if not task_identifier or not dataset_in_task:
                    continue

                if task_identifier == dataset["default_task"] and dataset_in_task == dataset["id"]:
                    return dataset

        for dataset in datasets:
            if "ir_datasets_id" not in dataset or not dataset["ir_datasets_id"] or len(dataset["ir_datasets_id"]) < 3:
                continue

            if dataset_identifier and dataset_identifier == dataset["ir_datasets_id"]:
                return dataset
