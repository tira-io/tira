---
tira_configs:
  input_format:
    name: "coding-tasks"
tasks:
  - name: sisap-2026-julia
    path: sisap-2026-julia
  - name: sisap-2026-rust
    path: sisap-2026-rust
---

# Coding Agent Task: SISAP 2026 Indexing Challenge (Spot Check)

> **Note:** This is an example dataset used to test the `sandboxed-coding-agent` workflow.

The task [`sisap-2026-julia`](sisap-2026-julia/README.md) uses the Julia example of the SISAP 2026 challenge as
baseline, [`sisap-2026-rust`](sisap-2026-rust/README.md) is the same task in Rust (exact brute-force baseline; its
`data` is a symbolic link to the data of the Julia task). Both have three train splits (`train`, `train-task-2`, `train-task-3`) and the same three test splits, one for
each sub-task (all-kNN graph, kNN search on dense vectors, kNN search on sparse vectors). The spot-check data (about
31 MB) is stored once in `sisap-2026-julia/data/` and used for train and test. The HDF5 files contain the ground truth,
so the agent sees the truth of the test splits in this example.

## Running the Coding Agent

Run this from `python-client/tests/resources/example-datasets/`:

```bash
export COPILOT_PROVIDER_TYPE=openai COPILOT_MODEL=... COPILOT_PROVIDER_BASE_URL=... COPILOT_PROVIDER_API_KEY=...

tira-cli run coding-agent \
  --path coding-agent-sisap-2026 \
  --agent ../example-agents/copilot-cli \
  --forward-environment-variable COPILOT_PROVIDER_TYPE COPILOT_MODEL COPILOT_PROVIDER_BASE_URL COPILOT_PROVIDER_API_KEY
```

## Validating the Packaging without an Agent

```bash
tira-cli dataset-submission \
  --path coding-agent-sisap-2026 \
  --task my-task \
  --split train \
  --dry-run
```
