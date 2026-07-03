import unittest

from ..format_check import _ERROR, _OK, JSONL_OUTPUT_VALID


def mocked_tira_client():
    return None


def run_worklow(workflow_name, workflow_config, software):
    from tira.workflows import run_workflow as rw

    tira_client = mocked_tira_client()
    return rw(
        system_inputs=JSONL_OUTPUT_VALID,
        workflow=workflow_name,
        workflow_configuration=workflow_config,
        software=software,
        tira=tira_client,
    )


class TestErrorMessageWorkflows(unittest.TestCase):
    def test_fails_for_non_existing_workflow_01(self):
        expected = [_ERROR, "No workflow with the identifyier 'non-existing-workflow' exists."]
        workflow_name = "non-existing-workflow"
        workflow_config = {}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_non_existing_workflow_02(self):
        expected = [_ERROR, "No workflow with the identifyier '1non-existing-workflow1' exists."]
        workflow_name = "1non-existing-workflow1"
        workflow_config = {}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_obfuscation_image(self):
        expected = [_ERROR, "The workflow 'pan26-text-watermarking' requires a configuration for 'obfuscation_image'."]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_obfuscation_command(self):
        expected = [
            _ERROR,
            "The workflow 'pan26-text-watermarking' requires a configuration for 'obfuscation_command'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01"}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_software_image(self):
        expected = [
            _ERROR,
            "Software executed for 'pan26-text-watermarking' needs a configuration for 'image'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01", "obfuscation_command": "some-command"}
        software = {}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_watermark_command(self):
        expected = [
            _ERROR,
            "Software executed for 'pan26-text-watermarking' needs a configuration for 'watermark_command'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01", "obfuscation_command": "some-command"}
        software = {"image": "some-image"}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_fails_for_missing_detect_command(self):
        expected = [
            _ERROR,
            "Software executed for 'pan26-text-watermarking' needs a configuration for 'detect_command'.",
        ]
        workflow_name = "pan26-text-watermarking"
        workflow_config = {"obfuscation_image": "some-obfuscation-image-01", "obfuscation_command": "some-command"}
        software = {"image": "some-image", "watermark_command": "some-command"}
        actual = run_worklow(workflow_name, workflow_config, software)
        self.assertEqual(expected[0], actual[0])
        self.assertEqual(expected[1], actual[1])

    def test_dispatches_workflow_arguments_by_name(self):
        import tira.workflows as workflows

        class CapturingWorkflow(workflows.WorkflowBase):
            captured = None

            def run_workflow(
                self,
                system_inputs,
                allow_network,
                additional_volumes,
                cpu_count,
                mem_limit,
                gpu_count,
                gpu_device_ids,
                tira,
                forward_environment_variables=None,
                mount_directory=None,
                cache_directory=None,
                platform="linux/amd64",
            ):
                CapturingWorkflow.captured = {
                    "system_inputs": system_inputs,
                    "allow_network": allow_network,
                    "additional_volumes": additional_volumes,
                    "cpu_count": cpu_count,
                    "mem_limit": mem_limit,
                    "gpu_count": gpu_count,
                    "gpu_device_ids": gpu_device_ids,
                    "tira": tira,
                    "forward_environment_variables": forward_environment_variables,
                    "mount_directory": mount_directory,
                    "cache_directory": cache_directory,
                    "platform": platform,
                }
                return workflows.WorkflowResult(_OK, "ok", None)

        workflow_name = "capturing-workflow"
        original = workflows.WORKFLOWS.get(workflow_name)
        workflows.WORKFLOWS[workflow_name] = CapturingWorkflow

        try:
            actual = workflows.run_workflow(
                system_inputs=JSONL_OUTPUT_VALID,
                workflow=workflow_name,
                workflow_configuration={},
                software={},
                allow_network=True,
                additional_volumes=["/tmp/data:/data:ro"],
                cpu_count=4,
                gpu_count=2,
                mem_limit="8g",
                gpu_device_ids=["0", "1"],
                tira="mocked-tira-client",
                forward_environment_variables=["OPENAI_API_KEY"],
                mount_directory={"CACHE_DIR": {"path": "/tmp/cache", "mode": "rw"}},
                cache_directory={"CACHE_DIR": "/tmp/cache"},
                platform="linux/arm64",
            )
        finally:
            if original is None:
                del workflows.WORKFLOWS[workflow_name]
            else:
                workflows.WORKFLOWS[workflow_name] = original

        self.assertEqual(_OK, actual[0])
        self.assertEqual(JSONL_OUTPUT_VALID, CapturingWorkflow.captured["system_inputs"])
        self.assertTrue(CapturingWorkflow.captured["allow_network"])
        self.assertEqual(["/tmp/data:/data:ro"], CapturingWorkflow.captured["additional_volumes"])
        self.assertEqual(4, CapturingWorkflow.captured["cpu_count"])
        self.assertEqual("8g", CapturingWorkflow.captured["mem_limit"])
        self.assertEqual(2, CapturingWorkflow.captured["gpu_count"])
        self.assertEqual(["0", "1"], CapturingWorkflow.captured["gpu_device_ids"])
        self.assertEqual("mocked-tira-client", CapturingWorkflow.captured["tira"])
        self.assertEqual(["OPENAI_API_KEY"], CapturingWorkflow.captured["forward_environment_variables"])
        self.assertEqual(
            {"CACHE_DIR": {"path": "/tmp/cache", "mode": "rw"}},
            CapturingWorkflow.captured["mount_directory"],
        )
        self.assertEqual({"CACHE_DIR": "/tmp/cache"}, CapturingWorkflow.captured["cache_directory"])
        self.assertEqual("linux/arm64", CapturingWorkflow.captured["platform"])
