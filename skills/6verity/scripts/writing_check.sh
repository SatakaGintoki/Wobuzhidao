#!/usr/bin/env bash
# Optional compatibility entry; PowerShell can run writing_check.py directly.
set -eu
if [ -n "${PYTHON_BIN:-}" ]; then
  checker_python="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
  checker_python="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  checker_python="$(command -v python)"
else
  echo "ERROR: Python not found; run writing_check.py with an available interpreter." >&2
  exit 2
fi
exec "$checker_python" "$(dirname "$0")/writing_check.py" "$@"
