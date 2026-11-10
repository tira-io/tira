---
tira_configs:
  input_format:
    name: "coding-tasks"
  baseline:
    link: "baseline"
    command: "sh /tira-agent/run-agent.sh"
    # Small steps that run first in the devcontainer of each task; a failing step ends the task.
    steps:
      - name: devcontainer
        command: "sh /tira-agent/steps/01-devcontainer.sh"
      - name: hello-world-test
        command: "sh /tira-agent/steps/02-hello-world-test.sh"
      - name: ls-test
        command: "sh /tira-agent/steps/03-ls-test.sh"
    # stop_after_step stops after the named step of the first task (e.g., "result") so that it can be verified.
    # stop_after_step: "result"
tasks:
  - name: sorting-python
    path: sorting-python
  - name: sorting-java
    path: sorting-java
  - name: sorting-julia
    path: sorting-julia
---

# Coding Agent Sorting Tasks

> **Note:** This is an example dataset used to exemplify the `sandboxed-coding-agent` workflow.

This dataset consists of three independent tasks. In each of them, a coding agent has to write a program that sorts
lists of integers. The tasks differ only in the programming language and the devcontainer (`.devcontainer/`) the
agent works in. The front matter above declares the tasks (`name` and `path`); every task directory contains
a dataset card `README.md` that defines the task description, the `train` and `test` splits and the evaluator.

| Task | Language |
| --- | --- |
| [`sorting-python`](sorting-python/README.md) | Python |
| [`sorting-java`](sorting-java/README.md) | Java |
| [`sorting-julia`](sorting-julia/README.md) | Julia |

To run all tasks with the `sandboxed-coding-agent` workflow, pass the directory of this dataset as
`dataset_directory` in the workflow configuration (see `documentation/organizers/coding-agent-tasks.rst`).

## Running the Coding Agent on all Tasks

The `baseline/` directory holds the scripts of a coding agent, the [GitHub Copilot CLI](https://docs.github.com/copilot/concepts/agents/about-copilot-cli)
in BYOK mode, and [`skill.md`](baseline/skill.md), which tells the agent how to solve a task and how to hand in its
submission. The agent is started in the devcontainer of each task (`.devcontainer/`, built from its Dockerfile, which
installs the Copilot CLI); `baseline/` is mounted at `/tira-agent`. A dry run of `tira-cli dataset-submission` on this
directory runs the `sandboxed-coding-agent` workflow for each task: the agent only sees the `train` split and the task
description, and its submission is evaluated on the `test` split. Forward the LLM configuration from your environment
with `--forward-environment-variable` (the variables are forwarded, not stored; network access is restricted to the
hostname of `COPILOT_PROVIDER_BASE_URL`, use a fully qualified hostname as it is resolved inside docker). Run this from
the directory that contains this dataset, i.e., `python-client/tests/resources/example-datasets/`:

```bash
export COPILOT_PROVIDER_TYPE=openai COPILOT_MODEL=... COPILOT_PROVIDER_BASE_URL=... COPILOT_PROVIDER_API_KEY=...

tira-cli dataset-submission \
  --path coding-agent-sorting-tasks \
  --task my-task \
  --split train \
  --dry-run \
  --forward-environment-variable COPILOT_PROVIDER_TYPE COPILOT_MODEL COPILOT_PROVIDER_BASE_URL COPILOT_PROVIDER_API_KEY
```

## The Workflow per Task

The workflow runs the tasks one after another and continues with the next task if one fails. For each task it prints
the current stage as `[task] ...`, and the final result as a checklist. The stages are:

1. **Smoke tests** (`01-devcontainer/`, `02-hello-world-test/`, `03-ls-test/`): in the devcontainer of the task, is
   the Copilot CLI installed, does the LLM answer "How are you?", and can the agent call the shell tool? Each is
   run once; a failing step ends the task.
2. **Agent run** (`04-result/`): the agent writes `solution/` and `submission-metadata.yml` (with the `command` that
   executes the submission). It sees only the task description and the `train` split at `/tira-data/input/`, and
   the devcontainer at `/tira-data/input/.devcontainer/`: the `Dockerfile` of its solution must start with the
   instructions of the devcontainer's `Dockerfile`. A run is stopped after 10 minutes (`AGENT_TIMEOUT_SECONDS` in
   `baseline/run-agent.sh`). Result: `source-code.zip`, `submission-metadata.yml`, `stdout.txt`, `stderr.txt`,
   `network-access.log`.
3. **Check, build, test run, evaluation** (`05-predictions/`, `06-results/`): the workflow checks the result, builds
   the docker image from `source-code.zip`, runs the `command` of `submission-metadata.yml` on the unseen `test`
   inputs, and runs the evaluator on the predictions.

Every stage directory records what that stage was given, so the input can be analyzed afterwards:

- `input/README.md`: the task description exactly as the agent saw it (without front matter).
- `input/feedback/`: the feedback of the run (`feedback.md`, plus `stdout.txt`, `stderr.txt`, and
  `evaluation.prototext` for retries and reviews).
- `input/manifest.txt`: the other mounted files (the `train` split and the devcontainer) with their sizes.
- `command.txt`: the exact command of the stage.
- `prompt.txt`: the exact prompt passed to the Copilot CLI (the scripts in `baseline/` write it).

4. **Error retries** (at most 5, `agent_retries`): if anything in stage 3 fails, the agent is started again. Its
   rejected solution is still in `/tira-data/output`, and `/tira-data/input/feedback/` contains `feedback.md` (the
   reason), and `stdout.txt` and `stderr.txt` of the failed test run. Back to stage 3.
5. **Reviews** (at most 5, `review_rounds`): after a successful evaluation, the agent is started again, and
   `/tira-data/input/feedback/` contains `feedback.md` (the submission ran successfully on unseen test data),
   `stdout.txt`, `stderr.txt`, and `evaluation.prototext`. If the agent finds the result reasonable it changes
   nothing, which ends the workflow for the task. If it modifies `solution/`, the workflow continues with stage 3.
   (Changes in `__pycache__` and `.git` are ignored.)

Every agent start is announced with its reason, e.g., `Agent run 3: reviewing the evaluation (review 1 of 5)`, so
repeated starts are expected only for retries and reviews. At most 1 + 5 + 5 = 11 agent runs per task happen, each
limited to 10 minutes. Replaced results are kept as `04-result-attempt-N/`, `05-predictions-attempt-N/`, and
`06-results-attempt-N/`; an unchanged review run is kept as `04-result-review-N/`. Set `stop_after_step: "result"` in
the front matter to stop after the first agent run of the first task.

The result is printed per task:

```
✓ sorting-python:
  - ✓ Coding Agent works and was able to finish basic tasks
  - ✓ Agent produced code and metadata (3 attempts)
  - ✓ Final code builds into docker image
  - ✓ Final result of evaluation: Exact Match Accuracy=1.0
  Results: /tmp/tira-…/sorting-python

✓ 1 of 1 tasks succeeded.
```

In dataset mode the `Results:` path points into the dataset result directory (e.g., `/tmp/tira-…/sorting-python`), not
to the temporary directory of the individual task.

`--task` and `--split` are required by the CLI but not used for this dataset, as every task defines its own splits.
Uploading such datasets is not yet supported, so `--dry-run` is mandatory. Add `--skip-baseline` to only check that the
declared tasks exist, without building or running the agent. The command requires the `datasets` and `gitpython`
packages.

## Validating a Single Task with a Dry Run

Each task directory is a dataset on its own. Validate the packaging of a task (dataset card, inputs, truths) without
running an agent (run from the same directory as above):

```bash
tira-cli dataset-submission \
  --path coding-agent-sorting-tasks/sorting-python \
  --task coding-agent-sorting-tasks \
  --split train \
  --dry-run \
  --skip-baseline
```

Use `sorting-java` or `sorting-julia` as `--path` for the other tasks, and `--split test` for the test split.
