#!/bin/sh
# Minimal check of the LLM connection: no tools are needed to answer.
set -e
# Files created in the container must stay readable for the host user.
trap 'chmod -R a+rwX /tira-data/output 2>/dev/null || true' EXIT
export COPILOT_HOME=/tmp/copilot-home
cd /tira-data/output
PROMPT='How are you? Answer in one short sentence and do not use any tools.'
# Record the exact prompt so that the workflow keeps it with the result of this run.
printf '%s\n' "$PROMPT" > /tira-data/output/prompt.txt
copilot -p "$PROMPT" --no-ask-user --no-auto-update --stream off --no-color --log-dir /tira-data/output/copilot-logs
