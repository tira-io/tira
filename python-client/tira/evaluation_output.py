"""Reading and writing the output of an evaluator in the formats that an evaluator can be configured to produce.

An evaluation is a flat dictionary that maps measure names to values. The default output format is `prototext`
(`evaluation.prototext`). All other formats are identified by the same names as the formats in `tira.check_format`.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_OUTPUT_FORMAT = "prototext"

# Maps the name of an output format to the name of the file that is written for this format.
OUTPUT_FORMAT_TO_FILE_NAME: "Dict[str, str]" = {
    DEFAULT_OUTPUT_FORMAT: "evaluation.prototext",
    "json": "evaluation.json",
    "*.jsonl": "evaluation.jsonl",
    "*.tsv": "evaluation.tsv",
    "trec-eval-leaderboard": "evaluation.txt",
}

SUPPORTED_OUTPUT_FORMATS = list(OUTPUT_FORMAT_TO_FILE_NAME.keys())

TREC_EVAL_AGGREGATE_QUERY = "all"
TREC_EVAL_RUN_ID = "evaluation"


def _num(value: Any) -> "Any":
    from tira.io_utils import __num as to_num  # noqa

    return to_num(value) if isinstance(value, str) else value


def validate_output_format(output_format: "Optional[str]") -> str:
    output_format = output_format or DEFAULT_OUTPUT_FORMAT
    if output_format not in OUTPUT_FORMAT_TO_FILE_NAME:
        raise ValueError(
            f"The evaluation output format '{output_format}' is not supported. "
            f"Valid formats are: {SUPPORTED_OUTPUT_FORMATS}."
        )
    return output_format


def _single_file(directory: Path, output_format: str) -> Path:
    expected = Path(directory) / OUTPUT_FORMAT_TO_FILE_NAME[output_format]
    if expected.is_file():
        return expected

    suffix = Path(OUTPUT_FORMAT_TO_FILE_NAME[output_format]).suffix
    candidates = sorted(i for i in Path(directory).glob("*") if i.is_file() and i.suffix == suffix)
    if len(candidates) != 1:
        raise ValueError(
            f"Expected exactly one evaluation file in the format '{output_format}' in {directory}. "
            f"Got: {[str(i) for i in candidates]}"
        )
    return candidates[0]


def _parse_prototext(file_name: Path) -> "Dict[str, Any]":
    ret = {}
    for i in [i for i in file_name.read_text().split("measure") if "key:" in i and "value:" in i]:
        key = i.split("key:")[1].split("value")[0].split('"')[1]
        value = i.split("key:")[1].split("value")[1].split('"')[1]
        ret[key.strip()] = _num(value.strip())
    return ret


def _parse_json(file_name: Path) -> "Dict[str, Any]":
    content = json.loads(file_name.read_text())
    if not isinstance(content, dict):
        raise ValueError(f"The evaluation in {file_name} must be a json object that maps measures to values.")
    return content


def _parse_jsonl(file_name: Path) -> "Dict[str, Any]":
    ret = {}
    for line in file_name.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if not isinstance(entry, dict):
            raise ValueError(f"Each line of the evaluation in {file_name} must be a json object.")
        if set(entry.keys()) == {"key", "value"}:
            ret[entry["key"]] = entry["value"]
        else:
            ret.update(entry)
    return ret


def _parse_tsv(file_name: Path) -> "Dict[str, Any]":
    ret = {}
    for line in file_name.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            raise ValueError(f"Could not parse line '{line}' in {file_name}: Expected a key and a value.")
        ret[parts[0].strip()] = _num(parts[1].strip())
    return ret


def _parse_trec_eval_leaderboard(file_name: Path) -> "Dict[str, Any]":
    ret = {}
    runs = set()
    for line in file_name.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"Could not parse line '{line}' in {file_name}: Expected 'run query measure value'.")
        run, query, measure, value = parts
        if query != TREC_EVAL_AGGREGATE_QUERY:
            continue
        runs.add(run)
        ret[measure] = _num(value)

    if len(runs) > 1:
        raise ValueError(f"The evaluation in {file_name} must contain the results of exactly one run, got: {runs}.")
    return ret


_PARSERS = {
    DEFAULT_OUTPUT_FORMAT: _parse_prototext,
    "json": _parse_json,
    "*.jsonl": _parse_jsonl,
    "*.tsv": _parse_tsv,
    "trec-eval-leaderboard": _parse_trec_eval_leaderboard,
}


def parse_evaluation_output(directory: Path, output_format: "Optional[str]" = None) -> "Dict[str, Any]":
    """Parse the evaluation in `directory` that was written in `output_format` to a dict of measures to values.

    If no `output_format` is given, the format is detected via the file names (and defaults to prototext).
    """
    if not output_format:
        output_format = next(
            (f for f, name in OUTPUT_FORMAT_TO_FILE_NAME.items() if (Path(directory) / name).is_file()),
            DEFAULT_OUTPUT_FORMAT,
        )
    output_format = validate_output_format(output_format)
    return _PARSERS[output_format](_single_file(directory, output_format))


def format_evaluation_output(evaluation: "Dict[str, Any]", output_format: "Optional[str]" = None) -> str:
    """Serialize the evaluation (a dict of measures to values) to the content of an evaluation file."""
    output_format = validate_output_format(output_format)

    if output_format == DEFAULT_OUTPUT_FORMAT:
        from tira.io_utils import to_prototext

        return to_prototext([evaluation])
    if output_format == "json":
        return json.dumps(evaluation, indent=2) + "\n"
    if output_format == "*.jsonl":
        return "".join(json.dumps({"key": k, "value": v}) + "\n" for k, v in evaluation.items())
    if output_format == "*.tsv":
        return "".join(f"{k}\t{v}\n" for k, v in evaluation.items())

    for measure in evaluation:
        if len(str(measure).split()) != 1:
            raise ValueError(f"The measure '{measure}' can not be written in the whitespace-separated {output_format}.")

    return "".join(f"{TREC_EVAL_RUN_ID} {TREC_EVAL_AGGREGATE_QUERY} {k} {v}\n" for k, v in evaluation.items())


def write_evaluation_output(
    evaluation: "Dict[str, Any]", output_dir: Path, output_format: "Optional[str]" = None
) -> Path:
    output_format = validate_output_format(output_format)
    target = Path(output_dir) / OUTPUT_FORMAT_TO_FILE_NAME[output_format]
    target.write_text(format_evaluation_output(evaluation, output_format))
    return target
