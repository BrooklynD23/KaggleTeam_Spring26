"""GPU availability check for optional cudf-polars acceleration."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

_GPU_CHECK_SCRIPT = """
import json
import sys

result = {"available": False, "reason": None}

try:
    import polars as pl
except ImportError as e:
    result["reason"] = f"polars: {e}"
    print(json.dumps(result))
    sys.exit(0)

# cudf-polars registers the GPU engine with Polars when installed.
# Try a trivial collect(engine="gpu") - Polars falls back to CPU if GPU unavailable.
try:
    lf = pl.LazyFrame({"a": [1, 2, 3]})
    lf.collect(engine="gpu")
    result["available"] = True
except Exception as e:
    result["reason"] = str(e)

print(json.dumps(result))
"""


def check_gpu_available(venv_python: Path, repo_root: Path) -> bool:
    """Return True if cudf-polars GPU backend is installed and usable.

    Runs a subprocess in the venv to avoid importing heavy GPU libs in the
    launcher process. Polars requires cudf-polars-cu12 for engine='gpu'.
    """
    available, _ = get_gpu_status(venv_python, repo_root)
    return available


def get_gpu_status(venv_python: Path, repo_root: Path) -> tuple[bool, str | None]:
    """Return (available, reason) for GPU acceleration status."""
    proc = subprocess.run(
        [str(venv_python), "-c", _GPU_CHECK_SCRIPT],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip() or "Check script failed"
    try:
        data = json.loads(proc.stdout.strip() or "{}")
        return data.get("available", False), data.get("reason")
    except json.JSONDecodeError:
        return False, "Invalid check output"
