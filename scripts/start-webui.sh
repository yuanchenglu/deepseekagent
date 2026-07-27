#!/bin/bash
# Compatibility wrapper. Lifecycle ownership lives in the DeepAgent CLI.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -x "$PROJECT_DIR/venv/bin/python" ]; then
    exec "$PROJECT_DIR/venv/bin/python" -m hermes_cli.main webui "$@"
fi

exec deepagent webui "$@"
