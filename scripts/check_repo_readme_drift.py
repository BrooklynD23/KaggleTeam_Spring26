"""Detect drift for the repository README.

The root README summarizes repository structure, implemented tracks, run
commands, data flow, and planning status. This script hashes a curated set of
repo files that can invalidate those claims and reports when README.md should
be reviewed.

Usage:
    # Check for README drift (exits 1 if drift is detected)
    python scripts/check_repo_readme_drift.py --check

    # Update the baseline after refreshing README.md
    python scripts/check_repo_readme_drift.py --update

    # Print a human-readable report and always exit 0
    python scripts/check_repo_readme_drift.py --report
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from pathlib import Path
from typing import NamedTuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_FILE = PROJECT_ROOT / "README.md"
STATE_FILE = PROJECT_ROOT / ".readme_state.json"
IGNORED_STRUCTURE_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv-wsl",
    ".venv-win",
    ".venv-linux",
    "__pycache__",
}

# Maps tracked source paths or glob patterns to the README sections most likely
# impacted when those files change.
DEPENDENCY_MAP: dict[str, list[str]] = {
    ".": ["Project Structure", "Repository Status"],
    ".githooks": ["How to Run"],
    "requirements.txt": ["Repository Status", "How to Run"],
    "run_pipeline.sh": ["How to Run"],
    "run_pipeline.ps1": ["How to Run"],
    "scripts/check_repo_readme_drift.py": ["How to Run"],
    "scripts/enable_git_hooks.py": ["How to Run"],
    "scripts/pipeline_dispatcher.py": ["Repository Status", "How to Run"],
    "scripts/run_pipeline.py": ["Repository Status", "How to Run"],
    "scripts/run_shared.sh": ["How to Run"],
    "scripts/run_track_a.sh": ["How to Run"],
    "scripts/run_track_b.sh": ["How to Run"],
    "configs/*.yaml": ["Project Structure", "Deliverables", "How to Run"],
    "src/common/*.py": ["Repository Status", "Project Structure"],
    "src/ingest/*.py": [
        "Repository Status",
        "Data Context Before Processing",
        "Deliverables",
    ],
    "src/validate/*.py": ["Repository Status", "Deliverables"],
    "src/curate/*.py": [
        "Repository Status",
        "Data Context Before Processing",
        "Deliverables",
    ],
    "src/eda/track_a/*.py": [
        "Repository Status",
        "Progress Tracking",
        "Track Folder Check",
        "Deliverables",
    ],
    "src/eda/track_b/*.py": [
        "Repository Status",
        "Progress Tracking",
        "Track Folder Check",
        "Deliverables",
    ],
    "src/eda": [
        "Repository Status",
        "Progress Tracking",
        "Track Folder Check",
        "Track Index",
    ],
    "src/eda/track_c/*.py": ["Repository Status", "Progress Tracking", "Track Index"],
    "src/eda/track_d/*.py": ["Repository Status", "Progress Tracking", "Track Index"],
    "src/eda/track_e/*.py": ["Repository Status", "Progress Tracking", "Track Index"],
    "tests/*.py": ["Repository Status"],
    "CoWork Planning/yelp_project/*.md": [
        "Core Planning Documents",
        "Progress Tracking",
        "Track Index",
    ],
    "CoWork Planning/yelp_project/README.md": ["Core Planning Documents"],
    "CoWork Planning/yelp_project/01_PRD_Yelp_Open_Dataset.md": [
        "Track Index",
        "Core Planning Documents",
    ],
    "CoWork Planning/yelp_project/07_Implementation_Plan_Ingestion_TrackA_TrackB.md": [
        "Progress Tracking",
        "Data Context Before Processing",
        "Core Planning Documents",
    ],
    "CoWork Planning/yelp_project/08_PM_Adversarial_Review_Implementation_Plan.md": [
        "Progress Tracking",
        "Core Planning Documents",
    ],
    "CoWork Planning/yelp_project/09_Resolution_TrackA_TrackB_Implementation_Plan.md": [
        "Progress Tracking",
        "Core Planning Documents",
    ],
    "CoWork Planning/yelp_project/track_*/README.md": [
        "Track Folder Check",
        "Track Index",
    ],
    "CoWork Planning/yelp_project/track_*/AGENTS.md": ["Track Folder Check"],
    "CoWork Planning/yelp_project/track_*/CLAUDE.md": ["Track Folder Check"],
}


class DriftResult(NamedTuple):
    changed_sources: list[str]
    new_sources: list[str]
    missing_sources: list[str]
    affected_sections: list[str]


def _normalize_path(relative_path: Path | str) -> str:
    if isinstance(relative_path, Path):
        return relative_path.as_posix()
    return str(relative_path).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_directory(path: Path) -> str:
    digest = hashlib.sha256()
    for entry in sorted(path.iterdir(), key=lambda item: item.name):
        if entry.name in IGNORED_STRUCTURE_NAMES or entry.name == STATE_FILE.name:
            continue
        suffix = "/" if entry.is_dir() else ""
        digest.update(f"{entry.name}{suffix}\n".encode("utf-8"))
    return digest.hexdigest()


def _hash_source(path: Path) -> str:
    if path.is_dir():
        return _hash_directory(path)
    return _sha256(path)


def _is_glob_pattern(pattern: str) -> bool:
    return any(token in pattern for token in "*?[]")


def _resolve_sources() -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for pattern in DEPENDENCY_MAP:
        if not _is_glob_pattern(pattern):
            absolute = PROJECT_ROOT / pattern
            resolved[_normalize_path(pattern)] = absolute
            continue

        matches = list(PROJECT_ROOT.glob(pattern))
        if matches:
            for match in matches:
                relative = _normalize_path(match.relative_to(PROJECT_ROOT))
                resolved[relative] = match
            continue

        absolute = PROJECT_ROOT / pattern
        resolved[_normalize_path(pattern)] = absolute

    return resolved


def _load_state() -> dict[str, str]:
    if not STATE_FILE.is_file():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def _save_state(hashes: dict[str, str]) -> None:
    STATE_FILE.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")


def _match_pattern(relative_path: str, pattern: str) -> bool:
    return fnmatch.fnmatch(relative_path, _normalize_path(pattern))


def _affected_sections(changed_source: str) -> list[str]:
    sections: set[str] = set()
    for pattern, mapped_sections in DEPENDENCY_MAP.items():
        if _match_pattern(changed_source, pattern):
            sections.update(mapped_sections)
    return sorted(sections)


def detect_drift() -> DriftResult:
    previous_state = _load_state()
    resolved_sources = _resolve_sources()

    changed_sources: list[str] = []
    new_sources: list[str] = []
    missing_sources: list[str] = []
    affected_sections: set[str] = set()

    for relative_path, absolute_path in resolved_sources.items():
        if not absolute_path.exists():
            if relative_path in previous_state:
                missing_sources.append(relative_path)
                affected_sections.update(_affected_sections(relative_path))
            continue

        current_hash = _hash_source(absolute_path)
        old_hash = previous_state.get(relative_path)
        if old_hash is None:
            new_sources.append(relative_path)
            affected_sections.update(_affected_sections(relative_path))
        elif old_hash != current_hash:
            changed_sources.append(relative_path)
            affected_sections.update(_affected_sections(relative_path))

    return DriftResult(
        changed_sources=sorted(changed_sources),
        new_sources=sorted(new_sources),
        missing_sources=sorted(missing_sources),
        affected_sections=sorted(affected_sections),
    )


def update_state() -> dict[str, str]:
    resolved_sources = _resolve_sources()
    hashes: dict[str, str] = {}
    for relative_path, absolute_path in resolved_sources.items():
        if absolute_path.exists():
            hashes[relative_path] = _hash_source(absolute_path)
    _save_state(hashes)
    return hashes


def _print_report(result: DriftResult) -> None:
    has_drift = bool(result.changed_sources or result.new_sources or result.missing_sources)
    if not has_drift:
        print("OK  No repo README drift detected.")
        return

    print("README DRIFT DETECTED\n")
    print(f"Target README: {README_FILE.relative_to(PROJECT_ROOT).as_posix()}\n")

    if result.changed_sources:
        print("Changed tracked files:")
        for item in result.changed_sources:
            print(f"  ~ {item}")

    if result.new_sources:
        print("New tracked files:")
        for item in result.new_sources:
            print(f"  + {item}")

    if result.missing_sources:
        print("Missing tracked files:")
        for item in result.missing_sources:
            print(f"  - {item}")

    if result.affected_sections:
        print("\nREADME sections to review:")
        for section in result.affected_sections:
            print(f"  * {section}")

    print(
        "\nFix: update README.md if needed, then refresh the baseline with:\n"
        "  python scripts/check_repo_readme_drift.py --update"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check for repository README drift.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if README drift is detected.",
    )
    command_group.add_argument(
        "--update",
        action="store_true",
        help="Record the current repo state as the README baseline.",
    )
    command_group.add_argument(
        "--report",
        action="store_true",
        help="Print a drift report and exit 0 regardless.",
    )
    args = parser.parse_args()

    if args.update:
        hashes = update_state()
        print(f"State updated: {len(hashes)} tracked files recorded in {STATE_FILE.name}")
        raise SystemExit(0)

    result = detect_drift()
    _print_report(result)

    if args.check:
        has_drift = bool(result.changed_sources or result.new_sources or result.missing_sources)
        raise SystemExit(1 if has_drift else 0)

    raise SystemExit(0)


if __name__ == "__main__":
    main()
