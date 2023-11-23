from abc import ABC
from typing import TYPE_CHECKING, Literal, overload

if TYPE_CHECKING:
    from typing import Any, Optional

    import pandas as pd

# TODO: this file needs further documentation


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
        # TODO: typehint
        pass

    def run_was_already_executed_on_dataset(self, approach, dataset) -> bool:
        # TODO: typehint
        pass

    def get_run_output(self, approach, dataset, allow_without_evaluation=False) -> str:
        # TODO: typehint
        pass

    def get_run_execution_or_none(self, approach, dataset, previous_stage_run_id=None) -> "Optional[Dict[str, str]]":
        # TODO: typehint
        pass

    @overload
    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: Literal[True] = False,
    ) -> "tuple[pd.DataFrame, str]":
        # TODO: typehint
        ...

    @overload
    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: Literal[False] = False,
    ) -> "pd.DataFrame":
        # TODO: typehint
        ...

    def download_run(
        self,
        task,
        dataset,
        software,
        team=None,
        previous_stage=None,
        return_metadata: bool = False,
    ) -> "pd.DataFrame | tuple[pd.DataFrame, str]":
        # TODO: typehint
        pass
