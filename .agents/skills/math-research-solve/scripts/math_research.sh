#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python 3.12 or newer was not found. No installation was attempted." >&2
  exit 10
fi
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUTF8=1
exec "$PYTHON" -B "$SCRIPT_DIR/math_research_platform.py" "$@"
