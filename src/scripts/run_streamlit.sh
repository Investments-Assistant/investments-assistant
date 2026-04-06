#!/usr/bin/env bash
set -euo pipefail

# Simple helper to run the Streamlit frontend from the project root.
# Usage: ./scripts/run_streamlit.sh

cd "$(dirname "$0")/.."

# Prefer poetry if available
if command -v poetry >/dev/null 2>&1; then
  poetry run streamlit run app.py
else
  streamlit run app.py
fi
