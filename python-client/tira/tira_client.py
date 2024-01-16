from abc import ABC
from typing import TYPE_CHECKING, Union, overload

if TYPE_CHECKING:
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
