from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    import io
    from pathlib import Path
    from typing import Any, Dict, Optional, Union

    import pandas as pd

# .. todo:: this file needs further documentation


class TiraClient(ABC):
    @abstractmethod
    def all_softwares(self) -> "pd.DataFrame":
        pass

    @abstractmethod
    def docker_software() -> "Any":
        # .. todo:: typehint
        pass

    @abstractmethod
    def run_was_already_executed_on_dataset(self, approach, dataset) -> bool:
        # .. todo:: typehint
        pass

    @abstractmethod
    def get_run_output(self, approach, dataset, allow_without_evaluation=False) -> str:
        # .. todo:: typehint
        pass

    @abstractmethod
    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None) -> "Optional[Dict[str, str]]":
        # .. todo:: typehint
        pass

    def docker_registry(self):
        return 'registry.webis.de'

    @abstractmethod
    def create_upload_group(self, task_id: str, vm_id: str, display_name: str) -> "Optional[str]":
        pass

    @abstractmethod
    def upload_run(
        self,
        file_path: "Path",
        dataset_id: str,
        approach: "Optional[str]" = None,
        task_id: "Optional[str]" = None,
        vm_id: "Optional[str]" = None,
        upload_id: "Optional[str]" = None,
        allow_multiple_uploads: bool = False,
    ) -> bool:
        """
        Returns true if the upload was successfull, false if not, or none if it was already uploaded.
        """
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

    @abstractmethod
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

    @abstractmethod
    def download_dataset(self, task: str, dataset: str, truth_dataset: bool = False) -> str:
        """
        Download the dataset. Set truth_dataset to true to load the truth used for evaluations.
        """
        pass



def RestClient(base_url: "Optional[str]"=None, api_key: str=None, failsave_retries: int=5, failsave_max_delay: int=15, api_user_name: "Optional[str]"=None) -> TiraClient:
    from ._internal.rest_api_client import Client as TiraRestClient
    return TiraRestClient(base_url=base_url, api_key=api_key, failsave_retries=failsave_retries, failsave_max_delay=failsave_max_delay, api_user_name=api_user_name)

def LocalClient(directory='.', rest_client: "Optional[TiraClient]"=None) -> TiraClient:
    from ._internal.local_client import Client as TiraLocalClient
    return TiraLocalClient(directory=directory, rest_client=rest_client)