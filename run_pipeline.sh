#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="${ROOT_DIR}/scripts/run_pipeline.py"

if [[ ! -f "$LAUNCHER" ]]; then
  printf 'Error: launcher not found: %s\n' "$LAUNCHER" >&2
  exit 1
fi

if [[ -n "${VIRTUAL_ENV:-}" ]] && command -v python >/dev/null 2>&1; then
  PYTHON=python
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  printf 'Error: python3 or python not found in PATH\n' >&2
  exit 1
fi

exec "$PYTHON" "$LAUNCHER" "$@"
