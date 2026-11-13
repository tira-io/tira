#!/bin/sh
# Minimal check of tool calling: the agent has to call a tool to answer.
set -e
# Files created in the container must stay readable for the host user.
trap 'chmod -R a+rwX /tira-data/output 2>/dev/null || true' EXIT
export COPILOT_HOME=/tmp/copilot-home
cd /tira-data/output
PROMPT='Run the command ls -la /tira-data/input with your shell tool and report the files you see.'
# Record the exact prompt so that the workflow keeps it with the result of this run.
printf '%s\n' "$PROMPT" > /tira-data/output/prompt.txt
copilot -p "$PROMPT" \
    --allow-all-tools --allow-all-paths --no-ask-user --no-auto-update --stream off --no-color --log-dir /tira-data/output/copilot-logs
