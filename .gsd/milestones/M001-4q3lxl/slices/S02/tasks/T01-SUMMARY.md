---
id: T01
parent: S02
milestone: M001-4q3lxl
provides:
  - Contract-first EDA export bundle generation from dispatcher metadata plus S01 evidence files
  - Tmp-repo regression coverage proving the packager does not depend on data/curated
key_files:
  - scripts/package_eda_exports.py
  - tests/test_package_eda_exports.py
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/tracks/track_d/manifest.json
key_decisions:
  - Recorded D013 to keep export truth dispatcher- and census-derived while copying markdown verbatim
patterns_established:
  - Validate required S01 inputs up front, then materialize root and per-track export manifests from the census instead of scraping markdown
observability_surfaces:
  - python scripts/package_eda_exports.py
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/tracks/track_d/manifest.json
  - outputs/exports/eda/manifest.csv
duration: ~45m
verification_result: passed
completed_at: 2026-03-21T22:47:00-07:00
blocker_discovered: false
---

# T01: Build the contract-first export bundle generator and regression test

**Added a dispatcher- and census-driven EDA export packager with tmp-repo contract coverage.**

## What Happened

I added `scripts/package_eda_exports.py` with a callable `generate_export_bundle(repo_root=...)` entrypoint and a CLI that writes `outputs/exports/eda/` from `scripts.pipeline_dispatcher.get_eda_summary_contract()`, `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, and the five final summary markdown files.

The implementation keeps bundle truth contract-first: it validates the required S01 inputs up front, copies the checklist and per-track summary markdowns verbatim, emits root `manifest.json` / `manifest.csv`, and writes per-track `summary.md`, `manifest.json`, and `artifacts.csv` files without touching `data/curated/`.

I also added `tests/test_package_eda_exports.py` using a `tmp_path` synthetic repo. The tests prove the packager can run from S01 evidence alone, preserves census statuses such as `repaired`, carries Track D's `blocked_by` dependency into the exported manifest, and fails with a path-specific error when a required S01 input is missing.

## Verification

Task-level verification passed: the focused pytest file is green, and the direct `generate_export_bundle(repo_root=Path('.'))` smoke check returned the expected root manifest and CSV paths.

I also ran the slice-level verification commands. The duplicate focused pytest check passed. The broader slice checks are still expected failures at this stage because T02/T03 have not yet added `outputs/exports/eda/EXPORT_CONTRACT.md` or the synthesized PNG files.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_package_eda_exports.py` | 0 | ✅ pass | 0.27s |
| 2 | `python - <<'PY'` smoke check importing `scripts.package_eda_exports` and asserting `manifest.json` / `manifest.csv` names | 0 | ✅ pass | 0.07s |
| 3 | `python -m pytest tests/test_package_eda_exports.py` | 0 | ✅ pass | 0.23s |
| 4 | `python scripts/package_eda_exports.py && test -f outputs/exports/eda/manifest.json && test -f outputs/exports/eda/manifest.csv && test -f outputs/exports/eda/EXPORT_CONTRACT.md && test -f outputs/exports/eda/figures/eda_overview.png && for track in track_a track_b track_c track_d track_e; do test -f outputs/exports/eda/figures/${track}_status_card.png && test -f outputs/exports/eda/tracks/${track}/summary.md && test -f outputs/exports/eda/tracks/${track}/manifest.json && test -f outputs/exports/eda/tracks/${track}/artifacts.csv; done` | 1 | ❌ fail | 0.07s |
| 5 | `python scripts/package_eda_exports.py && python - <<'PY'` forbidden-artifact and contract inspection | 1 | ❌ fail | 0.11s |

## Diagnostics

Run `python scripts/package_eda_exports.py` to rebuild the current bundle and print status totals plus per-track blocker state. Inspect `outputs/exports/eda/manifest.json` for root totals and emitted file counts, `outputs/exports/eda/manifest.csv` for the flattened artifact census, and `outputs/exports/eda/tracks/track_d/manifest.json` for the exported Track D blocker metadata.

## Deviations

None.

## Known Issues

The remaining slice-level checks are red because `EXPORT_CONTRACT.md` and the PNG status visuals belong to T02/T03 and are not implemented in this task yet.

## Files Created/Modified

- `scripts/package_eda_exports.py` — added the contract-first EDA export bundle generator and CLI.
- `tests/test_package_eda_exports.py` — added tmp-repo regression coverage for bundle layout, status preservation, and missing-input failures.
- `outputs/exports/eda/manifest.json` — generated the root machine-readable export manifest in the real worktree.
- `outputs/exports/eda/manifest.csv` — generated the root tabular export manifest with per-track export references.
- `outputs/exports/eda/eda_command_checklist.md` — copied the S01 checklist markdown into the export bundle.
- `outputs/exports/eda/tracks/track_d/manifest.json` — generated the per-track export manifest carrying Track D blocker metadata.
- `.gsd/milestones/M001-4q3lxl/slices/S02/S02-PLAN.md` — marked T01 complete.
