---
estimated_steps: 4
estimated_files: 6
skills_used:
  - coding-standards
  - tdd-workflow
  - test
  - verification-loop
---

# T01: Build the contract-first export bundle generator and regression test

**Slice:** S02 — Export contract and evidence packaging
**Milestone:** M001-4q3lxl

## Description

Create the first real export-bundle implementation around a tmp-repo contract test, not around ad hoc copies from the live worktree. The task should prove that S02 can derive a downstream bundle from the dispatcher contract plus S01 evidence files alone, preserving honest `existing` / `missing` semantics and Track D's blocker state without requiring curated parquet.

## Steps

1. Add `tests/test_package_eda_exports.py` using the same `tmp_path` style as `tests/test_eda_artifact_census_report.py`, with synthetic S01 inputs for the census CSV, checklist markdown, and final Track A–E summary markdowns.
2. Implement `scripts/package_eda_exports.py` with a `generate_export_bundle(repo_root=...)` entrypoint, dataclasses/helpers for loading the dispatcher contract and census rows, and deterministic writers for root/per-track JSON, CSV, and markdown outputs under `outputs/exports/eda/`.
3. Keep bundle truth dispatcher-derived and census-derived: copy summary markdowns verbatim into per-track export folders, carry Track D's `blocked_by` dependency into exported manifests, and do not infer artifact presence by scraping summary markdown tables.
4. Run the focused pytest file until it proves the packager works against the synthetic repo root without touching `data/curated/`.

## Must-Haves

- [ ] The implementation exposes a callable `generate_export_bundle(repo_root=...)` surface that can run against a temporary repo root in tests and the real worktree from the CLI.
- [ ] Root outputs include machine-readable bundle metadata (`manifest.json`, `manifest.csv`) and per-track folders include copied `summary.md`, `manifest.json`, and `artifacts.csv` files.
- [ ] Exported manifests preserve census status semantics and Track D's `track_a_s5_candidate_splits.parquet` blocker instead of inventing materialized evidence.

## Verification

- `python -m pytest tests/test_package_eda_exports.py`
- `python - <<'PY'
from pathlib import Path
from scripts import package_eda_exports as exports
bundle = exports.generate_export_bundle(repo_root=Path('.'))
assert bundle.root_manifest.name == 'manifest.json'
assert bundle.root_csv.name == 'manifest.csv'
PY`

## Observability Impact

- Signals added/changed: root/per-track manifest records now expose status totals and `blocked_by` fields for exported evidence.
- How a future agent inspects this: read `outputs/exports/eda/manifest.json` and `outputs/exports/eda/tracks/track_d/manifest.json`, or run `python -m pytest tests/test_package_eda_exports.py` against a tmp repo.
- Failure state exposed: missing S01 source files and contract drift fail with path-specific errors instead of producing a partially silent bundle.

## Inputs

- `scripts/pipeline_dispatcher.py` — authoritative Track A–E summary contract
- `scripts/report_eda_completeness.py` — existing repo-root-injected reporting pattern to mirror
- `outputs/tables/eda_artifact_census.csv` — machine-readable artifact status truth
- `outputs/tables/eda_command_checklist.md` — canonical launcher order and Track D blocker note
- `outputs/tables/track_d_s9_eda_summary.md` — representative per-track summary file whose blocker language must be copied, not re-derived

## Expected Output

- `scripts/package_eda_exports.py` — new export-bundle generator with repo-root injection and deterministic writers
- `tests/test_package_eda_exports.py` — tmp-repo contract coverage for the new bundle generator
- `outputs/exports/eda/manifest.json` — root machine-readable export manifest
- `outputs/exports/eda/manifest.csv` — root tabular export manifest
- `outputs/exports/eda/tracks/track_a/manifest.json` — representative per-track machine-readable manifest
- `outputs/exports/eda/tracks/track_d/manifest.json` — representative per-track manifest carrying Track D blocker metadata
