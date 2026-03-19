"""Notebook utilities for running EDA stages and displaying outputs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO_MARKERS = [
    ("requirements.txt", "file"),
    ("configs/base.yaml", "file"),
    ("src", "dir"),
]


def find_repo_root() -> Path:
    """Walk upward from Path.cwd() until repo markers are found."""
    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if _is_repo_root(candidate):
            return candidate
    raise RuntimeError(
        "Could not find repo root. Expected requirements.txt, configs/base.yaml, and src/."
    )


def _is_repo_root(path: Path) -> bool:
    for relative, kind in REPO_MARKERS:
        candidate = path / relative
        if kind == "file" and not candidate.is_file():
            return False
        if kind == "dir" and not candidate.is_dir():
            return False
    return True


def run_stage(module_name: str, config_path: str) -> None:
    """Run EDA stage module via subprocess. Raises on non-zero exit."""
    repo_root = find_repo_root()
    config_abs = (repo_root / config_path).resolve()
    if not config_abs.is_file():
        raise FileNotFoundError(f"Config not found: {config_abs}")
    subprocess.run(
        [sys.executable, "-m", module_name, "--config", str(config_abs)],
        cwd=repo_root,
        check=True,
    )


def _resolve_path(path: str | Path) -> Path:
    """Resolve path relative to repo root if not absolute."""
    p = Path(path)
    if p.is_absolute():
        return p
    return find_repo_root() / p


def read_table(path: str | Path) -> pd.DataFrame:
    """Load parquet and return DataFrame."""
    return pd.read_parquet(_resolve_path(path))


def show_image(path: str | Path) -> None:
    """Display PNG inline in notebook."""
    from IPython.display import Image, display

    display(Image(filename=str(_resolve_path(path))))


def show_markdown(path: str | Path) -> None:
    """Read and render markdown inline in notebook."""
    from IPython.display import Markdown, display

    text = _resolve_path(path).read_text(encoding="utf-8")
    display(Markdown(text))
