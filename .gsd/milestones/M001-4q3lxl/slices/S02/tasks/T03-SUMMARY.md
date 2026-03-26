---
id: T03
parent: S02
milestone: M001-4q3lxl
provides:
  - Manifest-backed synthesized PNG evidence visuals for the aggregate-safe EDA export bundle plus a finalized real-worktree CLI handoff
key_files:
  - scripts/package_eda_exports.py
  - tests/test_package_eda_exports.py
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/EXPORT_CONTRACT.md
  - outputs/exports/eda/figures/eda_overview.png
  - outputs/exports/eda/figures/track_d_status_card.png
  - outputs/exports/eda/tracks/track_d/manifest.json
key_decisions:
  - Recorded D015 to generate export PNGs from dispatcher/census truth inside the packager and publish their canonical paths in the manifests
patterns_established:
  - Treat PNGs as synthesized packaging evidence surfaces, not copied analytical figures, and keep their paths in root/per-track manifest metadata for downstream inspection
observability_surfaces:
  - python scripts/package_eda_exports.py
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/figures/eda_overview.png
  - outputs/exports/eda/figures/track_d_status_card.png
  - outputs/exports/eda/tracks/track_d/manifest.json
duration: ~1h 10m
verification_result: passed
completed_at: 2026-03-21T23:05:00-07:00
blocker_discovered: false
---

# T03: Add synthesized PNG evidence visuals and close the CLI handoff

**Added manifest-backed packaging-status PNGs and finalized the real-worktree EDA export CLI handoff.**

## What Happened

I extended `tests/test_package_eda_exports.py` first so the regression suite required a real `outputs/exports/eda/figures/eda_overview.png`, one `track_<x>_status_card.png` per track, and manifest pointers for those figures before any implementation changes could pass.

I then finalized `scripts/package_eda_exports.py` to synthesize the PNG layer directly from dispatcher contract metadata plus census/blocker totals using Pillow instead of depending on missing upstream analytical figures. The packager now emits a bundle-wide `eda_overview.png` and one per-track status card, keeps their canonical paths in the root and per-track manifests, and labels them as packaging/evidence visuals rather than analytical findings.

I also closed the CLI handoff so `python scripts/package_eda_exports.py` in the stripped real worktree rebuilds the full bundle, logs root/per-track status totals plus blocker visibility, prints the new figure paths, and points future agents at the inspection surfaces that matter next (`manifest.json`, `figures/eda_overview.png`, and `tracks/track_d/manifest.json`).

Finally, I regenerated the real bundle outputs, updated `EXPORT_CONTRACT.md` to document the concrete PNG layout, recorded D015 for the synthesized-visuals approach, added a `.gsd/KNOWLEDGE.md` note about avoiding concurrent packager invocations against the same worktree, and marked T03 complete in the slice plan.

## Verification

I ran the focused pytest file after extending the tests and again after the implementation landed; it passed with the new PNG and manifest assertions in place.

I then ran the real CLI in this stripped worktree and verified that it now writes JSON, CSV, markdown, and PNG surfaces together under `outputs/exports/eda/`, including `figures/eda_overview.png` plus all five per-track status cards.

I also ran the slice-level file-existence and governance checks. They passed: forbidden `.parquet`, `.ndjson`, and `.log` artifacts are absent from the bundle, the contract still declares the `aggregate-safe` / `internal` boundary, and Track D blocker visibility remains explicit in `outputs/exports/eda/tracks/track_d/manifest.json`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_package_eda_exports.py` | 0 | ✅ pass | 1.19s |
| 2 | `python scripts/package_eda_exports.py` | 0 | ✅ pass | 0.47s |
| 3 | `python scripts/package_eda_exports.py && test -f outputs/exports/eda/manifest.json && test -f outputs/exports/eda/manifest.csv && test -f outputs/exports/eda/EXPORT_CONTRACT.md && test -f outputs/exports/eda/figures/eda_overview.png && for track in track_a track_b track_c track_d track_e; do test -f outputs/exports/eda/figures/${track}_status_card.png && test -f outputs/exports/eda/tracks/${track}/summary.md && test -f outputs/exports/eda/tracks/${track}/manifest.json && test -f outputs/exports/eda/tracks/${track}/artifacts.csv; done` | 0 | ✅ pass | 0.41s |
| 4 | `python scripts/package_eda_exports.py && python - <<'PY'` (forbidden-artifact scan + contract/Track D blocker assertions) | 0 | ✅ pass | 0.50s |
| 5 | `python scripts/package_eda_exports.py && python - <<'PY'` (bundle layout assertions for manifest/CSV/contract/overview PNG + per-track files) | 0 | ✅ pass | 0.52s |

## Diagnostics

Run `python scripts/package_eda_exports.py` to rebuild the full bundle and print root status totals, emitted file counts, per-track blocker state, and the canonical inspection paths.

Inspect `outputs/exports/eda/manifest.json` for the new `figures` block, `inspection_surfaces`, and bundle-wide emitted-file counts. Inspect `outputs/exports/eda/figures/eda_overview.png` for the synthesized bundle overview. Inspect `outputs/exports/eda/tracks/track_d/manifest.json` and `outputs/exports/eda/figures/track_d_status_card.png` for Track D’s exported blocker visibility and packaging-evidence figure metadata.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scripts/package_eda_exports.py` — added synthesized overview/per-track PNG rendering, manifest figure pointers, richer CLI inspection output, and finalized real-worktree bundle generation.
- `tests/test_package_eda_exports.py` — extended regression coverage to require PNG outputs, PNG dimensions, and figure-path manifest metadata.
- `outputs/exports/eda/manifest.json` — regenerated the root export manifest with `figures` and `inspection_surfaces` metadata.
- `outputs/exports/eda/EXPORT_CONTRACT.md` — regenerated the contract to document the concrete overview/status-card PNG layout.
- `outputs/exports/eda/figures/eda_overview.png` — generated the bundle-wide packaging/evidence overview visual.
- `outputs/exports/eda/figures/track_d_status_card.png` — generated the Track D packaging status card that preserves blocker visibility.
- `outputs/exports/eda/tracks/track_d/manifest.json` — regenerated the Track D manifest with the exported status-card pointer and caption.
- `.gsd/DECISIONS.md` — recorded D015 for census-derived PNG packaging visuals.
- `.gsd/KNOWLEDGE.md` — noted that concurrent packager invocations race on the reset bundle root and should be avoided.
- `.gsd/milestones/M001-4q3lxl/slices/S02/S02-PLAN.md` — marked T03 complete.
