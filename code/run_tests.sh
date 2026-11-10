#!/usr/bin/env bash
# Run the unittest suite with the project's own venv (plain python3 lacks deps).
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/python -m unittest discover -s tests -t . "$@"
