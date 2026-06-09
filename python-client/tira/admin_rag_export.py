from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tira.check_format import _fmt, check_format, lines_if_valid


def _sanitize_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()


def _parse_score(value: str) -> "int | float | None":
    try:
        numeric_value = float(value)
    except ValueError:
        return None

    if numeric_value.is_integer():
        return int(numeric_value)

    return numeric_value


def _display_name_and_key_prefix(eval_directory: Path, eval_root: Path) -> tuple[str, str]:
    parts = [part for part in eval_directory.relative_to(eval_root).parts if part != "results"]
    if not parts:
        parts = [eval_directory.name]

    return " / ".join(parts), "__".join(_sanitize_key(part) for part in parts)


def discover_trec_eval_directories(evals_directory: Path) -> list[Path]:
    if not evals_directory.exists() or not evals_directory.is_dir():
        raise ValueError(f"The evaluations directory does not exist: {evals_directory}")

    ret = set()
    candidates = {evals_directory}
    candidates.update(path for path in evals_directory.rglob("*") if path.is_dir())
    for path in sorted(candidates):
        if check_format(path, "trec-eval-leaderboard")[0] == _fmt.OK:
            ret.add(path)

    # Keep only the deepest matching directories: a parent is excluded when any other candidate is nested inside it.
    ret = {path for path in ret if not any(other != path and path in other.parents for other in ret)}

    if not ret:
        raise ValueError(f"No trec-eval leaderboard files were found below {evals_directory}.")

    return sorted(ret)


def load_rag_runs(runs_directory: Path) -> list[dict[str, str]]:
    if not runs_directory.exists() or not runs_directory.is_dir():
        raise ValueError(f"The runs directory does not exist: {runs_directory}")

    runs = {}

    for line in lines_if_valid(runs_directory, "trec-rag-runs"):
        metadata = line["metadata"]
        run_id = metadata["run_id"]
        team_id = metadata.get("team_id", "")

        if run_id not in runs:
            runs[run_id] = {"run_id": run_id, "team_id": team_id}
            continue

        if runs[run_id]["team_id"] != team_id:
            raise ValueError(
                f'Run "{run_id}" has inconsistent team ids: ' + f'{runs[run_id]["team_id"]} and {team_id}.'
            )

    if not runs:
        raise ValueError(f"No trec-rag runs were found in {runs_directory}.")

    return [runs[run_id] for run_id in sorted(runs)]


def _collect_scores(eval_directory: Path) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Parse the trec-eval leaderboard file and return (ordered_measures, run_to_scores) for ALL queries."""
    measures: list[str] = []
    run_to_scores: dict[str, dict[str, Any]] = {}

    for line in lines_if_valid(eval_directory, "trec-eval-leaderboard"):
        if line["run"] == "run_id" or str(line["query"]).lower() != "all":
            continue
        score = _parse_score(line["value"])
        if score is None:
            continue
        if line["metric"] not in measures:
            measures.append(line["metric"])
        run_to_scores.setdefault(line["run"], {})[line["metric"]] = score

    return measures, run_to_scores


def _load_all_query_scores(eval_directory: Path, expected_run_ids: Iterable[str]) -> dict[str, Any]:
    run_ids = set(expected_run_ids)
    measures, run_to_scores = _collect_scores(eval_directory)

    if not measures:
        raise ValueError(f"The evaluation directory {eval_directory} does not contain numeric ALL scores.")

    missing_runs = sorted(run_ids - set(run_to_scores))
    if missing_runs:
        raise ValueError(f"The evaluation directory {eval_directory} misses ALL scores for runs {missing_runs}.")

    extra_runs = sorted(set(run_to_scores) - run_ids)
    if extra_runs:
        raise ValueError(
            f"The evaluation directory {eval_directory} contains runs not found in the input runs: {extra_runs}."
        )

    for run_id in sorted(run_ids):
        missing_measures = [measure for measure in measures if measure not in run_to_scores[run_id]]
        if missing_measures:
            raise ValueError(
                f'The evaluation directory {eval_directory} misses ALL scores for run "{run_id}" '
                + f"and measures {missing_measures}."
            )

    return {"measures": measures, "run_to_scores": run_to_scores}


def build_rag_responses_aggregated_results(runs_directory: Path, evals_directory: Path) -> dict[str, Any]:
    runs = load_rag_runs(runs_directory)
    run_ids = [run["run_id"] for run in runs]

    evaluations = []
    ev_keys = []
    table_headers = [
        {"title": "Team", "key": "team_id"},
        {"title": "Run", "key": "run_id"},
    ]

    for eval_directory in discover_trec_eval_directories(evals_directory):
        display_name, key_prefix = _display_name_and_key_prefix(eval_directory, evals_directory)
        scores = _load_all_query_scores(eval_directory, run_ids)

        children = []
        for measure in scores["measures"]:
            key = f"{key_prefix}__{_sanitize_key(measure)}"
            ev_keys.append(key)
            children.append({"title": measure, "key": key})

        evaluations.append(
            {
                "display_name": display_name,
                "key_prefix": key_prefix,
                "measures": scores["measures"],
                "run_to_scores": scores["run_to_scores"],
            }
        )
        table_headers.append({"title": display_name, "align": "center", "children": children})

    lines = []
    for run in runs:
        line = {"team_id": run["team_id"], "run_id": run["run_id"]}
        for evaluation in evaluations:
            for measure in evaluation["measures"]:
                key = f'{evaluation["key_prefix"]}__{_sanitize_key(measure)}'
                line[key] = evaluation["run_to_scores"][run["run_id"]][measure]
        lines.append(line)

    table_headers_small_layout = [{"title": "Run", "key": "run_id"}]
    if evaluations and evaluations[0]["measures"]:
        first_measure = evaluations[0]["measures"][0]
        table_headers_small_layout.append(
            {
                "title": first_measure,
                "key": f'{evaluations[0]["key_prefix"]}__{_sanitize_key(first_measure)}',
            }
        )

    return {
        "title": "RAG Response Evaluations",
        "description": "Evaluation scores for the ALL column across all exported RAG runs.",
        "ev_keys": ev_keys,
        "lines": lines,
        "table_headers": table_headers,
        "table_headers_small_layout": table_headers_small_layout,
        "table_sort_by": [{"key": "run_id", "order": "asc"}],
    }


def export_rag_responses(runs_directory: Path, evals_directory: Path, output_directory: Path) -> Path:
    aggregated_results = build_rag_responses_aggregated_results(runs_directory, evals_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_file = output_directory / "aggregated-results.json"

    with open(output_file, "w") as f:
        json.dump(aggregated_results, f, indent=2)
        f.write("\n")

    result, message = check_format(output_directory, "aggregated-results.json")
    if result != _fmt.OK:
        raise ValueError(f"Failed to write a valid aggregated-results.json file: {message}")

    return output_file
