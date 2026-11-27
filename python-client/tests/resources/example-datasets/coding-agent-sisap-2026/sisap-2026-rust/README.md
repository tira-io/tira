---
configs:
- config_name: inputs
  data_files:
  - split: train
    path:
      - "data/task-1-spot-check/benchmark-dev-gooaq-small.h5"
      - "data/task-1-spot-check/config.json"
  - split: train-task-2
    path:
      - "data/task-2-spot-check/benchmark-dev-llama-small.h5"
      - "data/task-2-spot-check/config.json"
  - split: train-task-3
    path:
      - "data/task-3-spot-check/benchmark-dev-fiqa-small.h5"
      - "data/task-3-spot-check/config.json"
  - split: test
    path:
      - "data/task-1-spot-check/benchmark-dev-gooaq-small.h5"
      - "data/task-1-spot-check/config.json"
  - split: test-task-2
    path:
      - "data/task-2-spot-check/benchmark-dev-llama-small.h5"
      - "data/task-2-spot-check/config.json"
  - split: test-task-3
    path:
      - "data/task-3-spot-check/benchmark-dev-fiqa-small.h5"
      - "data/task-3-spot-check/config.json"
- config_name: truths
  data_files:
  - split: train
    path:
      - "data/task-1-spot-check/benchmark-dev-gooaq-small.h5"
      - "data/task-1-spot-check/config.json"
  - split: train-task-2
    path:
      - "data/task-2-spot-check/benchmark-dev-llama-small.h5"
      - "data/task-2-spot-check/config.json"
  - split: train-task-3
    path:
      - "data/task-3-spot-check/benchmark-dev-fiqa-small.h5"
      - "data/task-3-spot-check/config.json"
  - split: test
    path:
      - "data/task-1-spot-check/benchmark-dev-gooaq-small.h5"
      - "data/task-1-spot-check/config.json"
  - split: test-task-2
    path:
      - "data/task-2-spot-check/benchmark-dev-llama-small.h5"
      - "data/task-2-spot-check/config.json"
  - split: test-task-3
    path:
      - "data/task-3-spot-check/benchmark-dev-fiqa-small.h5"
      - "data/task-3-spot-check/config.json"

tira_configs:
  # The same spot-check files are used for train and test: the h5 files contain data, queries, and ground truth.
  split_descriptions:
    train: "Task 1 (all-kNN graph, k=15) on gooaq-small: 10,000 dense float32 vectors with 384 dimensions."
    train-task-2: "Task 2 (MIPS / kNN search, k=30) on llama-small: 14,000 dense vectors with 128 dimensions and 400 queries."
    train-task-3: "Task 3 (sparse kNN search, k=30) on fiqa-small: SPLADE sparse vectors stored as CSR and 600 queries."
    test: "Task 1 (all-kNN graph, k=15) on gooaq-small: 10,000 dense float32 vectors with 384 dimensions."
    test-task-2: "Task 2 (MIPS / kNN search, k=30) on llama-small: 14,000 dense vectors with 128 dimensions and 400 queries."
    test-task-3: "Task 3 (sparse kNN search, k=30) on fiqa-small: SPLADE sparse vectors stored as CSR and 600 queries."
  resolve_inputs_to: "data"
  resolve_truths_to: "data"
  default_upload_name: "results.h5"
  input_format:
    name: "*.h5"
  truth_format:
    name: "*.h5"
  baseline:
    link: "baseline"
    command: "sisap2026 --input $inputDataset/*.h5 --task-description $inputDataset/config.json --output $outputDir"
    format:
      name: "*.h5"
  evaluator:
    image: "evaluator"
    command: "python3 /eval.py $inputDataset/*.json $inputDataset/*.h5 $inputRun $outputDir/evaluation.prototext"
---

# SISAP 2026 Indexing Challenge (Spot Check, Rust)

> **Note:** This is an example dataset used to test the `sandboxed-coding-agent` workflow with the small
> "spot-check" data of the [SISAP 2026 Indexing Challenge](https://sisap-challenges.github.io/). It is not (yet)
> registered with a real TIRA task.

## Task

Implement a **Rust** program (Rust 1.88 with `cargo`, available in the devcontainer) that builds an approximate nearest neighbor
index and answers nearest neighbor queries. The aim is a high recall with a small build and query time. There are
three sub-tasks, each with its own data (one HDF5 file) and its own `config.json`:

| `task` in `config.json` | Description | Data |
|---|---|---|
| `task1` | All-kNN graph: find the `k` nearest neighbors (cosine) of every vector, **excluding the vector itself**. | `train` (dense, float32) |
| `task2` | kNN search with maximum inner product / cosine similarity on dense vectors. | `train` (database) and `test/queries` |
| `task3` | kNN search on sparse (SPLADE) vectors stored in CSR format. | `train` and `otest/queries` (CSR groups with `data`, `indices`, `indptr`, attribute `shape`) |

The `config.json` next to each HDF5 file describes the sub-task: the key `task`, the dataset names of the database
(`data`), the queries (`queries`, if any), the ground truth (`gt_I`), the number of neighbors `k`, and whether the vectors are
`sparse`. Your program must read this file and handle all three sub-tasks with the same code, so that it also works on other
datasets of the three sub-tasks.

## Input and Output

The program is called once for every dataset (HDF5 file together with its `config.json`) with:

```bash
<command> --input <file.h5> --task-description <config.json> --output <directory>
```

It must write at least one HDF5 file (`*.h5`) to the output directory with:

- `knns`: the identifiers of the `k` nearest neighbors for every query (for `task1`: for every vector), 1-based
  (as in the ground truth `gt_I`), `Int32`, in the order of increasing distance (`n` rows and `k` columns when read
  with h5py, i.e., an `n x k` `ndarray` array in Rust).
- `dists`: the corresponding distances, `Float32`, same shape as `knns`.
- The attributes `algo`, `buildtime`, `querytime` (seconds), and `params`.

Several `*.h5` files (e.g., different parameter settings, trading recall against query time) may be written.
The reference implementation in `baseline/src/main.rs` shows the file format (`save_results`).

## Rules

- The program is run **without network access** and without access to any LLM. The devcontainer has the crates
  `hdf5-metno` (with `libhdf5`), `ndarray`, `rayon`, and `serde_json` preinstalled in `CARGO_HOME=/opt/cargo`; keep this
  setting in the `Dockerfile` and build with `cargo build --release --offline`. Other crates are not available.
- The `Dockerfile` must build the program and the `command` must run the compiled binary (no `cargo run`).
- The program must read the path of the data only from its command-line arguments, not from fixed locations.
- Do not copy or hard-code ground truth. The ground truth is contained in the HDF5 files only for evaluation.

## Data

The data is in `data/task-1-spot-check/`, `data/task-2-spot-check/`, and `data/task-3-spot-check/`
(`train`, `train-task-2`, `train-task-3` correspond to these three sub-tasks). Each directory contains an HDF5 file and
its `config.json`. Note: in this example, the evaluation uses the same files and therefore the same sub-tasks again.

## Baseline

The baseline in `baseline/` is an exact brute-force search (dot product, parallelized with `rayon`) for all three
sub-tasks. It reaches the maximum recall, but is slow on large data; a good solution uses an approximate index.
Build and invoke it with:

```bash
cargo build --release --offline
target/release/sisap2026 --input data/task-2-spot-check/benchmark-dev-llama-small.h5 \
  --task-description data/task-2-spot-check/config.json --output out/
```

## Evaluation

For each `*.h5` file in the output, the evaluation computes the recall of the first `k` entries of `knns`
against the first `k` entries of the ground truth `gt_I`. The reported measures are the minimum and maximum recall,
build time and query time over all output files of one sub-task.
