---
configs:
- config_name: inputs
  data_files:
  - split: train
    path: "inputs/train.jsonl"
  - split: test
    path: "inputs/test.jsonl"
  - split: train-02
    path: "inputs/train-02.jsonl"
  - split: test-02
    path: "inputs/test-02.jsonl"
- config_name: truths
  data_files:
  - split: train
    path: "truths/train.jsonl"
  - split: test
    path: "truths/test.jsonl"
  - split: train-02
    path: "truths/train-02.jsonl"
  - split: test-02
    path: "truths/test-02.jsonl"

tira_configs:
  # 'train' and 'test' are required, further splits are named 'train-<name>' and 'test-<name>'. The agent sees
  # all train splits, its submission is run and evaluated on every test split.
  split_descriptions:
    train: "Short lists (2 to 10 integers)."
    train-02: "Long lists (50 to 100 integers in the range -1000 to 1000)."
    test: "Short lists (2 to 10 integers), as in train."
    test-02: "Edge cases: empty lists, single elements, many duplicates, and lists of 200 integers."
  resolve_inputs_to: "inputs"
  resolve_truths_to: "truths"
  default_upload_name: "predictions.jsonl"
  input_format:
    name: "*.jsonl"
  truth_format:
    name: "*.jsonl"
  baseline:
    link: "baseline"
    command: "python3 /sort.py --input $inputDataset --output $outputDir"
    format:
      name: "*.jsonl"
  evaluator:
    image: "evaluator"
    command: "python3 /evaluate.py --predictions $inputRun --truths $inputDataset --output $outputDir"
---

# Sort a List of Integers (Python, Multiple Splits)

> **Note:** This is a dummy example dataset used to test the `sandboxed-coding-agent` workflow. It is not (yet)
> registered with a real TIRA task.

## Task

Implement a Python program that reads a JSON Lines file of unsorted integer arrays and writes a JSON Lines file
in which every array is sorted in ascending order.

Each line of the input file is a JSON object with the fields:

- `id`: a unique identifier for the instance.
- `unsorted`: a list of integers in arbitrary order.

For every input line, write one output line with the fields:

- `id`: the same identifier as the corresponding input line.
- `sorted`: the `unsorted` list, sorted in ascending order.

The program must be implemented in Python and run inside the devcontainer defined in `.devcontainer/`.

## Train Splits

The `train` split is made of `inputs/train.jsonl` (`id`, `unsorted`) and `truths/train.jsonl` (`id`,
`expected_sorted`). The additional split `train-02` (`inputs/train-02.jsonl`, `truths/train-02.jsonl`) contains
long lists. All files of all train splits are visible to the agent so that it may validate its implementation
before submission.

## Test Splits

The `test` and `test-02` splits are likewise made of `inputs/<split>.jsonl` and `truths/<split>.jsonl`. None of
them is shown to the agent during the agent phase; the truths are used only during the evaluation phase to score
the submission, which is run and evaluated on each test split separately.

## Baseline

The minimal reference baseline for this task is implemented in Python and lives in `baseline/sort.py`. It reads
the single `*.jsonl` file found in its `--input` directory and writes a `predictions.jsonl` file to its
`--output` directory, with every `unsorted` array replaced by its ascending sort under the `sorted` field.
Invoke it with:

```bash
python3 baseline/sort.py --input inputs/ --output out/
```

## Evaluation

A submission is scored by the fraction of test instances for which the produced `sorted` array exactly matches
the corresponding `expected_sorted` array from `truths/test.jsonl` (accuracy). The score ranges from `0.0` to
`1.0`: `1.0` is the best possible score (every test instance was sorted correctly), `0.0` is the worst (no
instance was sorted correctly), and values in between indicate the fraction of correctly sorted instances.

The minimal reference evaluator for this task is implemented in Python and lives in `evaluator/evaluate.py`. It
reads the submission's predictions file (one JSON object per line, with `id` and `sorted` fields) and the
truths file of the split being scored (`--predictions`/`--truths` may each be a `*.jsonl` file, or a directory
containing exactly one `*.jsonl` file), and prints the exact-match accuracy as JSON. Invoke it with:

```bash
python3 evaluator/evaluate.py --predictions predictions.jsonl --truths truths/test.jsonl
```

Add `--output <dir>` to instead write the result as TIRA's `evaluation.prototext` into `<dir>`.
