#!/usr/bin/env python3
"""Minimal reference baseline for the sorting-python task.

Reads the single *.jsonl file in --input (fields: id, unsorted) and writes predictions.jsonl to
--output with each array sorted in ascending order.

Usage:
    python3 sort.py --input <inputs-dir> --output <output-dir>
"""

import argparse
import json
import os


def find_jsonl(directory: str) -> str:
    matches = [f for f in os.listdir(directory) if f.endswith(".jsonl")]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one *.jsonl file in {directory}, found {matches}.")
    return os.path.join(directory, matches[0])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Directory containing the input *.jsonl file.")
    parser.add_argument("--output", required=True, help="Directory to write predictions.jsonl to.")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    predictions = []
    with open(find_jsonl(args.input)) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            predictions.append(json.dumps({"id": record["id"], "sorted": sorted(record["unsorted"])}))

    with open(os.path.join(args.output, "predictions.jsonl"), "w") as f:
        f.write("\n".join(predictions) + "\n")


if __name__ == "__main__":
    main()
