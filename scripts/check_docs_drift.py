"""Detect documentation drift for intern docs.

Compares SHA-256 hashes of tracked source files against a stored state file.
Reports which intern docs may be stale and optionally blocks commits.

Usage:
    # Check for drift (exits 1 if stale docs found):
    python scripts/check_docs_drift.py --check

    # Update stored state after docs are updated:
    python scripts/check_docs_drift.py --update

    # Print a human-readable drift report:
    python scripts/check_docs_drift.py --report
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_ROOT / ".docs_state.json"

# Maps source file paths (relative to PROJECT_ROOT) to the intern doc files
# that cover them.  Glob patterns are supported for source paths.
DEPENDENCY_MAP: dict[str, list[str]] = {
    # Ingestion
    "src/ingest/load_yelp_json.py": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/code/ingest_load_yelp_json.md",
    ],
    "src/ingest/validate_json_structure.py": [
        "CoWork Planning/yelp_project/docs/intern/code/ingest_load_yelp_json.md",
    ],
    # Validation
    "src/validate/schema_checks.py": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/code/validate_schema_checks.md",
    ],
    # Curation
    "src/curate/build_review_fact.py": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/code/curate_build_review_fact.md",
    ],
    # Track A EDA (glob pattern — matches any .py in track_a)
    "src/eda/track_a/*.py": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/workflows/track_a_pipeline.md",
    ],
    # Track B EDA
    "src/eda/track_b/*.py": [
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/workflows/track_b_pipeline.md",
    ],
    # Common
    "src/common/config.py": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
    ],
    # Configs
    "configs/base.yaml": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/config/base_yaml.md",
    ],
    "configs/track_a.yaml": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/config/track_a_yaml.md",
    ],
    "configs/track_b.yaml": [
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/config/track_b_yaml.md",
    ],
    # Run scripts
    "run_pipeline.sh": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/workflows/running_the_pipeline.md",
    ],
    "run_pipeline.ps1": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/workflows/running_the_pipeline.md",
    ],
    "scripts/run_pipeline.py": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
        "CoWork Planning/yelp_project/docs/intern/workflows/running_the_pipeline.md",
    ],
    "scripts/pipeline_dispatcher.py": [
        "CoWork Planning/yelp_project/docs/intern/workflows/running_the_pipeline.md",
    ],
    # Planning docs — changes here may require decision records
    "CoWork Planning/yelp_project/track_a/CLAUDE.md": [
        "CoWork Planning/yelp_project/docs/intern/track_a_explained.md",
    ],
    "CoWork Planning/yelp_project/track_b/CLAUDE.md": [
        "CoWork Planning/yelp_project/docs/intern/track_b_explained.md",
    ],
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


class DriftResult(NamedTuple):
    changed_sources: list[str]          # source files whose hash changed
    stale_docs: list[str]               # doc files that need updating
    new_sources: list[str]              # tracked sources that aren't in state yet
    missing_sources: list[str]          # sources that disappeared


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_sources() -> dict[str, Path]:
    """Expand glob patterns in DEPENDENCY_MAP keys into concrete file paths.

    Returns a mapping of canonical (relative) source path → absolute Path.
    """
    resolved: dict[str, Path] = {}
    for pattern in DEPENDENCY_MAP:
        matches = list(PROJECT_ROOT.glob(pattern))
        if matches:
            for match in matches:
                key = str(match.relative_to(PROJECT_ROOT))
                resolved[key] = match
        else:
            # Non-glob path that doesn't exist yet — still track it
            abs_path = PROJECT_ROOT / pattern
            resolved[pattern] = abs_path
    return resolved


def _load_state() -> dict[str, str]:
    """Load previously recorded hashes from STATE_FILE."""
    if STATE_FILE.is_file():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_state(hashes: dict[str, str]) -> None:
    STATE_FILE.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")


def _affected_docs(changed_source: str) -> list[str]:
    """Return doc paths affected by a changed source file.

    Matches both exact keys and the original glob pattern that expanded to
    this source path.
    """
    docs: set[str] = set()

    # Direct match
    if changed_source in DEPENDENCY_MAP:
        docs.update(DEPENDENCY_MAP[changed_source])

    # Match via glob pattern (the source was expanded from a glob)
    for pattern, doc_list in DEPENDENCY_MAP.items():
        if "*" in pattern or "?" in pattern:
            abs_source = PROJECT_ROOT / changed_source
            if abs_source.match(pattern) or abs_source in PROJECT_ROOT.glob(pattern):
                docs.update(doc_list)

    return sorted(docs)


def detect_drift() -> DriftResult:
    """Compare current file hashes against stored state."""
    old_state = _load_state()
    resolved = _resolve_sources()

    changed: list[str] = []
    new: list[str] = []
    missing: list[str] = []
    stale_docs: set[str] = set()

    for rel_path, abs_path in resolved.items():
        if not abs_path.is_file():
            if rel_path in old_state:
                missing.append(rel_path)
                stale_docs.update(_affected_docs(rel_path))
            # File doesn't exist and wasn't tracked — ignore
            continue

        current_hash = _sha256(abs_path)
        if rel_path not in old_state:
            new.append(rel_path)
            stale_docs.update(_affected_docs(rel_path))
        elif old_state[rel_path] != current_hash:
            changed.append(rel_path)
            stale_docs.update(_affected_docs(rel_path))

    return DriftResult(
        changed_sources=sorted(changed),
        stale_docs=sorted(stale_docs),
        new_sources=sorted(new),
        missing_sources=sorted(missing),
    )


def update_state() -> dict[str, str]:
    """Hash all current source files and write to STATE_FILE."""
    resolved = _resolve_sources()
    hashes: dict[str, str] = {}
    for rel_path, abs_path in resolved.items():
        if abs_path.is_file():
            hashes[rel_path] = _sha256(abs_path)
    _save_state(hashes)
    return hashes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_report(result: DriftResult) -> None:
    any_drift = result.changed_sources or result.new_sources or result.missing_sources

    if not any_drift:
        print("OK  No documentation drift detected.")
        return

    print("DRIFT DETECTED — The following intern docs may be stale:\n")

    if result.changed_sources:
        print("  Changed source files:")
        for f in result.changed_sources:
            print(f"    ~ {f}")

    if result.new_sources:
        print("  New source files (not yet in state):")
        for f in result.new_sources:
            print(f"    + {f}")

    if result.missing_sources:
        print("  Deleted source files:")
        for f in result.missing_sources:
            print(f"    - {f}")

    if result.stale_docs:
        print("\n  Docs that need updating:")
        for doc in result.stale_docs:
            exists = (PROJECT_ROOT / doc).is_file()
            status = "exists" if exists else "MISSING"
            print(f"    [{status}] {doc}")

    print(
        "\nFix: Update the docs above, then run:\n"
        "  python scripts/check_docs_drift.py --update\n"
        "\nOr re-run the intern-docs agent:\n"
        "  claude --agent intern-docs"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check for intern documentation drift.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if stale docs are found (for use in git hooks).",
    )
    group.add_argument(
        "--update",
        action="store_true",
        help="Record current file hashes as the new baseline.",
    )
    group.add_argument(
        "--report",
        action="store_true",
        help="Print a drift report and exit 0 regardless.",
    )
    args = parser.parse_args()

    if args.update:
        hashes = update_state()
        print(f"State updated: {len(hashes)} source files tracked in {STATE_FILE.name}")
        sys.exit(0)

    result = detect_drift()
    _print_report(result)

    if args.check:
        has_drift = bool(result.changed_sources or result.new_sources or result.missing_sources)
        sys.exit(1 if has_drift else 0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
