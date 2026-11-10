#!/bin/sh
# Runs the Copilot CLI (BYOK) as coding agent. The LLM is configured via COPILOT_PROVIDER_TYPE, COPILOT_MODEL,
# COPILOT_PROVIDER_BASE_URL, and COPILOT_PROVIDER_API_KEY that are forwarded into the devcontainer.
set -e
# Files created in the container must stay readable for the host user.
trap 'chmod -R a+rwX /tira-data/output 2>/dev/null || true' EXIT
export COPILOT_HOME=/tmp/copilot-home
cd /tira-data/output
# The skill is part of the prompt, as the model otherwise ignores the file.
PROMPT="$(cat /tira-agent/skill.md)


$(cat /tira-data/input/STAGE.md)

Now follow this skill to solve the task described in /tira-data/input/README.md."

# Feedback of the workflow (a rejected solution or the review of an evaluation) is mounted to /tira-data/input/feedback.
# The solution of the previous run is still in /tira-data/output.
if [ -f /tira-data/input/feedback/feedback.md ]; then
    PROMPT="$PROMPT

$(cat /tira-data/input/feedback/feedback.md)"
fi

# Record the exact prompt so that the workflow keeps it with the result of this run.
printf '%s\n' "$PROMPT" > /tira-data/output/prompt.txt

# The agent is stopped after AGENT_TIMEOUT_SECONDS (default 10 minutes) so that it can not run forever.
timeout "${AGENT_TIMEOUT_SECONDS:-600}" copilot -p "$PROMPT" \
    --allow-all-tools --allow-all-paths --no-ask-user --no-auto-update --stream off --no-color --log-dir /tira-data/output/copilot-logs
