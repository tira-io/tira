from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, NamedTuple, Optional

from .check_format import _fmt

if TYPE_CHECKING:
    from tira.tira_client import TiraClient


class WorkflowResult(NamedTuple):
    level: _fmt
    message: str
    run: Optional[Path]


class WorkflowBase:
    def __init__(self):
        self.workflow_configuration = None
        self.software_configuration = None

    def apply_configuration_and_throw_if_invalid(
        self, workflow_configuration: "Optional[Dict[str, Any]]", software: "Optional[Dict[str, Any]]"
    ):
        self.workflow_configuration = workflow_configuration
        self.software_configuration = software

    def run_workflow(
        self,
        system_inputs: Path,
        allow_network: bool,
        additional_volumes,
        cpu_count,
        mem_limit,
        gpu_count,
        gpu_device_ids,
        tira: "TiraClient",
        forward_environment_variables: "Optional[list[str]]" = None,
        mount_directory: "Optional[dict]" = None,
        cache_directory: "Optional[dict]" = None,
        platform: str = "linux/amd64",
    ):
        return WorkflowResult(_fmt.OK, "not implemented", None)

    def execute_monitored(self, method: Callable, forward_io: bool = False):
        import sys

        from tira.io_utils import MonitoredExecution, TeeStringIO

        stdout, stderr = None, None
        if forward_io:
            stdout = TeeStringIO(sys.stdout)
            stderr = TeeStringIO(sys.stderr)

        return MonitoredExecution(stdout, stderr).run(lambda i: method(i))
