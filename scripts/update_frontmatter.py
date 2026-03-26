"""
update_frontmatter.py — CLAUDE.md frontmatter validator and utility.

Usage:
    python scripts/update_frontmatter.py --list
    python scripts/update_frontmatter.py --check
    python scripts/update_frontmatter.py --bump <path/to/CLAUDE.md>
    python scripts/update_frontmatter.py --graph
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ── constants ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
REQUIRED_KEYS = {"id", "title", "version", "scope", "tags", "cross_dependencies", "toc"}
VALID_SCOPES = {"repo", "cowork", "src", "track", "scripts", "tests"}
REQUIRED_CROSS_DEP_KEYS = {"reads", "writes", "siblings"}
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


# ── helpers ────────────────────────────────────────────────────────────────────

def find_all_claude_mds() -> list[Path]:
    """Return all CLAUDE.md files under the repo root, sorted."""
    files: list[Path] = []

    def _onerror(_err: OSError) -> None:
        # Skip unreadable/corrupt directories instead of hard-failing the entire check.
        return

    for dirpath, dirnames, filenames in os.walk(REPO_ROOT, onerror=_onerror):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", "node_modules", ".next", ".venv", ".venv-wsl", ".venv-win", ".venv-linux"}
            and not d.startswith("__pycache__")
        ]
        if "CLAUDE.md" in filenames:
            files.append(Path(dirpath) / "CLAUDE.md")

    return sorted(files)


def extract_frontmatter(path: Path) -> tuple[dict | None, str]:
    """
    Parse YAML frontmatter from a CLAUDE.md file.
    Returns (parsed_dict_or_None, error_message_or_empty).
    """
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, "No YAML frontmatter block found (must start with '---')"
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    if not isinstance(data, dict):
        return None, "Frontmatter did not parse as a YAML mapping"
    return data, ""


def validate_frontmatter(path: Path, data: dict) -> list[str]:
    """Return a list of validation error strings (empty = valid)."""
    errors: list[str] = []

    # Required top-level keys
    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"Missing required key: '{key}'")

    # Scope value
    scope = data.get("scope")
    if scope and scope not in VALID_SCOPES:
        errors.append(f"Invalid scope '{scope}'. Must be one of: {sorted(VALID_SCOPES)}")

    # Tags must be a list with at least 2 items
    tags = data.get("tags", [])
    if not isinstance(tags, list):
        errors.append("'tags' must be a YAML list")
    elif len(tags) < 2:
        errors.append("'tags' must contain at least 2 entries")

    # cross_dependencies structure
    cross = data.get("cross_dependencies", {})
    if not isinstance(cross, dict):
        errors.append("'cross_dependencies' must be a YAML mapping")
    else:
        for subkey in REQUIRED_CROSS_DEP_KEYS:
            if subkey not in cross:
                errors.append(f"'cross_dependencies' is missing sub-key: '{subkey}'")
            elif not isinstance(cross[subkey], list):
                errors.append(f"'cross_dependencies.{subkey}' must be a YAML list")

    # toc must be a list of dicts with 'section' and 'anchor'
    toc = data.get("toc", [])
    if not isinstance(toc, list):
        errors.append("'toc' must be a YAML list")
    else:
        for i, entry in enumerate(toc):
            if not isinstance(entry, dict):
                errors.append(f"'toc[{i}]' must be a mapping with 'section' and 'anchor'")
            else:
                for field in ("section", "anchor"):
                    if field not in entry:
                        errors.append(f"'toc[{i}]' is missing field: '{field}'")

    # version must be YYYY-MM-DD
    version = data.get("version", "")
    if isinstance(version, str) and not re.match(r"^\d{4}-\d{2}-\d{2}$", version):
        errors.append(f"'version' must be YYYY-MM-DD, got: '{version}'")

    # id must be present and be a valid slug
    fid = data.get("id", "")
    if isinstance(fid, str) and not re.match(r"^[a-z][a-z0-9_]*$", fid):
        errors.append(f"'id' must be a snake_case slug, got: '{fid}'")

    return errors


# ── subcommands ────────────────────────────────────────────────────────────────

def cmd_list() -> int:
    """Print all CLAUDE.md files with id, scope, version."""
    files = find_all_claude_mds()
    if not files:
        print("No CLAUDE.md files found under repo root.")
        return 1

    header = f"{'ID':<30} {'SCOPE':<10} {'VERSION':<14} {'PATH'}"
    print(header)
    print("-" * len(header))

    ok = 0
    bad = 0
    seen_ids: dict[str, Path] = {}

    for path in files:
        rel = path.relative_to(REPO_ROOT)
        data, err = extract_frontmatter(path)
        if err or data is None:
            print(f"{'<NO FRONTMATTER>':<30} {'?':<10} {'?':<14} {rel}  [ERROR: {err}]")
            bad += 1
        else:
            fid = data.get("id", "<missing>")
            scope = data.get("scope", "<missing>")
            version = str(data.get("version", "<missing>"))

            # Detect duplicate ids
            dup_flag = ""
            if fid in seen_ids:
                dup_flag = f"  [DUPLICATE id with {seen_ids[fid].relative_to(REPO_ROOT)}]"
            else:
                seen_ids[fid] = path

            print(f"{str(fid):<30} {scope:<10} {version:<14} {rel}{dup_flag}")
            ok += 1

    print(f"\nTotal: {ok + bad} files  ({ok} valid frontmatter, {bad} errors)")
    return 0 if bad == 0 else 1


def cmd_check() -> int:
    """Validate all CLAUDE.md frontmatter. Exits non-zero on any failure."""
    files = find_all_claude_mds()
    if not files:
        print("No CLAUDE.md files found.")
        return 1

    all_ok = True
    seen_ids: dict[str, Path] = {}

    for path in files:
        rel = path.relative_to(REPO_ROOT)
        data, parse_err = extract_frontmatter(path)

        if parse_err or data is None:
            print(f"FAIL  {rel}")
            print(f"      {parse_err}")
            all_ok = False
            continue

        errors = validate_frontmatter(path, data)

        # Check duplicate id
        fid = data.get("id", "")
        if fid and fid in seen_ids:
            errors.append(
                f"Duplicate 'id' value '{fid}' also used in "
                f"{seen_ids[fid].relative_to(REPO_ROOT)}"
            )
        elif fid:
            seen_ids[fid] = path

        if errors:
            print(f"FAIL  {rel}")
            for err in errors:
                print(f"      - {err}")
            all_ok = False
        else:
            print(f"OK    {rel}")

    print()
    if all_ok:
        print("All CLAUDE.md files passed frontmatter validation.")
        return 0
    else:
        print("One or more CLAUDE.md files failed validation. See errors above.")
        return 1


def cmd_bump(target: str) -> int:
    """Update the 'version' field in one CLAUDE.md to today's date."""
    path = Path(target)
    if not path.is_absolute():
        path = REPO_ROOT / target
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    today = date.today().isoformat()

    new_text, count = re.subn(
        r'^(version:\s*")[^"]*(")',
        rf'\g<1>{today}\g<2>',
        text,
        flags=re.MULTILINE,
    )
    if count == 0:
        # Try unquoted version
        new_text, count = re.subn(
            r'^(version:\s*)[\d]{4}-[\d]{2}-[\d]{2}',
            rf'\g<1>"{today}"',
            text,
            flags=re.MULTILINE,
        )
    if count == 0:
        print(f"ERROR: Could not find 'version:' field in frontmatter of {path}", file=sys.stderr)
        return 1

    path.write_text(new_text, encoding="utf-8")
    print(f"Bumped version to {today} in {path.relative_to(REPO_ROOT)}")
    return 0


def cmd_graph() -> int:
    """Print a sibling dependency graph for all CLAUDE.md files."""
    files = find_all_claude_mds()
    id_to_path: dict[str, Path] = {}
    id_to_siblings: dict[str, list[str]] = {}
    parse_errors: list[str] = []

    for path in files:
        data, err = extract_frontmatter(path)
        if err or data is None:
            parse_errors.append(f"  {path.relative_to(REPO_ROOT)}: {err}")
            continue
        fid = str(data.get("id", "<missing>"))
        siblings = data.get("cross_dependencies", {}).get("siblings", []) or []
        id_to_path[fid] = path
        id_to_siblings[fid] = [str(s) for s in siblings]

    if parse_errors:
        print("WARNING: Some files had parse errors and are excluded from graph:")
        for e in parse_errors:
            print(e)
        print()

    print("CLAUDE.md Sibling Dependency Graph")
    print("===================================")
    print("(Each entry lists the siblings declared in its frontmatter)\n")

    for fid in sorted(id_to_siblings):
        siblings = id_to_siblings[fid]
        rel = id_to_path[fid].relative_to(REPO_ROOT)
        if siblings:
            sib_str = ", ".join(siblings)
        else:
            sib_str = "(none)"
        # Flag missing ids
        missing = [s for s in siblings if s not in id_to_siblings]
        missing_note = f"  ⚠ unknown ids: {missing}" if missing else ""
        print(f"  {fid:<30} → {sib_str}{missing_note}")

    print()
    print(f"Total CLAUDE.md files in graph: {len(id_to_siblings)}")
    return 0


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="CLAUDE.md frontmatter validator and utility.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List all CLAUDE.md files")
    group.add_argument("--check", action="store_true", help="Validate all frontmatter")
    group.add_argument("--bump", metavar="FILE", help="Bump version date in FILE")
    group.add_argument("--graph", action="store_true", help="Print sibling dependency graph")

    args = parser.parse_args()

    if args.list:
        return cmd_list()
    elif args.check:
        return cmd_check()
    elif args.bump:
        return cmd_bump(args.bump)
    elif args.graph:
        return cmd_graph()
    return 0


if __name__ == "__main__":
    sys.exit(main())
