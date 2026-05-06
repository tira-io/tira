import json
from pathlib import Path
from shutil import copyfile, copytree
from typing import Any, Callable, Dict, NamedTuple, Optional

from tira.third_party_integrations import temporary_directory
from tira.tira_client import TiraClient

from .check_format import _fmt, check_format, fmt_message, lines_if_valid


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
        gpu_device_ids,
        tira: "TiraClient",
        forward_environment_variables: "Optional[list[str]]" = None,
        mount_directory: "Optional[dict]" = None,
    ):
        return WorkflowResult(_fmt.OK, "not implemented", None)

    def execute_monitored(self, method: Callable):
        from tira.io_utils import MonitoredExecution

        return MonitoredExecution().run(lambda i: method(i))


class Pan26TextWatermarking(WorkflowBase):
    def apply_configuration_and_throw_if_invalid(
        self, workflow_configuration: "Optional[Dict[str, Any]]", software: "Optional[Dict[str, Any]]"
    ):
        workflow_required = ["obfuscation_image", "obfuscation_command"]
        software_required = ["image", "watermark_command", "detect_command"]

        for k in workflow_required:
            if not workflow_configuration or k not in workflow_configuration:
                raise ValueError(f"The workflow 'pan26-text-watermarking' requires a configuration for '{k}'.")

        for k in software_required:
            if not software or k not in software:
                raise ValueError(f"Software executed for 'pan26-text-watermarking' needs a configuration for '{k}'.")

        super().apply_configuration_and_throw_if_invalid(workflow_configuration, software)

    def run_workflow(
        self,
        system_inputs: Path,
        allow_network: bool,
        additional_volumes,
        cpu_count,
        mem_limit,
        gpu_device_ids,
        tira: "TiraClient",
        forward_environment_variables: "Optional[list[str]]" = None,
        mount_directory: "Optional[dict]" = None,
    ):
        ret = temporary_directory()
        (ret / "output").mkdir(parents=True, exist_ok=True)
        stderr = ret / "stderr.txt"
        stdout = ret / "stdout.txt"

        stderr.write_text(f"# Step 1: Watermarking with {self.software_configuration['watermark_command']}\n\n")
        stdout.write_text(f"# Step 1: Watermarking with {self.software_configuration['watermark_command']}\n\n")

        code, msg = check_format(system_inputs, "*.jsonl")
        if code != _fmt.OK:
            raise ValueError(f"Input is invalid (likely an configuration error): {msg}")

        watermarking_results = self.execute_monitored(
            lambda i: tira.local_execution.run(
                image=self.software_configuration["image"],
                command=self.software_configuration["watermark_command"],
                input_dir=system_inputs,
                output_dir=i,
                allow_network=allow_network,
                additional_volumes=additional_volumes,
                cpu_count=cpu_count,
                mem_limit=mem_limit,
                gpu_device_ids=gpu_device_ids,
                forward_environment_variables=forward_environment_variables,
            )
        )

        copytree(watermarking_results / "output", ret / "output" / "01-watermarking")
        stderr.write_text(stderr.read_text() + "\n" + (watermarking_results / "stderr.txt").read_text())
        stdout.write_text(stdout.read_text() + "\n" + (watermarking_results / "stdout.txt").read_text())

        code, msg = check_format(ret / "output" / "01-watermarking", "*.jsonl")

        txt = "# Step 2: Check Format\n\t" + fmt_message(msg, code)
        stderr.write_text(stderr.read_text() + "\n\n" + txt)
        stdout.write_text(stdout.read_text() + "\n\n" + txt)

        if code != _fmt.OK:
            return WorkflowResult(
                _fmt.ERROR,
                f"Watermarking the text failed. The command \"{self.software_configuration['watermark_command']}\" did not produce a valid jsonl file.",
                ret,
            )

        obfuscation_inputs = temporary_directory()
        copytree(watermarking_results / "output", obfuscation_inputs / "01-watermarking")
        copytree(system_inputs, obfuscation_inputs / "original")

        obfuscation_results = self.execute_monitored(
            lambda i: tira.local_execution.run(
                image=self.workflow_configuration["obfuscation_image"],
                command=self.workflow_configuration["obfuscation_command"],
                input_dir=obfuscation_inputs,
                output_dir=i,
                allow_network=allow_network,
                additional_volumes=additional_volumes,
                cpu_count=cpu_count,
                mem_limit=mem_limit,
                gpu_device_ids=gpu_device_ids,
            )
        )

        stderr_txt = (
            stderr.read_text()
            + f"\n\n# Step 3: Obfuscation with {self.workflow_configuration['obfuscation_command']}\n\n"
        )
        stdout_txt = (
            stdout.read_text()
            + f"\n\n# Step 3: Obfuscation with {self.workflow_configuration['obfuscation_command']}\n\n"
        )

        stderr_txt += (obfuscation_results / "stderr.txt").read_text()
        stdout_txt += (obfuscation_results / "stdout.txt").read_text()

        copytree(obfuscation_results / "output", ret / "output" / "02-obfuscation")
        code, msg = check_format(ret / "output" / "02-obfuscation", "*.jsonl")

        txt = "\n# Step 4: Check Obfuscation Results\n\t" + fmt_message(msg, code)

        stdout.write_text(stdout_txt + txt)
        stderr.write_text(stderr_txt + txt)

        if code != _fmt.OK:
            return WorkflowResult(_fmt.ERROR, "The step 2 (obfuscation) failed. No valid jsonl file was produced.", ret)

        stderr_txt = (
            stderr.read_text() + f"\n\n# Step 5: Detection with {self.software_configuration['detect_command']}\n\n"
        )
        stdout_txt = (
            stdout.read_text() + f"\n\n# Step 5: Detection with {self.software_configuration['detect_command']}\n\n"
        )

        detection_inputs = temporary_directory()
        detection_lines = []
        for i in lines_if_valid(obfuscation_results / "output", "*.jsonl"):
            del i["truth_label"]
            detection_lines.append(json.dumps(i))

        (detection_inputs / "texts.jsonl").write_text("\n".join(detection_lines))

        detection_results = self.execute_monitored(
            lambda i: tira.local_execution.run(
                image=self.software_configuration["image"],
                command=self.software_configuration["detect_command"],
                input_dir=detection_inputs,
                output_dir=i,
                allow_network=allow_network,
                additional_volumes=additional_volumes,
                cpu_count=cpu_count,
                mem_limit=mem_limit,
                gpu_device_ids=gpu_device_ids,
            )
        )

        stderr_txt += (detection_results / "stderr.txt").read_text()
        stdout_txt += (detection_results / "stdout.txt").read_text()

        copytree(detection_results / "output", ret / "output" / "03-detection")
        code, msg = check_format(ret / "output" / "03-detection", "*.jsonl")

        txt = "\n# Step 6: Check Detection Results\n\t" + fmt_message(msg, code)

        stdout.write_text(stdout_txt + txt)
        stderr.write_text(stderr_txt + txt)

        if code != _fmt.OK:
            return WorkflowResult(
                _fmt.ERROR,
                f"The detection step failed. The command \"{self.software_configuration['detect_command']}\" did not produce a valid jsonl file.",
                ret,
            )

        return WorkflowResult(_fmt.OK, "workflow executed on 'pan26-text-watermarking'.", ret)


WORKFLOWS = {
    "pan26-text-watermarking": Pan26TextWatermarking,
}


class WorkflowResult(NamedTuple):
    level: _fmt
    message: str
    run: Optional[Path]


def run_workflow(
    system_inputs: Path,
    workflow: str,
    workflow_configuration: "Optional[Dict[str, Any]]",
    software: "Optional[Dict[str, Any]]" = None,
    allow_network: bool = False,
    additional_volumes=None,
    cpu_count=1,
    mem_limit=None,
    gpu_device_ids=None,
    tira: "Optional[TiraClient]" = None,
    forward_environment_variables: "Optional[list[str]]" = None,
    mount_directory: "Optional[dict]" = None,
) -> WorkflowResult:
    """Run the specified workflow. Provides debug messages intended for users.

    Args:
        system_inputs (Path): The input to the software.
        workflow (str): The workflow to run.
        workflow_configuration (Optional[Dict[str, Any]]): the configuration of the workflow.
        software (Optional[Dict[str, Any]]): the software to execute in the workflow.
    """
    if workflow not in WORKFLOWS:
        msg = f"No workflow with the identifyier '{workflow}' exists."
        return WorkflowResult(_fmt.ERROR, msg, None)

    workflow_impl = WORKFLOWS[workflow]()
    try:
        workflow_impl.apply_configuration_and_throw_if_invalid(workflow_configuration, software)
    except Exception as e:
        return WorkflowResult(_fmt.ERROR, str(e), None)

    if not tira:
        tira = TiraClient()

    try:
        return workflow_impl.run_workflow(
            system_inputs,
            allow_network,
            additional_volumes,
            cpu_count,
            mem_limit,
            gpu_device_ids,
            tira,
            forward_environment_variables,
            mount_directory,
        )
    except Exception as e:
        return WorkflowResult(_fmt.ERROR, str(e), None)
