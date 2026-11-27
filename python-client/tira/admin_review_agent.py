"""Runs a Copilot CLI agent in a sandbox (docker) that reviews the runs prepared by admin_review_runs, and
loads/summarizes the reviews that the agent wrote."""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from tira.admin_review_runs import BATCHES_DIRECTORY

# The CA certificates are required: the native HTTP client of the Copilot CLI fails without a system trust store.
REVIEW_AGENT_DOCKERFILE = """FROM node:22-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && npm install -g @github/copilot
"""
# The tag depends on the Dockerfile so that a changed Dockerfile is rebuilt.
REVIEW_AGENT_IMAGE = "tira-review-agent:" + hashlib.sha256(REVIEW_AGENT_DOCKERFILE.encode()).hexdigest()[:12]
REQUIRED_ENVIRONMENT_VARIABLES = [
    "COPILOT_PROVIDER_TYPE",
    "COPILOT_PROVIDER_BASE_URL",
    "COPILOT_MODEL",
    "COPILOT_PROVIDER_API_KEY",
]
INPUT_MOUNT = "/tira-data/input"
OUTPUT_MOUNT = "/tira-data/output"
DEFAULT_TIMEOUT_SECONDS = 3600

AGENT_SCRIPT = """set -e
export COPILOT_HOME=/tmp/copilot-home HOME=/tmp
cd /tira-data/output
PROMPT="$(cat /tira-data/input/README.md)

Now follow these instructions. The manifest of what is to be reviewed is /tira-data/input/manifest.json."
timeout "$AGENT_TIMEOUT_SECONDS" copilot -p "$PROMPT" --allow-all-tools --allow-all-paths --no-ask-user \\
    --no-auto-update --stream off --no-color --log-dir /tira-data/output/copilot-logs
"""

CHECKS = ["output_reasonable", "software_failure", "hacking_attempt", "data_leak_attempt"]
OK_STATUSES = {
    "output_reasonable": {"ok", "problem", "unclear"},
    "software_failure": {"ok", "problem", "unclear"},
    "hacking_attempt": {"ok", "suspicious", "unclear"},
    "data_leak_attempt": {"ok", "suspicious", "unclear"},
}
VERDICTS = {"valid", "invalid", "needs_human_review"}


def shorten(text: Any, length: int = 120) -> str:
    """The start of the text in a single line (for the terminal; the full text is in the review files)."""
    text = " ".join(str(text).split())
    return text if len(text) <= length else text[: length - 1].rstrip() + "…"


def _batch_mounts(review_directory: Path, batch_directory: Path) -> dict:
    """The read-only docker mounts that make up the input of the agent for the batch."""
    from tira.local_execution_integration import translate_tmp_dir_for_docker_mount

    def mount(relative_path: str) -> dict:
        source = review_directory / relative_path
        return {translate_tmp_dir_for_docker_mount(source): {"bind": f"{INPUT_MOUNT}/{relative_path}", "mode": "ro"}}

    manifest = json.loads((batch_directory / "manifest.json").read_text())
    ret = {}
    for name in ("README.md", "manifest.json"):
        source = translate_tmp_dir_for_docker_mount(batch_directory / name)
        ret[source] = {"bind": f"{INPUT_MOUNT}/{name}", "mode": "ro"}

    for run in manifest["runs"] + manifest["example_runs"]:
        ret.update(mount(run["location"]))
        for evaluation in run["evaluations"]:
            ret.update(mount(evaluation["location"]))

    for path in manifest.get("input_paths", []):
        ret.update(mount(path))

    return ret


def run_review_agent(
    review_directory: Path,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    environment: Optional[dict] = None,
    output_directory: Optional[Path] = None,
    on_batch_done: Optional[Callable[[Path, Path], None]] = None,
) -> Path:
    """Runs the agent on the batches of the review directory (mounted read-only) and returns the output directory of the
    agent
    (mounted read-write), which will contain the reviews. The output directory defaults to `agent-output` in the
    review directory (recreated on each run); for a configured one, a fresh subdirectory is created in it on each
    run (so that reviews of earlier runs can never be mistaken for the reviews of this run).
    The agent can only reach the host of COPILOT_PROVIDER_BASE_URL (through a filtering proxy). After each batch,
    on_batch_done is called with the directory of the batch and the output directory (errors
    of the callback are logged and do not stop the remaining batches)."""
    import docker

    from tira.local_execution_integration import translate_tmp_dir_for_docker_mount
    from tira.network_proxy import start_network_proxy

    environment = dict(os.environ if environment is None else environment)
    missing = [i for i in REQUIRED_ENVIRONMENT_VARIABLES if not environment.get(i)]
    if missing:
        raise ValueError("The following environment variables must be set: " + ", ".join(missing) + ".")

    hostname = urlparse(environment["COPILOT_PROVIDER_BASE_URL"]).hostname
    if not hostname:
        raise ValueError("COPILOT_PROVIDER_BASE_URL must be a URL with a hostname.")

    review_directory = Path(review_directory).resolve()
    if output_directory is None:
        output_directory = review_directory / "agent-output"
        shutil.rmtree(output_directory, ignore_errors=True)
    else:
        output_directory = Path(output_directory) / f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    output_directory = Path(output_directory).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    client = docker.from_env()
    try:
        client.images.get(REVIEW_AGENT_IMAGE)
    except docker.errors.ImageNotFound:
        logging.info(f"Building the image {REVIEW_AGENT_IMAGE} ...")
        client.images.build(fileobj=io.BytesIO(REVIEW_AGENT_DOCKERFILE.encode()), tag=REVIEW_AGENT_IMAGE, rm=True)

    container_environment = {k: environment[k] for k in REQUIRED_ENVIRONMENT_VARIABLES}
    container_environment["AGENT_TIMEOUT_SECONDS"] = str(timeout_seconds)
    proxy = start_network_proxy(client, [hostname], access_log_file=output_directory / "network-access.log")
    container_environment.update(proxy.environment_variables)

    # One container per batch of runs. A batch is independent of everything else: the agent only gets the README.md and
    # manifest.json of the batch and the directories of the runs, examples, and evaluations that the batch lists.
    batch_directories = sorted((review_directory / BATCHES_DIRECTORY).glob("*"))
    batches = [_batch_mounts(review_directory, d) for d in batch_directories]
    if not batches:
        logging.warning(f"No batches found in {review_directory}, nothing to review.")

    logs = []
    try:
        for number, batch_mounts in enumerate(batches, start=1):
            print(f"Reviewing batch {number}/{len(batches)} ...", flush=True)
            container = None
            try:
                container = client.containers.run(
                    REVIEW_AGENT_IMAGE,
                    entrypoint="sh",
                    command=["-c", AGENT_SCRIPT],
                    environment=container_environment,
                    volumes={
                        translate_tmp_dir_for_docker_mount(output_directory): {"bind": OUTPUT_MOUNT, "mode": "rw"},
                        **batch_mounts,
                    },
                    user=f"{os.getuid()}:{os.getgid()}",
                    network=proxy.network.name,
                    detach=True,
                )
                exit_code = container.wait().get("StatusCode")  # the output of the agent is in the agent log
                logs.append(f"===== batch {number}/{len(batches)} =====\n")
                logs.append(container.logs().decode("utf-8", errors="replace"))
                if exit_code != 0:
                    logging.warning(f"The review agent exited with code {exit_code} (batch {number}).")
                else:
                    print(f"Batch {number}/{len(batches)} finished.", flush=True)
            finally:
                if container is not None:
                    try:
                        container.remove(force=True)
                    except Exception:
                        pass

            if on_batch_done is not None:
                try:
                    on_batch_done(batch_directories[number - 1], output_directory)
                except Exception:
                    logging.exception(f"Processing the reviews of batch {number} failed.")
    finally:
        (output_directory / "agent-log.txt").write_text("\n".join(logs))
        proxy.stop()

    return output_directory


def _check_review(review: Any, run: dict) -> list[str]:
    """Returns a list of problems of the review of the run (empty if the review is valid)."""
    if not isinstance(review, dict):
        return ["the review is not a JSON object"]

    problems = []
    only_evaluations = bool(run.get("only_evaluations"))
    for check in [] if only_evaluations else CHECKS:
        value = review.get(check)
        if not isinstance(value, dict) or value.get("status") not in OK_STATUSES[check]:
            problems.append(f"'{check}' needs a 'status' of {sorted(OK_STATUSES[check])}")
        elif value["status"] not in ("ok", "unclear") and not value.get("evidence"):
            problems.append(f"'{check}' has status '{value['status']}' but no evidence")

    verdict = review.get("verdict")
    if verdict not in VERDICTS:
        problems.append(f"'verdict' must be one of {sorted(VERDICTS)}")

    checks = [] if only_evaluations else [review.get(c) for c in CHECKS]
    if verdict == "valid" and any(not isinstance(c, dict) or c.get("status") != "ok" for c in checks):
        problems.append("'verdict' is 'valid' but not all checks are 'ok'")

    tira_review = review.get("tira_review")
    if only_evaluations:
        tira_review = {}  # the run itself is already reviewed in TIRA
    elif not isinstance(tira_review, dict) or not str(tira_review.get("comment", "")).strip():
        problems.append("'tira_review' needs a non-empty 'comment'")
    elif any(not isinstance(tira_review.get(k), bool) for k in ("no_errors", "output_error", "software_error")):
        problems.append("'tira_review' needs boolean 'no_errors', 'output_error', and 'software_error'")
    elif tira_review["no_errors"] and (tira_review["output_error"] or tira_review["software_error"]):
        problems.append("'tira_review' has 'no_errors' together with an error flag")
    elif verdict == "invalid" and tira_review["no_errors"]:
        problems.append("'verdict' is 'invalid' but 'tira_review' has 'no_errors'")

    evaluations = review.get("evaluations")
    expected = {e["run_id"] for e in run.get("evaluations", [])}
    if not isinstance(evaluations, list):
        problems.append("'evaluations' must be a list")
    else:
        if not all(isinstance(e, dict) and isinstance(e.get("run_id"), str) for e in evaluations):
            problems.append("each of the 'evaluations' must be an object with a 'run_id'")
        else:
            ids = [e["run_id"] for e in evaluations]
            if len(ids) != len(set(ids)):
                problems.append("'evaluations' contains duplicate run ids")
            if expected - set(ids):
                problems.append(f"evaluations not reviewed: {sorted(expected - set(ids))}")
            if set(ids) - expected:
                problems.append(f"evaluations that are not in the manifest: {sorted(set(ids) - expected)}")

    return problems


def load_reviews(
    review_directory: Path, output_directory: Path, manifest_directory: Optional[Path] = None
) -> list[dict]:
    """Loads the review of each run in the manifest (of the review directory, or of the given manifest directory, e.g.,
    of a batch) from the output directory of the agent.
    Returns one entry per run: {run, review, problems}. 'review' is None if the file is missing or not parseable."""
    manifest = json.loads((Path(manifest_directory or review_directory) / "manifest.json").read_text())
    ret = []
    for run in manifest["runs"]:
        path = Path(output_directory) / "reviews" / run["dataset"] / run["team"] / f"{run['run_id']}.json"
        review: Any = None
        if not path.is_file():
            problems = [f"missing review file {path.relative_to(output_directory)}"]
        else:
            try:
                review = json.loads(path.read_text())
                problems = _check_review(review, run)
            except json.JSONDecodeError as e:
                problems = [f"invalid JSON: {e}"]

        ret.append({"run": run, "review": review, "problems": problems})

    return ret


def needs_human_attention(result: dict) -> bool:
    """Whether the agent flagged the review for a human, or found something suspicious."""
    review = result["review"]
    return isinstance(review, dict) and bool(
        review.get("needs_human_review")
        or review.get("verdict") == "needs_human_review"
        or any(isinstance(review.get(c), dict) and review[c].get("status") != "ok" for c in CHECKS)
    )


def upload_reviews(client: Any, results: list[dict]) -> list[dict]:
    """Uploads the reviews of all runs that are valid and do not need a human review to TIRA, together with generic
    reviews of their evaluations (runs with an evaluation that is not ok are left for a human). Returns the uploaded
    results."""
    uploaded = []
    for r in results:
        if r["problems"] or needs_human_attention(r):
            continue
        if any(e.get("status") != "ok" for e in r["review"]["evaluations"]):
            continue  # a problem with an evaluation needs a human
        run = r["run"]
        if not run.get("only_evaluations"):
            tira_review = r["review"]["tira_review"]
            client.review_run(
                run["run_id"],
                run["dataset"],
                run["team"],
                tira_review["no_errors"],
                tira_review["output_error"],
                tira_review["software_error"],
                tira_review["comment"],
            )
        for evaluation in r["review"]["evaluations"]:
            client.review_run(
                evaluation["run_id"],
                run["dataset"],
                run["team"],
                True,
                False,
                False,
                "Automatic review of the evaluation.",  # the agent's summary can contain scores, so it is not uploaded
            )
        uploaded.append(r)

    return uploaded


def format_summary(results: list[dict]) -> str:
    """A human-readable summary of the loaded reviews."""
    headers = ["dataset", "team", "run", "verdict", "output", "failure", "hacking", "leak", "evals"]
    rows = []
    for r in results:
        review, run = r["review"], r["run"]
        review = review if isinstance(review, dict) else {}

        def status(check):
            value = review.get(check)
            return value.get("status", "?") if isinstance(value, dict) else "-"

        evaluations = review.get("evaluations") if isinstance(review.get("evaluations"), list) else []
        bad = sum(1 for e in evaluations if isinstance(e, dict) and e.get("status") != "ok")
        rows.append(
            [run["dataset"], run["team"], run["run_id"], str(review.get("verdict", "MISSING"))]
            + [status(c) for c in CHECKS]
            + [f"{len(evaluations) - bad}/{len(evaluations)} ok"]
        )

    widths = [max(len(str(x)) for x in [h] + [row[i] for row in rows]) for i, h in enumerate(headers)]
    lines = ["  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip()]
    lines += ["  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip() for row in rows]

    counts = {v: 0 for v in sorted(VERDICTS)}
    for r in results:
        verdict = r["review"].get("verdict") if isinstance(r["review"], dict) else None
        if verdict in counts:
            counts[verdict] += 1
    invalid_files = [r for r in results if r["problems"]]
    lines += ["", f"Reviewed {len(results)} run(s): " + ", ".join(f"{v}: {c}" for v, c in counts.items())]

    attention = [r for r in results if needs_human_attention(r)]
    if attention:
        lines += ["", "Needs human attention:"]
        for r in attention:
            run = r["run"]
            comment = (r["review"].get("tira_review") or {}).get("comment", "")
            lines.append(f"  - {run['dataset']}/{run['team']}/{run['run_id']}: {shorten(comment)}")

    if invalid_files:
        lines += ["", "Problems with the reviews written by the agent:"]
        for r in invalid_files:
            run = r["run"]
            lines += [f"  - {run['dataset']}/{run['team']}/{run['run_id']}: {shorten(p)}" for p in r["problems"]]

    return "\n".join(lines)
