#!/usr/bin/env python3
"""Minimal evaluator for the sorting-python task.

Compares a predictions file against a truths file and reports exact-match accuracy: the
fraction of instances for which the submitted "sorted" array exactly equals the
"expected_sorted" array from the truths file. A score of 1.0 is best (all predictions correct)
and 0.0 is worst (no predictions correct).

--predictions and --truths may each be either a *.jsonl file directly, or a directory that
contains exactly one *.jsonl file.

Usage:
    # Print the result as JSON to stdout.
    python3 evaluate.py --predictions predictions.jsonl --truths truths.jsonl

    # Write the result as TIRA's evaluation.prototext instead.
    python3 evaluate.py --predictions predictions.jsonl --truths truths.jsonl --output out-dir
"""

import argparse
import json
import os


def resolve_jsonl(path: str) -> str:
    if os.path.isdir(path):
        matches = [f for f in os.listdir(path) if f.endswith(".jsonl")]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one *.jsonl file in {path}, found {matches}.")
        return os.path.join(path, matches[0])
    return path


def load_jsonl(path: str) -> dict:
    records = {}
    with open(resolve_jsonl(path)) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            records[record["id"]] = record
    return records


def to_prototext(measures: dict) -> str:
    ret = ""
    for key, value in measures.items():
        title = key.replace("-", " ").replace("_", " ").title()
        ret += 'measure{\n  key: "' + title + '"\n  value: "' + str(value) + '"\n}\n'
    return ret


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--predictions", required=True, help="Path to the submission's predictions.jsonl (file or directory)."
    )
    parser.add_argument(
        "--truths", required=True, help="Path to the truths.jsonl of the split being evaluated (file or directory)."
    )
    parser.add_argument(
        "--output", required=False, help="If set, write evaluation.prototext into this directory instead of stdout."
    )
    args = parser.parse_args()

    truths = load_jsonl(args.truths)
    predictions = load_jsonl(args.predictions)

    correct = 0
    for instance_id, truth in truths.items():
        prediction = predictions.get(instance_id)
        if prediction is not None and prediction.get("sorted") == truth["expected_sorted"]:
            correct += 1

    accuracy = correct / len(truths) if truths else 0.0
    measures = {"exact-match-accuracy": accuracy}

    if args.output:
        os.makedirs(args.output, exist_ok=True)
        with open(os.path.join(args.output, "evaluation.prototext"), "w") as f:
            f.write(to_prototext(measures))
    else:
        print(json.dumps(measures))


if __name__ == "__main__":
    main()
