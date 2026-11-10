import json
import re
import unittest
from pathlib import Path

from tira.workflows import run_workflow

from ..format_check import _ERROR, _OK

SUMMARY = "summary.md"
TASK = Path(__file__).parent.parent / "resources" / "example-datasets" / "coding-agent-sorting-tasks" / "sorting-python"


def mocked_tira_client(submission=None):
    class MockedLocalExecution:
        def __init__(self):
            self.calls = []
            self.builds = []

        def build_docker_image(self, path, tag, dockerfile):
            self.builds.append((path, tag, dockerfile))

        def run(self, image, command, input_dir, output_dir, **kwargs):
            call = {"image": image, "command": command, "input_dir": input_dir, "kwargs": kwargs}
            call["input_files"] = sorted(
                str(i.relative_to(input_dir)) for i in Path(input_dir).rglob("*") if i.is_file()
            )
            call["readme"] = (
                (Path(input_dir) / "README.md").read_text() if (Path(input_dir) / "README.md").exists() else None
            )
            self.calls.append(call)
            if image == "agent" and command.endswith(".step-succeeded"):
                if "fail" not in command:
                    (output_dir / ".step-succeeded").write_text("")
            elif image == "agent":
                (output_dir / "prompt.txt").write_text("the prompt of this run\n")
                print("Tool output\n\nThe solution is written and validated.\nIt sorts.\n\nChanges    +3 -0")
                if submission is not None:
                    if "command" in submission:
                        (output_dir / "submission-metadata.yml").write_text(f"command: {submission['command']}\n")
                    if submission.get("dockerfile") != "":
                        (output_dir / "solution").mkdir(exist_ok=True)
                        devcontainer = (Path(input_dir) / ".devcontainer" / "Dockerfile").read_text()
                        # an agent that was given feedback fixes its solution
                        dockerfile = (
                            devcontainer
                            if (input_dir / "feedback" / "feedback.md").exists()
                            else submission.get("dockerfile", devcontainer)
                        )
                        feedback_file = input_dir / "feedback" / "feedback.md"
                        reviewing = feedback_file.exists() and "built and executed" in feedback_file.read_text()
                        if reviewing:
                            self.review_files = sorted(i.name for i in (input_dir / "feedback").iterdir())
                            self.reviews = getattr(self, "reviews", 0) + 1
                        previous = output_dir / "solution" / "Dockerfile"
                        if reviewing and previous.exists():
                            # the solution of the previous run is kept
                            dockerfile = previous.read_text().replace("\nCOPY . /solution\n", "")
                        if reviewing and self.reviews <= getattr(self, "review_edits", 0):
                            dockerfile += "\n# modified after review"
                        previous.write_text(dockerfile + "\nCOPY . /solution\n")
                        self.feedback = (
                            (input_dir / "feedback" / "feedback.md").read_text()
                            if (input_dir / "feedback" / "feedback.md").exists()
                            else None
                        )
            elif "evaluator" in image:
                (output_dir / "evaluation.prototext").write_text('measure { key: "accuracy" value: "1.0" }')
            elif getattr(self, "empty_runs", 0) > 0:
                self.empty_runs -= 1
                print("SyntaxError in sort.jl")
            else:
                (output_dir / "predictions.jsonl").write_text("")

    class MockedTiraClient:
        def __init__(self):
            self.local_execution = MockedLocalExecution()

        def _resolve_evaluator_image(self, dataset_path, evaluator_config, image, print_message, dry_run):
            return "built-evaluator" if (dataset_path / image).is_dir() else image

    return MockedTiraClient()


def run(submission, **config):
    tira = mocked_tira_client(submission)
    configuration = {
        "task_directory": str(TASK),
        "allowed_hostnames": ["api.openai.com"],
        "evaluator_image": "evaluator:latest",
        "review_rounds": 0,
        **config,
    }
    result = run_workflow(
        system_inputs=TASK,
        workflow="sandboxed-coding-agent",
        workflow_configuration=configuration,
        software={"image": "agent", "command": "run-agent"},
        tira=tira,
    )
    return result, tira.local_execution.calls


class TestSandboxedCodingAgent(unittest.TestCase):
    def test_steps_run_in_agent_image_before_the_agent(self):
        steps = [{"name": "hello", "command": "echo hi"}, {"name": "tools", "command": "ls"}]
        result, calls = run({"command": "sort"}, agent_steps=steps)
        self.assertEqual(_OK, result.level)
        self.assertEqual(["echo hi && touch /tira-data/output/.step-succeeded"], [calls[0]["command"]])
        self.assertEqual(["run-agent"], [c["command"] for c in calls[2:3]])
        self.assertTrue((result.run / "01-hello").is_dir())
        self.assertEqual(
            "echo hi && touch /tira-data/output/.step-succeeded\n",
            (result.run / "01-hello" / "command.txt").read_text(),
        )
        self.assertTrue((result.run / "01-hello" / "input" / "README.md").is_file())

    def test_result_is_packaged_and_the_submission_is_built_by_the_workflow(self):
        tira = mocked_tira_client({"command": "sort"})
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={
                "task_directory": str(TASK),
                "evaluator_image": "evaluator:latest",
                "review_rounds": 0,
            },
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        self.assertEqual(_OK, result.level)
        self.assertEqual(
            ["source-code.zip", "submission-metadata.yml"],
            sorted(i.name for i in (result.run / "01-result").iterdir() if i.suffix in [".zip", ".yml"]),
        )
        self.assertEqual(1, len(tira.local_execution.builds))
        self.assertEqual(tira.local_execution.builds[0][1], tira.local_execution.calls[1]["image"])

    def test_dockerfile_must_extend_the_devcontainer(self):
        result, calls = run({"command": "sort", "dockerfile": "FROM python:3.12"}, agent_retries=0)
        self.assertEqual(_ERROR, result.level)
        self.assertIn("devcontainer", result.message)
        self.assertEqual(1, len(calls))

    def test_agent_is_started_again_with_feedback_if_the_solution_is_rejected(self):
        tira = mocked_tira_client({"command": "sort", "dockerfile": "FROM python:3.12"})
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={
                "task_directory": str(TASK),
                "evaluator_image": "evaluator:latest",
                "review_rounds": 0,
            },
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        self.assertEqual(_OK, result.level)
        self.assertEqual(["agent", "agent"], [c["image"] for c in tira.local_execution.calls[:2]])
        self.assertIn("rejected", tira.local_execution.feedback)
        self.assertTrue(
            (result.run / "01-result-attempt-1" / "stdout.txt").exists()
            or (result.run / "01-result-attempt-1").is_dir()
        )
        self.assertTrue((result.run / "01-result" / "source-code.zip").is_file())

    def test_agent_is_started_again_if_the_submission_produces_no_predictions(self):
        tira = mocked_tira_client({"command": "sort"})
        tira.local_execution.empty_runs = 2
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={
                "task_directory": str(TASK),
                "evaluator_image": "evaluator:latest",
                "review_rounds": 0,
            },
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        self.assertEqual(_OK, result.level)
        self.assertEqual(3, [c["image"] for c in tira.local_execution.calls].count("agent"))
        self.assertIn("wrote no files", tira.local_execution.feedback)
        self.assertTrue((result.run / "05-predictions-attempt-1").is_dir())
        self.assertTrue((result.run / "06-results" / "output" / "evaluation.prototext").is_file())

    def test_failing_submission_is_an_error_after_all_attempts(self):
        tira = mocked_tira_client({"command": "sort"})
        tira.local_execution.empty_runs = 10
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={
                "task_directory": str(TASK),
                "evaluator_image": "evaluator:latest",
                "review_rounds": 0,
                "agent_retries": 1,
            },
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        self.assertEqual(_ERROR, result.level)
        self.assertIn("wrote no files", result.message)
        self.assertIn("SyntaxError", (result.run / "05-predictions" / "stdout.txt").read_text())

    def test_agent_reviews_the_evaluation_and_keeps_an_unchanged_solution(self):
        tira = mocked_tira_client({"command": "sort"})
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={"task_directory": str(TASK), "evaluator_image": "evaluator:latest"},
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        self.assertEqual(_OK, result.level)
        self.assertEqual(
            ["agent", "tira-submission-sorting-python", "evaluator:latest", "agent"],
            [c["image"] for c in tira.local_execution.calls],
        )
        self.assertEqual(
            ["evaluation.prototext", "feedback.md", "stderr.txt", "stdout.txt"], tira.local_execution.review_files
        )
        self.assertTrue((result.run / "06-results" / "output" / "evaluation.prototext").is_file())
        self.assertIn("accuracy", result.message)

    def test_agent_modifies_its_solution_after_review_and_is_evaluated_again(self):
        tira = mocked_tira_client({"command": "sort"})
        tira.local_execution.review_edits = 1
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={
                "task_directory": str(TASK),
                "evaluator_image": "evaluator:latest",
                "review_rounds": 2,
            },
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        self.assertEqual(_OK, result.level)
        self.assertEqual(2, [c["image"] for c in tira.local_execution.calls].count("evaluator:latest"))
        self.assertEqual(3, [c["image"] for c in tira.local_execution.calls].count("agent"))
        self.assertTrue((result.run / "05-predictions-attempt-1").is_dir())
        self.assertTrue((result.run / "06-results" / "output" / "evaluation.prototext").is_file())

    def test_stop_after_result_does_not_build_or_evaluate(self):
        result, calls = run({"command": "sort"}, stop_after_step="result")
        self.assertEqual(_OK, result.level)
        self.assertEqual(1, len(calls))
        self.assertTrue((result.run / "01-result" / "source-code.zip").is_file())

    def test_failing_step_stops_the_workflow(self):
        steps = [{"name": "hello", "command": "fail"}, {"name": "tools", "command": "ls"}]
        result, calls = run({"command": "sort"}, agent_steps=steps)
        self.assertEqual(_ERROR, result.level)
        self.assertEqual(1, len(calls))
        self.assertIn("hello", result.message)

    def test_stop_after_step(self):
        steps = [{"name": "hello", "command": "echo"}, {"name": "tools", "command": "ls"}]
        result, calls = run({"command": "sort"}, agent_steps=steps, stop_after_step="hello")
        self.assertEqual(_OK, result.level)
        self.assertEqual(1, len(calls))

    def test_dataset_continues_with_the_next_task_after_a_failure(self):
        tira = mocked_tira_client(None)
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={
                "dataset_directory": str(TASK.parent),
                "evaluator_image": "evaluator:latest",
                "review_rounds": 0,
                "agent_retries": 2,
            },
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        self.assertEqual(_ERROR, result.level)
        self.assertEqual(9, len(tira.local_execution.calls))  # the agent is tried 3 times for each of the 3 tasks
        message = re.sub(r"\x1b\[[0-9;]*m", "", result.message)
        self.assertIn("✖ sorting-python:", message)
        self.assertIn("✖ sorting-julia:", message)
        self.assertIn("✖ 0 of 3 tasks succeeded.", message)

    def test_agent_only_sees_train_split_and_stripped_readme(self):
        _, calls = run({"command": "sort"})

        agent = calls[0]
        self.assertEqual(
            ["README.md", "STAGE.md", "inputs/train.jsonl", "truths/train.jsonl"],
            [i for i in agent["input_files"] if not i.startswith(".devcontainer/")],
        )
        self.assertIn(".devcontainer/Dockerfile", agent["input_files"])
        self.assertIn("# Sort a List of Integers", agent["readme"])
        self.assertNotIn("tira_configs", agent["readme"])
        self.assertEqual(["api.openai.com"], agent["kwargs"]["network_allowlist"])
        self.assertFalse(agent["kwargs"]["allow_network"])

    def test_missing_submission_is_an_error(self):
        result, calls = run(None, agent_retries=0)
        self.assertEqual(_ERROR, result.level)
        self.assertIn("submission-metadata.yml", result.message)
        self.assertEqual(1, len(calls))

    def test_invalid_submission_is_an_error(self):
        result, calls = run({"command": " "})
        self.assertEqual(_ERROR, result.level)
        self.assertIn("command", result.message)

    def test_stage_records_the_input_and_prompt_of_each_agent_run(self):
        result, calls = run({"command": "sort"})

        stage = result.run / "01-result"
        self.assertEqual("the prompt of this run\n", (stage / "prompt.txt").read_text())
        self.assertEqual("run-agent\n", (stage / "command.txt").read_text())
        self.assertTrue((stage / "input" / "README.md").is_file())
        self.assertNotIn("tira_configs", (stage / "input" / "README.md").read_text())
        manifest = (stage / "input" / "manifest.txt").read_text()
        self.assertIn("inputs/train.jsonl", manifest)
        self.assertIn(".devcontainer/Dockerfile", manifest)
        self.assertNotIn("feedback", manifest)

    def test_stage_records_the_feedback_of_a_rejected_run(self):
        result, calls = run({"command": "sort", "dockerfile": "FROM python:3.12"})

        self.assertEqual(2, len([c for c in calls if c["image"] == "agent"]))
        first = result.run / "01-result-attempt-1"
        self.assertFalse((first / "input" / "feedback").exists())
        self.assertIn("rejected", (result.run / "01-result" / "input" / "feedback" / "feedback.md").read_text())

    def test_agent_is_told_its_stage(self):
        steps = [{"name": "hello", "command": "echo hi"}]
        result, _ = run({"command": "sort", "dockerfile": "FROM python:3.12"}, agent_steps=steps)
        self.assertIn("`hello`: succeeded", (result.run / "summary.md").read_text())

        stage = lambda d: (result.run / d / "input" / "STAGE.md").read_text()
        smoke = stage("01-hello")
        self.assertIn("1. Smoke test `hello`  **<- you are here**", smoke)
        self.assertIn("smoke test of the agent setup", smoke)
        self.assertEqual(1, smoke.count("you are here"))
        self.assertIn(
            "2. Solve the task: write `solution/` and `submission-metadata.yml`  **<- you are here**",
            stage("02-result"),
        )
        self.assertIn("retry 1 of 5", stage("02-result"))
        self.assertIn("was rejected", stage("02-result"))
        self.assertIn("first time", stage("02-result-attempt-1"))
        self.assertIn("`feedback`", stage("02-result"))
        self.assertNotIn("`feedback`", stage("02-result-attempt-1"))
        self.assertNotIn("STAGE.md", (result.run / "02-result" / "input" / "manifest.txt").read_text())

    def test_review_stage_is_described(self):
        tira = mocked_tira_client({"command": "sort"})
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={"task_directory": str(TASK), "evaluator_image": "evaluator:latest"},
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )
        stage = (result.run / "01-result-review-1" / "input" / "STAGE.md").read_text()
        self.assertIn("review round 1 of 5", stage)
        self.assertRegex(stage, r"3\. Review the evaluation[^\n]*you are here")

    def test_summaries_explain_the_result_directory(self):
        result, _ = run({"command": "sort", "dockerfile": "FROM python:3.12"})

        summary = (result.run / SUMMARY).read_text()
        self.assertIn("**succeeded**", summary)
        self.assertIn("Final result of evaluation: accuracy=1.0", summary)
        self.assertIn("`01-result-attempt-1/`: agent run 1: rejected", summary)
        self.assertIn("`01-result/`: final agent run", summary)
        self.assertIn("Run 1 (solution): rejected", summary)
        self.assertIn("> Agent: The solution is written and validated. It sorts.", summary)
        self.assertIn("## Solution", summary)
        self.assertIn("Command: `sort`", summary)
        self.assertIn("- `Dockerfile`", summary)
        self.assertIn("Run 2 (fix 1): evaluated: accuracy=1.0", summary)
        self.assertIn("(1 solution run, 1 fix run)", summary)
        self.assertIn("network of the submission and the evaluator: none", summary)
        self.assertIn("agent image: agent", summary)
        self.assertIn("`NN-result-attempt-K/`", (result.run / "README.md").read_text())

    def test_summary_of_a_failed_task_names_the_problem(self):
        result, _ = run(None, agent_retries=0)

        summary = (result.run / SUMMARY).read_text()
        self.assertIn("**failed**", summary)
        self.assertIn("submission-metadata.yml", summary)
        self.assertIn("## To do", summary)

    def test_successful_run_evaluates_on_test_split(self):
        result, calls = run({"command": "sort"})

        self.assertEqual(_OK, result.level)
        self.assertIn("accuracy", result.message)
        self.assertEqual(["agent", "tira-submission-sorting-python", "evaluator:latest"], [c["image"] for c in calls])
        self.assertEqual(["test.jsonl"], calls[1]["input_files"])
        self.assertEqual(["test.jsonl"], calls[2]["input_files"])
        for call in calls[1:]:
            self.assertFalse(call["kwargs"]["allow_network"])
            self.assertEqual([], call["kwargs"]["network_allowlist"])
            self.assertIsNone(call["kwargs"]["forward_environment_variables"])
        self.assertEqual("sort\n", (result.run / "05-predictions" / "command.txt").read_text())
        self.assertEqual(
            "python3 /evaluate.py --predictions $inputRun --truths $inputDataset --output $outputDir\n",
            (result.run / "06-results" / "command.txt").read_text(),
        )

    def test_local_evaluator_directory_is_built_dynamically(self):
        result, calls = run({"command": "sort"}, evaluator_image="evaluator")
        self.assertEqual("built-evaluator", calls[2]["image"])

    def test_all_tasks_of_a_dataset_are_run(self):
        tira = mocked_tira_client({"command": "sort"})
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={
                "dataset_directory": str(TASK.parent),
                "allowed_hostnames": ["api.openai.com"],
                "evaluator_image": "evaluator:latest",
                "review_rounds": 0,
            },
            software={"image": "agent", "command": "run-agent"},
            tira=tira,
        )

        self.assertEqual(_OK, result.level)
        self.assertEqual(9, len(tira.local_execution.calls))
        for task in ["sorting-python", "sorting-java", "sorting-julia"]:
            self.assertIn(f"{task}:", result.message)
            self.assertIn(f"Results: {result.run / task}", result.message)
            self.assertTrue((result.run / task / "06-results" / "output" / "evaluation.prototext").is_file())
            self.assertTrue((result.run / task / "01-result" / "prompt.txt").is_file())
            self.assertIn("**succeeded**", (result.run / task / SUMMARY).read_text())
        self.assertIn("3 of 3 tasks succeeded.", (result.run / SUMMARY).read_text())

    def test_task_and_dataset_directory_are_exclusive(self):
        result, _ = run({"command": "sort"}, dataset_directory=str(TASK.parent))
        self.assertEqual(_ERROR, result.level)
        self.assertIn("exactly one", result.message)

    def test_missing_configuration_is_an_error(self):
        result = run_workflow(
            system_inputs=TASK,
            workflow="sandboxed-coding-agent",
            workflow_configuration={},
            software={"image": "agent", "command": "x"},
        )
        self.assertEqual(_ERROR, result.level)
