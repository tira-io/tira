#!/bin/sh
# Minimal check of the devcontainer: is the Copilot CLI installed and are the task files mounted?
set -e
# Files created in the container must stay readable for the host user.
trap 'chmod -R a+rwX /tira-data/output 2>/dev/null || true' EXIT
echo "whoami: $(whoami)"; uname -a
copilot --version
ls -la /tira-data/input /tira-data/output /tira-agent
