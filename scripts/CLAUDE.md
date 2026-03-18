---
id: scripts
title: scripts/ — Pipeline Entry Points and Utilities
version: "2026-03-18"
scope: scripts
tags: [scripts, cli, pipeline-dispatcher, drift-check, frontmatter, git-hooks]

cross_dependencies:
  reads:
    - configs/base.yaml
    - configs/track_a.yaml
    - configs/track_b.yaml
    - .readme_state.json
    - .docs_state.json
  writes:
    - outputs/logs/
    - README.md
  siblings: [root, src]

toc:
  - section: "What Is In Here"
    anchor: "#what-is-in-here"
  - section: "Primary Entrypoints"
    anchor: "#primary-entrypoints"
  - section: "Utility Scripts"
    anchor: "#utility-scripts"
  - section: "Git Hook Integration"
    anchor: "#git-hook-integration"
---

# scripts/ — Pipeline Entry Points and Utilities

## What Is In Here

All CLI entry points and developer utility scripts. Agent code should **never** be added here — utilities only.

## Primary Entrypoints

| Script | Purpose |
|---|---|
| `run_pipeline.py` | Canonical cross-platform launcher: interactive dashboard, runtime-matched venv, approach selection |
| `pipeline_dispatcher.py` | Pure execution engine: runs stages given `--approach` (invoked by the launcher) |

```bash
# Canonical launcher (interactive or explicit)
python scripts/run_pipeline.py
python scripts/run_pipeline.py --approach shared
python scripts/run_pipeline.py --approach track_a
python scripts/run_pipeline.py --help
```

OS-specific wrappers delegate to the launcher:

```bash
./run_pipeline.sh
./run_pipeline.sh shared
```

```powershell
.\run_pipeline.ps1
.\run_pipeline.ps1 track_a
```

Runtime-matched virtual environments: `.venv-wsl`, `.venv-win`, `.venv-linux`. Do not reuse one venv across Windows and WSL.

## Utility Scripts

| Script | Purpose |
|---|---|
| `check_repo_readme_drift.py` | Detects when `README.md` is out of sync with repo state |
| `check_docs_drift.py` | Detects doc drift in the intern docs folder |
| `update_frontmatter.py` | Validates, lists, and bumps CLAUDE.md frontmatter |
| `enable_git_hooks.py` | Points Git at the repo-managed `.githooks/` directory |

### update_frontmatter.py

```bash
python scripts/update_frontmatter.py --list     # list all CLAUDE.md files
python scripts/update_frontmatter.py --check    # validate all frontmatter (CI gate)
python scripts/update_frontmatter.py --bump src/ingest/CLAUDE.md
python scripts/update_frontmatter.py --graph    # print sibling dependency tree
```

## Git Hook Integration

```bash
python scripts/enable_git_hooks.py
```

Registers `.githooks/pre-commit`, which runs:
1. `check_repo_readme_drift.py --check`
2. `update_frontmatter.py --check`

Both must pass for a commit to succeed.
