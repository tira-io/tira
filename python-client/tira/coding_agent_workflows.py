import json
import re
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from shutil import Error as CopyError
from shutil import copy, copytree, ignore_patterns, make_archive, rmtree, unpack_archive
from typing import Any, Dict, Optional, Tuple

import yaml

from tira.third_party_integrations import temporary_directory

from .check_format import _fmt, fmt_message
from .workflow_base import WorkflowBase, WorkflowResult

SUBMISSION_FILE = "submission-metadata.yml"
SOLUTION_DIRECTORY = "solution"
RESULT_STEP = "result"
FEEDBACK_DIRECTORY = "feedback"
FEEDBACK_FILE = "feedback.md"
PREDICTIONS_STEP = "05-predictions"
RESULTS_STEP = "06-results"
LOG_TAIL_CHARACTERS = 3000
DEVCONTAINER_DIRECTORY = ".devcontainer"
STEP_SUCCEEDED = ".step-succeeded"
RECORDED_INPUT_DIRECTORY = "input"
RECORDED_COMMAND_FILE = "command.txt"
RECORDED_PROMPT_FILE = "prompt.txt"
STAGE_FILE = "STAGE.md"
SUMMARY_FILE = "summary.md"
LAYOUT_FILE = "README.md"


def split_dataset_card(readme: Path) -> "Tuple[Dict[str, Any], str]":
    """Returns the parsed YAML front matter and the Markdown body of a dataset card."""
    text = readme.read_text()
    if not text.startswith("---"):
        return {}, text

    parts = text.split("\n---", 1)
    if len(parts) != 2:
        return {}, text

    front_matter = yaml.safe_load(parts[0][3:]) or {}
    return front_matter, parts[1].lstrip("-").lstrip("\n")


def write_readme_without_front_matter(readme: Path, target: Path) -> None:
    """The front matter reveals the location of the test split and the evaluation, so only the
    human-readable Markdown body is kept for the agent."""
    target.write_text(split_dataset_card(readme)[1])


def tasks_of_dataset(dataset_directory: Path) -> "Dict[str, Path]":
    """Maps the name of each task declared in the front matter of the dataset's README.md to its directory."""
    readme = dataset_directory / "README.md"
    if not readme.is_file():
        raise ValueError(f"The dataset directory '{dataset_directory}' has no README.md.")

    tasks = split_dataset_card(readme)[0].get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError(f"The README.md of '{dataset_directory}' does not declare any 'tasks'.")

    ret = {}
    for task in tasks:
        if not isinstance(task, dict) or "name" not in task or "path" not in task:
            raise ValueError("Each task in the dataset README.md needs a 'name' and a 'path'.")
        if not (dataset_directory / task["path"] / "README.md").is_file():
            raise ValueError(f"The task '{task['name']}' has no README.md at '{task['path']}'.")
        ret[task["name"]] = dataset_directory / task["path"]
    return ret


def split_files(card: "Dict[str, Any]", split: str) -> "Dict[str, Path]":
    """Maps each config of the dataset card (e.g., 'inputs', 'truths') to the file of the given split."""
    ret = {}
    for config in card.get("configs", []):
        for data_file in config.get("data_files", []):
            if data_file.get("split") == split:
                ret[config["config_name"]] = Path(data_file["path"])
    return ret


def dataset_splits(card: "Dict[str, Any]") -> "Tuple[list[str], list[str]]":
    """The names of the train and test splits of a dataset card. 'train' and 'test' are required, additional splits
    are named 'train-<name>' and 'test-<name>' (e.g., 'train-02', 'test-02'). The agent sees all train splits, the
    submission is run and evaluated on all test splits."""
    names = []
    for config in card.get("configs", []):
        for data_file in config.get("data_files", []):
            if data_file.get("split") and data_file["split"] not in names:
                names.append(data_file["split"])

    ret = []
    for kind in ["train", "test"]:
        if kind not in names:
            raise ValueError(f"The dataset card must define the split '{kind}'.")
        ret.append([kind] + [i for i in names if i.startswith(kind + "-") and len(i) > len(kind) + 1])

    unknown = [i for i in names if i not in ret[0] + ret[1]]
    if unknown:
        raise ValueError(f"Splits must be named 'train', 'test', 'train-<name>', or 'test-<name>', got {unknown}.")
    return ret[0], ret[1]


def split_descriptions(card: "Dict[str, Any]") -> "Dict[str, str]":
    """The optional descriptions of splits ('split_descriptions' in 'tira_configs' of the dataset card)."""
    ret = (card.get("tira_configs") or {}).get("split_descriptions") or {}
    if not isinstance(ret, dict):
        raise ValueError("'split_descriptions' of the dataset card must map split names to descriptions.")
    return {str(k): str(v).strip() for k, v in ret.items()}


def evaluation_name(prefix: str, split: str) -> str:
    """Name of a result of a test split: the default split 'test' has no suffix."""
    return prefix if split == "test" else f"{prefix}-{split}"


def combined_measures(evaluations: "Dict[str, str]") -> str:
    if len(evaluations) == 1:
        return measures_of(next(iter(evaluations.values())))
    return "; ".join(f"{split}: {measures_of(i)}" for split, i in evaluations.items())


def read_submission(output_dir: Path) -> str:
    """Returns the command of the docker submission produced by the agent. The agent writes its source code
    (with a Dockerfile) to 'solution/' and the command that executes it to 'submission-metadata.yml'. The workflow
    builds the image, as the agent runs inside docker and can not build images."""
    file = output_dir / SUBMISSION_FILE
    if not file.is_file():
        raise ValueError(f"The agent did not produce the file '{SUBMISSION_FILE}'.")

    try:
        metadata = yaml.safe_load(file.read_text())
    except Exception as e:
        raise ValueError(f"The file '{SUBMISSION_FILE}' is not valid YAML: {e}")

    command = metadata.get("command") if isinstance(metadata, dict) else None
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"The file '{SUBMISSION_FILE}' must contain a non-empty string for 'command'.")

    if not (output_dir / SOLUTION_DIRECTORY / "Dockerfile").is_file():
        raise ValueError(f"The agent did not produce '{SOLUTION_DIRECTORY}/Dockerfile'.")

    return command.strip()


def dockerfile_instructions(text: str) -> "list[str]":
    return [i.strip() for i in text.splitlines() if i.strip() and not i.strip().startswith("#")]


def check_extends_devcontainer(solution_directory: Path, task_directory: Path):
    """The Dockerfile of the solution must start with the devcontainer of the task, so that the submission runs in
    the environment the agent worked in."""
    config_file = task_directory / DEVCONTAINER_DIRECTORY / "devcontainer.json"
    config = json.loads(config_file.read_text())
    if "image" in config:
        expected = [f"FROM {config['image']}"]
    else:
        docker_file = (config_file.parent / config["build"]["dockerfile"]).resolve()
        expected = dockerfile_instructions(docker_file.read_text())

    actual = dockerfile_instructions((solution_directory / "Dockerfile").read_text())
    if actual[: len(expected)] != expected:
        raise ValueError(
            f"The '{SOLUTION_DIRECTORY}/Dockerfile' must start with the instructions of the devcontainer "
            f"(/tira-data/input/{DEVCONTAINER_DIRECTORY}), i.e.:\n" + "\n".join(expected)
        )


def measures_of(prototext: str) -> str:
    pairs = re.findall(r'key:\s*"([^"]*)"\s*value:\s*"([^"]*)"', prototext)
    return ", ".join(f"{k}={v}" for k, v in pairs) or prototext.strip()


def format_task_report(
    name: str, result: WorkflowResult, report: "Dict[str, Any]", results_path: "Optional[Path]" = None
) -> str:
    """A checklist of what worked for a task. The first stage that did not work is marked as failed (with the
    problem), the following stages were not reached."""
    parts = ["1 solution run"] if report.get("attempts") else []
    for count, what in [(report.get("retries"), "fix run"), (report.get("reviews"), "review")]:
        if count:
            parts.append(f"{count} {what}{'' if count == 1 else 's'}")
    stages = [
        ("Coding Agent works and was able to finish basic tasks", report.get("agent_works"), ""),
        (
            "Agent produced code and metadata",
            report.get("produced"),
            f" ({', '.join(parts)})" if parts else "",
        ),
        ("Final code builds into docker image", report.get("builds"), ""),
        ("Final result of evaluation", report.get("evaluations") is not None or None, ""),
    ]
    lines, failed = [fmt_message(f"{name}:", result.level)], False
    for title, status, suffix in stages:
        text = f"{title}{suffix}"
        if status:
            level = _fmt.OK
        elif result.level != _fmt.OK and not failed:
            level, failed = _fmt.ERROR, True
        else:
            level = None
            text += " (not reached)" if result.level != _fmt.OK else " (not run)"
        if title.startswith("Final result") and report.get("evaluations") is not None:
            text += f": {combined_measures(report['evaluations'])}"
        lines.append("  - " + (fmt_message(text, level) if level is not None else f"– {text}"))
        if level == _fmt.ERROR:
            problem = result.message if len(result.message) <= 800 else result.message[:800] + " …"
            lines.append("      " + problem.replace("\n", "\n      "))

    if result.level == _fmt.OK and not report.get("evaluations"):
        lines.append("  " + result.message)
    results_path = results_path or result.run
    if results_path:
        lines.append(f"  Results: {results_path}")
    return "\n".join(lines)


INPUT_FILE_DESCRIPTIONS = {
    STAGE_FILE: "this stage: where you are in the pipeline and what is required from you",
    "README.md": "the task description (input/output format, programming language, evaluation)",
    "inputs": "input files of the train splits (there is no test data, your software is evaluated on it later)",
    "truths": "expected outputs of the train splits",
    DEVCONTAINER_DIRECTORY: "the devcontainer of your environment, the Dockerfile of your solution extends it",
    FEEDBACK_DIRECTORY: "feedback of the workflow on your previous run (start with feedback.md)",
}

STAGE_REQUIREMENTS = {
    "step": [
        "This is a smoke test of the agent setup: only the exit code of the command is checked.",
        "Do what the prompt asks, nothing else. Nothing needs to be written to `/tira-data/output`.",
    ],
    "solve": [
        "Solve the task of `/tira-data/input/README.md` by writing software, not by producing results by hand.",
        f"Write the source code of your solution to `/tira-data/output/{SOLUTION_DIRECTORY}/` together with a "
        "`Dockerfile` that starts with exactly the instructions of `/tira-data/input/.devcontainer/Dockerfile`.",
        f"Write `/tira-data/output/{SUBMISSION_FILE}` with a `command` that runs your solution. It may only rely on "
        "`$inputDataset` (input directory) and `$outputDir` (output directory), never on hard-coded paths.",
        "Validate your solution on the train split(s), then finish. Nobody answers questions, decide on your own.",
    ],
    "fix": [
        f"Your previous solution in `/tira-data/output/{SOLUTION_DIRECTORY}/` was rejected, the reason is in "
        f"`/tira-data/input/{FEEDBACK_DIRECTORY}/{FEEDBACK_FILE}`.",
        "Fix exactly this problem in the existing solution (do not start from scratch), finish as soon as it is fixed.",
        f"The requirements for `{SOLUTION_DIRECTORY}/` and `{SUBMISSION_FILE}` are unchanged.",
    ],
    "review": [
        "Your solution was built, run on unseen test data, and evaluated. Review the results in "
        f"`/tira-data/input/{FEEDBACK_DIRECTORY}/` (`stdout.txt`, `stderr.txt`, `evaluation.prototext` of the split "
        "`test`; the files of additional test splits have the split name as suffix, e.g., `evaluation-test-02.prototext`).",
        "If the results look reasonable, finish immediately without changing anything: this ends the review.",
        f"If not (e.g., errors in the logs or a very low score), modify the existing `{SOLUTION_DIRECTORY}/` and "
        "finish as soon as it is fixed. The modified solution is evaluated again and uses up a review round.",
    ],
}


def stage_description(
    task: str,
    step_names: "list[str]",
    kind: str,
    current: str,
    notes: "list[str]",
    present,
    train_splits: "Optional[Dict[str, str]]" = None,
) -> str:
    """The description of the current stage that is mounted to the agent as STAGE.md, so that the agent knows
    what to expect: the pipeline with its own position, what this stage is, what is required, and which files
    it gets. `kind` is 'step', 'solve', 'fix', or 'review'."""
    pipeline = [(f"Smoke test `{n}`", kind == "step" and n == current) for n in step_names]
    pipeline += [
        ("Solve the task: write `solution/` and `submission-metadata.yml`", kind in ("solve", "fix")),
        ("The workflow builds the solution, runs it on unseen test data (no network), and evaluates it", False),
        ("Review the evaluation, improve the solution if needed (repeated until nothing changes)", kind == "review"),
    ]
    lines = [f"# Stage of the task `{task}`", "", "## Pipeline", ""]
    for i, (title, is_current) in enumerate(pipeline, 1):
        lines.append(f"{i}. {title}" + ("  **<- you are here**" if is_current else ""))
    lines += ["", f"## This stage: {current}", ""] + [f"- {i}" for i in notes]
    lines += ["", "## Required from you", ""] + [f"- {i}" for i in STAGE_REQUIREMENTS[kind]]
    lines += ["", "## Files", "", "In `/tira-data/input/` (read-only):"]
    lines += [f"- `{n}`: {d}" for n, d in INPUT_FILE_DESCRIPTIONS.items() if n in present]
    if train_splits and len(train_splits) > 1:
        lines += ["", "Train splits:"]
        lines += [f"- `{n}`: {d or 'no description'}" for n, d in train_splits.items()]
    lines += ["", "Everything you write belongs to `/tira-data/output/` (also `$outputDir`).", ""]
    lines += ["Network access is restricted to the LLM you use. This holds only for you (the agent): the software you"]
    lines += ["write runs later without any network and without your LLM credentials, so it must not use an LLM."]
    return "\n".join(lines) + "\n"


def plain(text: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", text)


def describe_directory(directory: Path) -> str:
    m = re.fullmatch(r"\d\d-(.+?)(?:-(attempt|review)-(\d+))?", directory.name)
    if not m:
        return ""

    base, suffix, k = m.groups()
    split = ""
    for kind in ("predictions", "results"):
        if base.startswith(kind + "-"):
            base, split = kind, f" (split '{base[len(kind) + 1:]}')"
    if base in ("predictions", "results"):
        what = "predictions of the submission on the test inputs" if base == "predictions" else "evaluation"
        what += split
        return what + (f" of agent run {k}, replaced by a later run" if suffix else "")
    if base != RESULT_STEP:
        return "smoke test of the agent setup"
    if suffix == "review":
        return f"agent run {int(k) + 1}, a review of the evaluation of run {k}: the agent did not change its solution"
    if suffix == "attempt":
        evaluation = directory.parent / f"{RESULTS_STEP}-attempt-{k}" / "output" / "evaluation.prototext"
        if evaluation.is_file():
            return f"agent run {k}: evaluated successfully, then reviewed by the next run"
        return f"agent run {k}: rejected (the reason is in input/feedback/feedback.md of the next run)"
    return "final agent run (its solution was built, run, and evaluated)"


def agent_final_message(stdout_file: Path, limit: int = 1200) -> str:
    """The last paragraph the agent wrote to stdout, before the usage statistics of the Copilot CLI (a line starting
    with 'Changes'). Returns an empty string if there is none."""
    if not stdout_file.is_file():
        return ""

    text = re.split(r"^\s*Changes\s+[+-]\d", stdout_file.read_text(errors="replace"), flags=re.M)[0].strip()
    paragraphs = [i.strip() for i in re.split(r"\n\s*\n", text) if i.strip()]
    message = " ".join(paragraphs[-1].split()) if paragraphs else ""
    return message if len(message) <= limit else message[:limit] + " …"


def quoted(message: str) -> str:
    return f"\n  > Agent: {message}" if message else ""


def describe_solution(directory: Path) -> "list[str]":
    """The command and the files of the final solution of the task directory."""
    from zipfile import ZipFile

    for result in sorted(directory.glob(f"*-{RESULT_STEP}")):
        archive, metadata = result / "source-code.zip", result / SUBMISSION_FILE
        if not archive.is_file() or not metadata.is_file():
            continue
        with ZipFile(archive) as zipped:
            files = sorted(i.filename for i in zipped.infolist() if not i.is_dir())
        command = yaml.safe_load(metadata.read_text()).get("command", "")
        listed = files[:30] + ([f"… ({len(files) - 30} more)"] if len(files) > 30 else [])
        return [f"Command: `{command}`", f"Files in `{result.name}/source-code.zip`:"] + [f"- `{i}`" for i in listed]
    return []


def write_task_summary(
    directory: Path,
    name: str,
    result: WorkflowResult,
    report: "Dict[str, Any]",
    configuration: "Optional[list[str]]" = None,
):
    """Writes summary.md: what worked, what did not, and where to look, so that the result directory can be
    understood without the console output."""
    stages = [
        plain(i).strip()
        for i in format_task_report(name, result, report).splitlines()
        if not i.startswith("  Results:")
    ]
    lines = [f"# {name}", "", "Status: " + ("**succeeded**" if result.level == _fmt.OK else "**failed**"), ""]
    lines += ["## Stages", ""] + [f"    {i}" for i in stages[1:]]
    if report.get("split_descriptions") and len(report["split_descriptions"]) > 2:
        lines += ["", "## Splits", ""]
        lines += [f"- `{n}`: {d or 'no description'}" for n, d in report["split_descriptions"].items()]
    if report.get("smoke_tests"):
        lines += ["", "## Smoke tests", ""] + [f"- {i}" for i in report["smoke_tests"]]
    if report.get("timeline"):
        lines += ["", "## Agent runs", ""] + [f"- {i}" for i in report["timeline"]]
    solution = describe_solution(directory)
    if solution and result.level == _fmt.OK:
        lines += ["", "## Solution", ""] + solution
    if configuration:
        lines += ["", "## Configuration", ""] + [f"- {i}" for i in configuration]
    if result.level != _fmt.OK:
        lines += ["", "## To do", "", "Fix the first failed stage above (the problem is quoted there), then run again."]
    lines += ["", "## Directories", ""]
    lines += [f"- `{i.name}/`: {describe_directory(i)}" for i in sorted(directory.iterdir()) if i.is_dir()]
    (directory / SUMMARY_FILE).write_text("\n".join(lines) + "\n")


def describe_configuration(configuration: "Dict[str, Any]", software: "Dict[str, Any]", forwarded) -> "list[str]":
    """The settings that produced a result. Only the names of forwarded environment variables are listed."""
    keys = ["agent_retries", "review_rounds", "stop_after_step", "evaluator_image", "evaluator_command"]
    lines = [f"agent image: {software.get('image') or 'the devcontainer of the task'}"]
    lines += [f"agent command: `{software['command']}`"]
    lines += [f"smoke tests: {', '.join(i['name'] for i in configuration.get('agent_steps', [])) or 'none'}"]
    lines += [
        f"network of the agent: {', '.join(configuration.get('allowed_hostnames', [])) or 'none'} (plus LLM hosts)"
    ]
    lines += ["network of the submission and the evaluator: none"]
    lines += [f"forwarded environment variables: {', '.join(forwarded or []) or 'none'}"]
    return lines + [f"{k}: {configuration[k]}" for k in keys if k in configuration]


def write_dataset_summary(directory: Path, task_summaries: "Dict[str, bool]"):
    lines = ["# Summary", ""]
    lines += [
        f"- `{n}/`: {'succeeded' if ok else 'failed'} (see `{n}/{SUMMARY_FILE}`)" for n, ok in task_summaries.items()
    ]
    lines += ["", f"{sum(task_summaries.values())} of {len(task_summaries)} tasks succeeded."]
    (directory / SUMMARY_FILE).write_text("\n".join(lines) + "\n")


LAYOUT = """# Results of the sandboxed coding agent

Each task has `summary.md` (what worked, what failed, what to do) and numbered stage directories in the order they
ran (for a dataset of tasks, in one directory per task):

- `NN-<step>/`: smoke tests of the agent setup (`agent_steps`).
- `NN-result/`: the final agent run: `source-code.zip` and `submission-metadata.yml` (its solution),
  `stdout.txt`/`stderr.txt` (agent log), `network-access.log`.
- `NN-result-attempt-K/`: agent run K that was replaced by a later run (rejected, or evaluated and then reviewed).
- `NN-result-review-K/`: a review in which the agent did not change its solution.
- `05-predictions/`, `06-results/`: the solution on the test inputs and its evaluation
  (`output/evaluation.prototext`). Replaced runs are kept as `...-attempt-K`. Additional test splits
  (`test-<name>`) have their own `05-predictions-test-<name>/` and `06-results-test-<name>/`.

Every agent run records what it was given and did: `input/STAGE.md` (the stage description of the agent),
`input/README.md` (task), `input/feedback/` (feedback), `input/manifest.txt` (other mounted files), `command.txt`,
and `prompt.txt` (if the agent writes it).
"""


def directory_digest(directory: Path) -> str:
    digest = sha256()
    ignored = {"__pycache__", ".git", ".pytest_cache"}
    for f in sorted(i for i in directory.rglob("*") if i.is_file() and not ignored & set(i.parts)):
        digest.update(str(f.relative_to(directory)).encode())
        digest.update(f.read_bytes())
    return digest.hexdigest()


def stage_names(test_splits: "list[str]") -> "list[str]":
    return [evaluation_name(i, split) for split in test_splits for i in (PREDICTIONS_STEP, RESULTS_STEP)]


def copy_results(source: Path, target: Path):
    """Files created by containers (e.g., as root) may be unreadable; copy what is possible instead of failing."""
    try:
        copytree(source, target, dirs_exist_ok=True)
    except CopyError as e:
        target.mkdir(parents=True, exist_ok=True)
        (target / "copy-errors.txt").write_text(f"Some files could not be copied from {source}:\n{e}")


def record_agent_input(agent_inputs: Path, feedback_directory: Path, step_directory: Path):
    """Records what the agent saw in this run, so that the input can be inspected later: the task description
    (without front matter), the feedback of this run, a manifest of the remaining mounted files (the train split
    and the devcontainer are not duplicated), and the command that was executed."""
    recorded = step_directory / RECORDED_INPUT_DIRECTORY
    rmtree(recorded, ignore_errors=True)
    recorded.mkdir(parents=True)

    copy(agent_inputs / "README.md", recorded / "README.md")
    copy(agent_inputs / STAGE_FILE, recorded / STAGE_FILE)
    if feedback_directory.is_dir():
        copytree(feedback_directory, recorded / FEEDBACK_DIRECTORY)

    manifest = []
    for f in sorted(i for i in agent_inputs.rglob("*") if i.is_file()):
        relative = f.relative_to(agent_inputs)
        if relative in (Path("README.md"), Path(STAGE_FILE)) or relative.parts[0] == FEEDBACK_DIRECTORY:
            continue
        manifest.append(f"{relative}\t{f.stat().st_size} bytes")
    (recorded / "manifest.txt").write_text("\n".join(manifest) + ("\n" if manifest else ""))


def record_agent_prompt(results: Path, step_directory: Path):
    """Agents may write the prompt they received to 'prompt.txt' in their output directory; it is copied to the
    stage directory so that the exact prompt of every run can be inspected."""
    prompt = results / "output" / RECORDED_PROMPT_FILE
    if prompt.is_file():
        try:
            copy(prompt, step_directory / RECORDED_PROMPT_FILE)
        except (OSError, CopyError):
            pass


def devcontainer_image(task_directory: Path, tira) -> str:
    """Returns the docker image of the devcontainer of the task, i.e., the image the agent is started in.
    Devcontainers that are defined via a Dockerfile are built."""
    config_file = task_directory / ".devcontainer" / "devcontainer.json"
    if not config_file.is_file():
        raise ValueError(f"The task '{task_directory}' has no {config_file.relative_to(task_directory)}.")

    config = json.loads(config_file.read_text())
    if "image" in config:
        return config["image"]

    build = config.get("build") or {}
    if "dockerfile" not in build:
        raise ValueError(f"The devcontainer of '{task_directory}' defines neither an 'image' nor a 'build.dockerfile'.")

    docker_file = (config_file.parent / build["dockerfile"]).resolve()
    context = (config_file.parent / build.get("context", ".")).resolve()
    tag = f"tira-devcontainer-{task_directory.resolve().name.lower()}"
    tira.local_execution.build_docker_image(context, tag, docker_file)
    return tag


class SandboxedCodingAgent(WorkflowBase):
    """Phase 1: a coding agent is started in the devcontainer of the task (or in 'software.image'). It only
    sees the train split and the task description and may only access the configured LLM hostnames. The
    optional 'agent_steps' ({"name", "command"}, e.g., small smoke tests) run first in the same container; a
    step succeeds if its command exits with 0, and the workflow stops directly at the first failing step. The
    final agent ('software.command', directory 'result') writes its source code with a Dockerfile to 'solution/'
    and a 'submission-metadata.yml' with the 'command' to run it to its output directory. Phase 2: the produced
    docker submission is executed on the test split (no network) and scored by the evaluator of the dataset card.

    Optional workflow configuration: 'agent_directory' (mounted read-only at /tira-agent, e.g., with the scripts
    of the steps), 'stop_after_step' (name of the last step to run, for debugging), 'agent_retries' (default 5: how
    often the agent is started again with its rejected solution mounted and a 'feedback.md' if the result is
    invalid), and 'review_rounds' (default 5: how often the agent reviews a successful evaluation)."""

    def apply_configuration_and_throw_if_invalid(
        self, workflow_configuration: "Optional[Dict[str, Any]]", software: "Optional[Dict[str, Any]]"
    ):
        if not workflow_configuration:
            raise ValueError("The workflow 'sandboxed-coding-agent' requires a configuration.")

        # Hostnames of forwarded LLM configurations (e.g., OPENAI_BASE_URL) are allowed additionally.
        hostnames = workflow_configuration.get("allowed_hostnames", [])
        if not isinstance(hostnames, list) or not all(isinstance(h, str) for h in hostnames):
            raise ValueError("'allowed_hostnames' must be a list of hostnames.")

        if ("task_directory" in workflow_configuration) == ("dataset_directory" in workflow_configuration):
            raise ValueError(
                "The workflow 'sandboxed-coding-agent' requires exactly one of 'task_directory' or 'dataset_directory'."
            )

        if "dataset_directory" in workflow_configuration:
            task_directories = list(tasks_of_dataset(Path(workflow_configuration["dataset_directory"])).values())
        else:
            task_directories = [Path(workflow_configuration["task_directory"])]

        for task_directory in task_directories:
            if not (task_directory / "README.md").is_file():
                raise ValueError(f"The task directory '{task_directory}' has no README.md dataset card.")

        if not software or "command" not in software:
            raise ValueError("Software executed for 'sandboxed-coding-agent' needs a configuration for 'command'.")

        steps = workflow_configuration.get("agent_steps", [])
        if not isinstance(steps, list) or not all(isinstance(i, dict) and {"name", "command"} <= set(i) for i in steps):
            raise ValueError("'agent_steps' must be a list of objects with a 'name' and a 'command'.")

        stop_after = workflow_configuration.get("stop_after_step")
        if stop_after and stop_after not in [i["name"] for i in steps] + [RESULT_STEP]:
            raise ValueError(f"'stop_after_step' must be the name of a step or '{RESULT_STEP}', not '{stop_after}'.")

        for task_directory in task_directories:
            card = split_dataset_card(task_directory / "README.md")[0]
            evaluator = (card.get("tira_configs") or {}).get("evaluator") or {}
            if not (workflow_configuration.get("evaluator_image") or evaluator.get("image")):
                raise ValueError(f"No evaluator image is configured for '{task_directory}'.")
            if not (workflow_configuration.get("evaluator_command") or evaluator.get("command")):
                raise ValueError(f"No evaluator command is configured for '{task_directory}'.")

        super().apply_configuration_and_throw_if_invalid(workflow_configuration, software)

    def run_workflow(
        self,
        system_inputs: Path,
        allow_network: bool,
        additional_volumes,
        cpu_count,
        mem_limit,
        gpu_count,
        gpu_device_ids,
        tira,
        forward_environment_variables: "Optional[list[str]]" = None,
        mount_directory: "Optional[dict]" = None,
        cache_directory: "Optional[dict]" = None,
        platform: str = "linux/amd64",
    ):
        kwargs = dict(
            additional_volumes=additional_volumes,
            cpu_count=cpu_count,
            mem_limit=mem_limit,
            gpu_count=gpu_count,
            gpu_device_ids=gpu_device_ids,
            tira=tira,
            forward_environment_variables=forward_environment_variables,
            mount_directory=mount_directory,
            platform=platform,
        )
        if "task_directory" in self.workflow_configuration:
            task_directory = Path(self.workflow_configuration["task_directory"])
            report: "Dict[str, Any]" = {}
            started = datetime.now()
            result = self.run_task(task_directory, report=report, **kwargs)
            if result.run:
                write_task_summary(
                    result.run,
                    task_directory.name,
                    result,
                    report,
                    self.describe(forward_environment_variables, started),
                )
                (result.run / LAYOUT_FILE).write_text(LAYOUT)
            return WorkflowResult(result.level, format_task_report(task_directory.name, result, report), result.run)

        ret = temporary_directory()
        level, messages, succeeded, task_results = _fmt.OK, [], 0, {}
        tasks = tasks_of_dataset(Path(self.workflow_configuration["dataset_directory"]))
        for name, task_directory in tasks.items():
            report = {}
            started = datetime.now()
            result = self.run_task(task_directory, report=report, **kwargs)
            if result.run:
                write_task_summary(
                    result.run, name, result, report, self.describe(forward_environment_variables, started)
                )
                copy_results(result.run, ret / name)
                task_results[name] = result.level == _fmt.OK
            messages.append(format_task_report(name, result, report, ret / name if result.run else None))
            if result.level == _fmt.OK and self.workflow_configuration.get("stop_after_step"):
                messages.append("Stopped after the first task for inspection (stop_after_step is set).")
                break
            if result.level != _fmt.OK:
                level = _fmt.ERROR
            else:
                succeeded += 1

        # A failing task does not stop the remaining tasks
        summary = fmt_message(f"{succeeded} of {len(tasks)} tasks succeeded.", level)
        write_dataset_summary(ret, task_results)
        (ret / LAYOUT_FILE).write_text(LAYOUT)
        return WorkflowResult(level, "\n\n".join(messages + [summary]), ret)

    def describe(self, forwarded, started: datetime) -> "list[str]":
        finished = datetime.now()
        timing = [f"started {started:%Y-%m-%d %H:%M:%S}, finished {finished:%H:%M:%S} ({finished - started})"]
        return timing + describe_configuration(self.workflow_configuration, self.software_configuration, forwarded)

    def run_task(
        self,
        task_directory: Path,
        additional_volumes,
        cpu_count,
        mem_limit,
        gpu_count,
        gpu_device_ids,
        tira,
        forward_environment_variables,
        mount_directory,
        platform,
        report: "Dict[str, Any]",
    ):
        config = self.workflow_configuration
        card = split_dataset_card(task_directory / "README.md")[0]
        train_splits, test_splits = dataset_splits(card)
        descriptions = split_descriptions(card)
        train_files = {i: split_files(card, i) for i in train_splits}
        test_files = {i: split_files(card, i) for i in test_splits}
        for split in train_splits:
            if "inputs" not in train_files[split]:
                raise ValueError(f"The dataset card must define 'inputs' for the split '{split}'.")
        for split in test_splits:
            if "inputs" not in test_files[split] or "truths" not in test_files[split]:
                raise ValueError(f"The dataset card must define 'inputs' and 'truths' for the split '{split}'.")

        # Phase 1: the agent only sees the train split and the task description
        agent_inputs = temporary_directory()
        write_readme_without_front_matter(task_directory / "README.md", agent_inputs / "README.md")
        for relative_path in {p for files in train_files.values() for p in files.values()}:
            (agent_inputs / relative_path).parent.mkdir(parents=True, exist_ok=True)
            copy(task_directory / relative_path, agent_inputs / relative_path)

        # The agent sees the devcontainer it runs in, as its Dockerfile has to extend it
        copytree(task_directory / DEVCONTAINER_DIRECTORY, agent_inputs / DEVCONTAINER_DIRECTORY)

        agent_image = self.software_configuration.get("image") or devcontainer_image(task_directory, tira)
        agent_volumes = list(additional_volumes or [])
        if config.get("agent_directory"):
            agent_volumes.append(f"{Path(config['agent_directory']).resolve()}:/tira-agent:ro")

        def announce(message: str):
            print(f"[{task_directory.name}] {message}", flush=True)

        step_names = [i["name"] for i in config.get("agent_steps", [])]

        def run_in_agent_container(
            command,
            step_directory: Path,
            kind: str,
            current: str,
            notes: "list[str]",
            previous_output=None,
            feedback=None,
            feedback_files=None,
        ):
            # The feedback is mounted into the input of the agent (/tira-data/input/feedback)
            feedback_directory = agent_inputs / FEEDBACK_DIRECTORY
            rmtree(feedback_directory, ignore_errors=True)
            if feedback:
                feedback_directory.mkdir()
                (feedback_directory / FEEDBACK_FILE).write_text(feedback)
                for name, path in (feedback_files or {}).items():
                    if Path(path).is_file():
                        copy(path, feedback_directory / name)

            present = {i.name for i in agent_inputs.iterdir()} | {STAGE_FILE}
            (agent_inputs / STAGE_FILE).write_text(
                stage_description(
                    task_directory.name,
                    step_names,
                    kind,
                    current,
                    notes,
                    present,
                    {i: descriptions.get(i, "") for i in train_splits},
                )
            )
            record_agent_input(agent_inputs, feedback_directory, step_directory)
            (step_directory / RECORDED_COMMAND_FILE).write_text(command + "\n")

            def execute(output_dir):
                # A retry continues with the previous output (the solution)
                if previous_output:
                    try:
                        copytree(
                            previous_output,
                            output_dir,
                            dirs_exist_ok=True,
                            ignore=ignore_patterns(
                                "copilot-logs", ".tracking-results.yml", FEEDBACK_FILE, RECORDED_PROMPT_FILE
                            ),
                        )
                    except CopyError:
                        pass
                return tira.local_execution.run(
                    image=agent_image,
                    command=command,
                    input_dir=agent_inputs,
                    output_dir=output_dir,
                    allow_network=False,
                    additional_volumes=agent_volumes,
                    cpu_count=cpu_count,
                    gpu_count=gpu_count,
                    mem_limit=mem_limit,
                    gpu_device_ids=gpu_device_ids,
                    forward_environment_variables=forward_environment_variables,
                    mount_directory=mount_directory,
                    platform=platform,
                    network_allowlist=config.get("allowed_hostnames", []),
                )

            results = self.execute_monitored(execute, True)
            record_agent_prompt(results, step_directory)
            return results

        ret = temporary_directory()
        steps = list(config.get("agent_steps", [])) + [
            {"name": RESULT_STEP, "command": self.software_configuration["command"]}
        ]
        for i, step in enumerate(steps[:-1]):
            announce(f"Step {i + 1} of {len(steps) - 1}: {step['name']}")
            step_directory = ret / f"{i + 1:02d}-{step['name']}"
            step_directory.mkdir(parents=True, exist_ok=True)
            results = run_in_agent_container(
                f"{step['command']} && touch /tira-data/output/{STEP_SUCCEEDED}",
                step_directory,
                "step",
                step["name"],
                [f"Step {i + 1} of {len(steps) - 1} before the final agent run: `{step['name']}`."],
            )
            copy_results(results, step_directory)

            if (results / "exception.txt").exists():
                msg = f"The step '{step['name']}' failed: {(results / 'exception.txt').read_text()}"
                return WorkflowResult(_fmt.ERROR, f"{msg}\nSee {step_directory}", ret)

            if not (results / "output" / STEP_SUCCEEDED).exists():
                msg = f"The step '{step['name']}' ({step['command']}) did not exit with 0 in the image {agent_image}."
                return WorkflowResult(_fmt.ERROR, f"{msg}\nSee {step_directory}", ret)

            said = agent_final_message(step_directory / "stdout.txt")
            report.setdefault("smoke_tests", []).append(f"`{step['name']}`: succeeded{quoted(said)}")

            if config.get("stop_after_step") == step["name"]:
                return WorkflowResult(_fmt.OK, f"Stopped after the step '{step['name']}': {step_directory}", ret)

        evaluator = (card.get("tira_configs") or {}).get("evaluator") or {}
        evaluator_image = config.get("evaluator_image") or evaluator.get("image")
        evaluator_command = config.get("evaluator_command") or evaluator.get("command")
        if config.get("stop_after_step") != RESULT_STEP:
            # Local directories and git links are built into a docker image, other values are image references.
            evaluator_image = tira._resolve_evaluator_image(
                task_directory, evaluator, evaluator_image, lambda message, level: print(message), dry_run=True
            )

        test_inputs, test_truths = {}, {}
        for split in test_splits:
            test_inputs[split], test_truths[split] = temporary_directory(), temporary_directory()
            copy(task_directory / test_files[split]["inputs"], test_inputs[split] / test_files[split]["inputs"].name)
            copy(task_directory / test_files[split]["truths"], test_truths[split] / test_files[split]["truths"].name)
        report["split_descriptions"] = {i: descriptions.get(i, "") for i in train_splits + test_splits}

        feedback_files: "Dict[str, Path]" = {}

        def evaluate_result(step_directory: Path) -> "Tuple[Optional[str], Optional[str]]":
            """Phase 2 uses only the packaged result: unpack source-code.zip, build it, run the command of the
            metadata file on the test inputs of each test split (05-predictions), and evaluate the predictions (06-results).
            Returns (problem, None) if something fails or (None, evaluation) if the evaluation succeeded."""
            packaged_solution = temporary_directory()
            unpack_archive(step_directory / "source-code.zip", packaged_solution)
            command = yaml.safe_load((step_directory / SUBMISSION_FILE).read_text())["command"].strip()
            image = f"tira-submission-{task_directory.resolve().name.lower()}"
            announce("Building the docker image of the solution")
            try:
                tira.local_execution.build_docker_image(packaged_solution, image, packaged_solution / "Dockerfile")
            except Exception as e:
                report["builds"] = False
                return f"Building the docker image of your solution failed: {e}", None
            report["builds"] = True
            evaluations: "Dict[str, str]" = {}
            for split in test_splits:
                where = f" (split '{split}')" if len(test_splits) > 1 else ""
                predictions_step = evaluation_name(PREDICTIONS_STEP, split)
                results_step = evaluation_name(RESULTS_STEP, split)
                announce(f"Running the submission on the unseen test inputs{where}")

                submission_results = self.execute_monitored(
                    lambda o: tira.local_execution.run(
                        image=image,
                        command=command,
                        input_dir=test_inputs[split],
                        output_dir=o,
                        allow_network=False,
                        network_allowlist=[],
                        forward_environment_variables=None,
                        additional_volumes=None,
                        cpu_count=cpu_count,
                        gpu_count=gpu_count,
                        mem_limit=mem_limit,
                        gpu_device_ids=gpu_device_ids,
                        platform=platform,
                    ),
                    True,
                )
                copy_results(submission_results, ret / predictions_step)
                (ret / predictions_step / RECORDED_COMMAND_FILE).write_text(command + "\n")
                for base in ["stdout", "stderr", "exception"]:
                    feedback_files[evaluation_name(base, split) + ".txt"] = ret / predictions_step / f"{base}.txt"

                problem = f'Running your submission with the command "{command}" on unseen test data{where} failed.'
                if (submission_results / "exception.txt").exists():
                    return f"{problem} {(submission_results / 'exception.txt').read_text()}", None
                if not any(i.is_file() for i in (submission_results / "output").rglob("*")):
                    return f"{problem} It wrote no files to $outputDir.", None

                announce(f"Evaluating the predictions{where}")
                evaluation_results = self.execute_monitored(
                    lambda o: tira.local_execution.run(
                        image=evaluator_image,
                        command=evaluator_command,
                        input_dir=test_truths[split],
                        input_run=submission_results / "output",
                        output_dir=o,
                        allow_network=False,
                        network_allowlist=[],
                        forward_environment_variables=None,
                        additional_volumes=None,
                        cpu_count=cpu_count,
                        mem_limit=mem_limit,
                        platform=platform,
                    ),
                    True,
                )
                copy_results(evaluation_results, ret / results_step)
                (ret / results_step / RECORDED_COMMAND_FILE).write_text(evaluator_command + "\n")

                problem = f'The evaluator could not evaluate the predictions{where} of your submission ("{command}").'
                if (evaluation_results / "exception.txt").exists():
                    return f"{problem} {(evaluation_results / 'exception.txt').read_text()}", None

                evaluation_file = ret / results_step / "output" / "evaluation.prototext"
                if not evaluation_file.is_file():
                    return f"{problem} The output format is probably wrong.", None

                feedback_files[evaluation_name("evaluation", split) + ".prototext"] = evaluation_file
                evaluations[split] = evaluation_file.read_text()

            report["evaluations"] = evaluations
            if len(evaluations) == 1:
                return None, next(iter(evaluations.values()))
            return None, "\n".join(f"Split {split}:\n{text}" for split, text in evaluations.items())

        report["agent_works"] = True

        # The agent is started again (with the rejected solution and feedback) if its result is invalid or if its
        # submission can not be run and evaluated. After a successful evaluation, it reviews the results
        # (stdout, stderr, evaluation) and can modify its solution if they do not look reasonable.
        step_directory = ret / f"{len(steps):02d}-{RESULT_STEP}"
        max_retries = error_retries = int(config.get("agent_retries", 5))
        max_reviews = reviews = int(config.get("review_rounds", 5))
        results, feedback, reviewed_digest, reviewed_evaluation = None, None, None, None
        reviewed_evaluations = None
        run = 0
        while True:
            run += 1
            report.update(attempts=run, produced=None, builds=None, evaluations=None)
            timeline = report.setdefault("timeline", [])
            if feedback is None:
                kind, title = "solve", "writing the solution"
                notes = [f"Agent run {run}: you write the solution for the first time."]
                notes.append(f"If it is rejected, you get up to {max_retries} retries with feedback.")
            elif reviewed_digest is None:
                kind, title = "fix", "fixing the solution after an error"
                notes = [f"Agent run {run}: retry {max_retries - error_retries} of {max_retries} after a rejection."]
                notes.append(f"Retries left after this one: {error_retries}.")
            else:
                kind, title = "review", "reviewing the evaluation"
                notes = [f"Agent run {run}: review round {max_reviews - reviews} of {max_reviews}."]
                notes.append(f"Review rounds left after this one: {reviews}.")
            report.update(retries=max_retries - error_retries, reviews=max_reviews - reviews)
            label = {"solve": "solution", "fix": f"fix {report['retries']}", "review": f"review {report['reviews']}"}[
                kind
            ]
            announce(f"Agent run {run}: {title}")
            step_directory.mkdir(parents=True, exist_ok=True)
            results = run_in_agent_container(
                steps[-1]["command"],
                step_directory,
                kind,
                title.capitalize(),
                notes,
                results / "output" if results and feedback else None,
                feedback,
                feedback_files,
            )
            for f in ["stdout.txt", "stderr.txt", "network-access.log"]:
                if (results / f).exists():
                    copy(results / f, step_directory / f)
            said = quoted(agent_final_message(results / "stdout.txt"))

            if (results / "exception.txt").exists():
                msg = f"The agent failed: {(results / 'exception.txt').read_text()}"
                timeline.append(f"Run {run} ({label}): the agent failed{said}")
                return WorkflowResult(_fmt.ERROR, f"{msg}\nSee {step_directory}", ret)

            problem, evaluation = None, None
            report["produced"] = False
            try:
                read_submission(results / "output")
                check_extends_devcontainer(results / "output" / SOLUTION_DIRECTORY, task_directory)
            except ValueError as e:
                problem = str(e)

            if not problem:
                report["produced"] = True
                digest = directory_digest(results / "output" / SOLUTION_DIRECTORY)
                if reviewed_digest == digest:
                    # The review did not change anything: the evaluation of the previous run is final
                    announce(f"Run {run}: the agent did not change its solution, the review is finished")
                    report.update(builds=True, evaluations=reviewed_evaluations)
                    timeline.append(
                        f"Run {run} ({label}): the agent did not change its solution, review finished{said}"
                    )
                    review_directory = ret / f"{step_directory.name}-review-{run - 1}"
                    step_directory.rename(review_directory)
                    for name in [step_directory.name, *stage_names(test_splits)]:
                        if (ret / f"{name}-attempt-{run - 1}").exists():
                            (ret / f"{name}-attempt-{run - 1}").rename(ret / name)
                    return WorkflowResult(_fmt.OK, f"The agent submission was evaluated:\n{reviewed_evaluation}", ret)

                make_archive(str(step_directory / "source-code"), "zip", results / "output" / SOLUTION_DIRECTORY)
                copy(results / "output" / SUBMISSION_FILE, step_directory / SUBMISSION_FILE)
                if config.get("stop_after_step") == RESULT_STEP:
                    return WorkflowResult(_fmt.OK, f"Stopped after the result of the agent: {step_directory}", ret)
                if reviewed_digest is not None:
                    announce(f"Run {run}: the agent modified its solution, it is evaluated again")
                feedback_files.clear()
                problem, evaluation = evaluate_result(step_directory)

            if problem:
                timeline.append(f"Run {run} ({label}): rejected: {problem.splitlines()[0][:200]}{said}")
            else:
                timeline.append(f"Run {run} ({label}): evaluated: {combined_measures(report['evaluations'])}{said}")

            if not problem and reviews <= 0:
                return WorkflowResult(_fmt.OK, f"The agent submission was evaluated:\n{evaluation}", ret)

            if problem and error_retries <= 0:
                return WorkflowResult(_fmt.ERROR, f"{problem}\nSee {step_directory}", ret)

            # The logs are kept for the feedback while the step directories are renamed
            snapshot = temporary_directory()
            for name, path in list(feedback_files.items()):
                if Path(path).is_file():
                    copy(path, snapshot / name)
                    feedback_files[name] = snapshot / name
            for name in [step_directory.name, *stage_names(test_splits)]:
                if (ret / name).exists():
                    (ret / name).rename(ret / f"{name}-attempt-{run}")

            if problem:
                announce(f"Run {run} was rejected: {problem.splitlines()[0][:300]}")
                error_retries -= 1
                reviewed_digest = None
                feedback = (
                    f"Your solution in /tira-data/output/{SOLUTION_DIRECTORY} was rejected (run {run}): {problem}\n"
                    "The rejected solution is still in /tira-data/output. Available in "
                    f"/tira-data/input/{FEEDBACK_DIRECTORY}: the stdout.txt and stderr.txt of the run on the test "
                    "data (if it was executed). Fix exactly this problem in the existing solution, do not start from "
                    "scratch, and finish as soon as it is fixed."
                )
            else:
                announce(f"Run {run} was evaluated successfully, the agent reviews the result next")
                reviews -= 1
                reviewed_digest, reviewed_evaluation = digest, evaluation
                reviewed_evaluations = report["evaluations"]
                feedback = (
                    f"Your solution in /tira-data/output/{SOLUTION_DIRECTORY} was built and executed successfully on "
                    "unseen test data and the result was evaluated (run {run}). Review the results in "
                    f"/tira-data/input/{FEEDBACK_DIRECTORY}: stdout.txt and stderr.txt of the execution and "
                    "evaluation.prototext with the evaluation measures (these are the files of the split `test`; the results "
                    "of additional test splits have the split name as suffix, e.g., evaluation-test-02.prototext). Reason whether the results look reasonable. "
                    "If they do, finish immediately without changing anything. If they do not (e.g., errors in the "
                    "logs, or a very low score), modify the existing solution to fix it and finish as soon as it is "
                    "fixed. Do not start from scratch."
                ).replace("{run}", str(run))
