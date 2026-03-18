"""Configure Git to use the repo-managed hook directory."""

from __future__ import annotations

import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    print("Configured git hooks path: .githooks")


if __name__ == "__main__":
    main()