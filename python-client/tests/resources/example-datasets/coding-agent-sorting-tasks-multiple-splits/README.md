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
  - name: sorting-python-multiple-splits
    path: sorting-python-multiple-splits
---

# Coding Agent Sorting Task with Multiple Splits

> **Note:** This is an example dataset used to exemplify and test the `sandboxed-coding-agent` workflow with
> multiple train and test splits per task.

Variant of [`coding-agent-sorting-tasks`](../coding-agent-sorting-tasks/README.md) whose single task
[`sorting-python-multiple-splits`](sorting-python-multiple-splits/README.md) has two train splits (`train`, `train-02`)
and two test splits (`test`, `test-02`). The agent sees all train splits; its submission is run and evaluated on each
test split separately. Splits are named `train`/`test` plus optional `train-<name>`/`test-<name>` and are described in
`split_descriptions` of the dataset card of the task. The agent scripts in `baseline/` are the same as in the
original dataset. See `documentation/organizers/coding-agent-tasks.rst`.

## Running the Coding Agent

Run this from the directory that contains this dataset, i.e., `python-client/tests/resources/example-datasets/`
(the LLM configuration is forwarded from your environment, see the README of the original dataset for details):

```bash
export COPILOT_PROVIDER_TYPE=openai COPILOT_MODEL=... COPILOT_PROVIDER_BASE_URL=... COPILOT_PROVIDER_API_KEY=...

tira-cli dataset-submission \
  --path coding-agent-sorting-tasks-multiple-splits \
  --task my-task \
  --split train \
  --dry-run \
  --forward-environment-variable COPILOT_PROVIDER_TYPE COPILOT_MODEL COPILOT_PROVIDER_BASE_URL COPILOT_PROVIDER_API_KEY
```

The result lists the measures of every test split, e.g., `test: ...; test-02: ...`, and the result directory contains
`05-predictions`/`06-results` (`test`) and `05-predictions-test-02`/`06-results-test-02` (`test-02`).

## Validating the Packaging without an Agent

Check the declared task and its dataset card (splits, inputs, truths) without building or running the agent:

```bash
tira-cli dataset-submission \
  --path coding-agent-sorting-tasks-multiple-splits \
  --task my-task \
  --split train \
  --dry-run \
  --skip-baseline
```

The same check works for a single task with `--path coding-agent-sorting-tasks-multiple-splits/sorting-python-multiple-splits`
and `--split train-02` or `--split test-02` for the additional splits.
