#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --disable-pip-version-check -r backend/requirements.txt
printf '\nZH-1 is starting at http://127.0.0.1:8420\n'
( sleep 2; command -v xdg-open >/dev/null && xdg-open http://127.0.0.1:8420 >/dev/null 2>&1 || true ) &
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8420
