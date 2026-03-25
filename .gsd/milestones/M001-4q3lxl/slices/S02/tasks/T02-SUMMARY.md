---
id: T02
parent: S02
milestone: M001-4q3lxl
provides:
  - Governance-safe EDA export packaging with an explicit source allowlist and forbidden-artifact exclusion enforcement
  - Generated `EXPORT_CONTRACT.md` plus metadata-only Track E validity-log summaries for downstream inspection
key_files:
  - scripts/package_eda_exports.py
  - tests/test_package_eda_exports.py
  - outputs/exports/eda/EXPORT_CONTRACT.md
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/tracks/track_e/manifest.json
key_decisions:
  - Recorded D014 to carry Track E validity-log evidence forward as manifest metadata instead of copying raw `.log` files into the bundle
patterns_established:
  - Rebuild `outputs/exports/eda/` from scratch on each run so stale forbidden artifacts cannot survive governance checks
observability_surfaces:
  - python scripts/package_eda_exports.py
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/EXPORT_CONTRACT.md
  - outputs/exports/eda/tracks/track_e/manifest.json
  - outputs/exports/eda/tracks/track_d/manifest.json
duration: ~1h 5m
verification_result: passed
completed_at: 2026-03-21T22:54:17-07:00
blocker_discovered: false
---

# T02: Enforce governance-safe packaging rules and publish the export contract

**Added governance-enforced EDA export packaging with a generated contract and metadata-only validity-log summaries.**

## What Happened

I updated `scripts/package_eda_exports.py` so the bundle now enforces a real allowlist boundary instead of relying on operator discipline. The packager only copies the S01 checklist plus the five final summary markdown files, rejects non-allowlisted copies, wipes `outputs/exports/eda/` before each rebuild, and fails if a `.parquet`, `.ndjson`, or `.log` file appears anywhere inside the bundle.

I also added generated `outputs/exports/eda/EXPORT_CONTRACT.md`, documenting the bundle layout, per-format expectations, `existing` / `missing` / `repaired` semantics, Track D’s blocker rule, and the internal-only / aggregate-safe / no-raw-review-text governance boundary.

For Track E, I preserved the validity-scan signal without copying the raw log: the packager now reads `outputs/logs/track_e_s9_validity_scan.log`, summarizes it into manifest metadata, and exposes that metadata in both the root manifest and `outputs/exports/eda/tracks/track_e/manifest.json`.

I expanded `tests/test_package_eda_exports.py` to cover the new contract file, governance metadata, stale forbidden-file cleanup, metadata-only validity-log handling, and path-specific failure when the validity log is marked existing in the census but missing on disk.

I also fixed the flagged observability gap in `.gsd/milestones/M001-4q3lxl/slices/S02/tasks/T02-PLAN.md` by adding an `## Observability Impact` section before proceeding.

## Verification

I ran the focused pytest file and the task-level packaging command with explicit forbidden-artifact and contract assertions; both passed.

I then ran the slice-level checks. The forbidden-artifact / Track D blocker inspection passed, while the broader file-presence command still fails as expected because T03 has not yet added the synthesized PNG figures (`outputs/exports/eda/figures/eda_overview.png` and per-track status cards).

I also inspected the generated manifests directly to confirm the new observability surfaces are present: the root manifest now carries `governance.forbidden_source_suffixes`, `governance.allowlisted_source_copies`, `governance.forbidden_source_status_totals`, and the metadata-only Track E validity summary; Track E’s per-track manifest exposes the same summary under `metadata_summaries`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_package_eda_exports.py` | 0 | ✅ pass | 0.25s |
| 2 | `python scripts/package_eda_exports.py && python - <<'PY' ...` (forbidden suffix scan + `EXPORT_CONTRACT.md` checks for `aggregate-safe`, `internal`, and `raw review text`) | 0 | ✅ pass | 0.08s |
| 3 | `python scripts/package_eda_exports.py && test -f outputs/exports/eda/manifest.json && test -f outputs/exports/eda/manifest.csv && test -f outputs/exports/eda/EXPORT_CONTRACT.md && test -f outputs/exports/eda/figures/eda_overview.png && for track in track_a track_b track_c track_d track_e; do test -f outputs/exports/eda/figures/${track}_status_card.png && test -f outputs/exports/eda/tracks/${track}/summary.md && test -f outputs/exports/eda/tracks/${track}/manifest.json && test -f outputs/exports/eda/tracks/${track}/artifacts.csv; done` | 1 | ❌ fail | 0.08s |
| 4 | `python scripts/package_eda_exports.py && python - <<'PY' ...` (slice forbidden-artifact scan + Track D blocker assertion) | 0 | ✅ pass | 0.12s |

## Diagnostics

Run `python scripts/package_eda_exports.py` to rebuild the bundle and print root status totals, governance totals, the Track E validity summary, and per-track blocker state.

Inspect `outputs/exports/eda/manifest.json` for the allowlist, forbidden-source status totals, emitted file count, and metadata-only validity-log summary. Inspect `outputs/exports/eda/EXPORT_CONTRACT.md` for the human-readable governance boundary and bundle format contract. Inspect `outputs/exports/eda/tracks/track_d/manifest.json` for Track D blocker visibility and `outputs/exports/eda/tracks/track_e/manifest.json` for the metadata-only validity summary.

## Deviations

None.

## Known Issues

The slice-level figure-presence check is still red because T03 has not yet generated `outputs/exports/eda/figures/eda_overview.png` or the per-track status-card PNG files.

## Files Created/Modified

- `scripts/package_eda_exports.py` — enforced source allowlisting, stale-bundle cleanup, forbidden-artifact checks, generated contract writing, and metadata-only Track E validity-log summarization.
- `tests/test_package_eda_exports.py` — added governance regression coverage for the contract file, forbidden suffix exclusion, stale artifact removal, and missing validity-log failures.
- `outputs/exports/eda/EXPORT_CONTRACT.md` — generated the human-readable export contract documenting layout, status semantics, blocker rules, and governance boundaries.
- `outputs/exports/eda/manifest.json` — regenerated the root manifest with governance metadata and Track E validity-scan summary fields.
- `outputs/exports/eda/tracks/track_e/manifest.json` — regenerated the Track E manifest with metadata-only validity-log summary output.
- `.gsd/milestones/M001-4q3lxl/slices/S02/tasks/T02-PLAN.md` — added the missing observability-impact section required by the pre-flight check.
- `.gsd/DECISIONS.md` — recorded D014 for metadata-only representation of the Track E validity log.
- `.gsd/KNOWLEDGE.md` — noted that the packager intentionally rebuilds the export bundle from scratch to flush stale forbidden artifacts.
