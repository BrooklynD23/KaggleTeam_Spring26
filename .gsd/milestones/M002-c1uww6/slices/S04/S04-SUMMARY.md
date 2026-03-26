---
id: S04
parent: M002-c1uww6
milestone: M002-c1uww6
provides:
  - Track C monitoring baseline runtime that emits deterministic ranked drift/stability artifacts under outputs/modeling/track_c/.
requires:
  - slice: M001-4q3lxl/S01
    provides: Stage 4/6/8 aggregate artifacts used to build city-level monitoring features.
affects:
  - S06
  - M003-rdpeu4
key_files:
  - src/modeling/track_c/baseline.py
  - tests/test_track_c_baseline_model.py
  - outputs/modeling/track_c/drift_surface.parquet
  - outputs/modeling/track_c/metrics.csv
  - outputs/modeling/track_c/config_snapshot.json
  - outputs/modeling/track_c/summary.md
key_decisions:
  - D023 fixed Track C monitoring score composition, deterministic ranking tie-breaks, and monitoring-only non-forecast framing as explicit contract behavior.
patterns_established:
  - Validate both positive contract phrases and negative framing constraints (forbidden predictive language) so monitoring docs do not drift into forecast claims.
observability_surfaces:
  - python -m src.modeling.track_c.baseline --config configs/track_c.yaml
  - python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py
  - outputs/modeling/track_c/drift_surface.parquet
  - outputs/modeling/track_c/metrics.csv
  - outputs/modeling/track_c/config_snapshot.json
  - outputs/modeling/track_c/summary.md
drill_down_paths:
  - .gsd/milestones/M002-c1uww6/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S04/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S04/tasks/T03-SUMMARY.md
duration: 2h 35m
verification_result: passed
completed_at: 2026-03-23
---

# S04: Track C monitoring baseline contract

**Implemented and stabilized the Track C monitoring baseline that ranks city-level change surfaces while explicitly rejecting forecast-style framing.**

## What Happened

S04 introduced `src/modeling/track_c/baseline.py` as a runnable CLI that joins Stage 4/6/8 signals, derives monitoring features, computes deterministic `monitoring_change_score`, and writes a complete Track C artifact bundle. The slice also added helper regression tests and contract assertions for deterministic ranking, required drift config keys, and summary wording that must stay monitoring-only.

A runtime packaging issue surfaced around eager package imports; `src/modeling/track_c/__init__.py` was kept lightweight to avoid `python -m` warning/noise. Slice close reran the full gate and confirmed the generated artifacts already satisfied schema, score ordering, and non-forecast phrase constraints.

Concrete verification artifacts for this slice are:
- `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
- `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py`
- `outputs/modeling/track_c/drift_surface.parquet` with descending `monitoring_change_score` and no raw-text leakage columns.

## Verification

All T01–T03 checks passed, including runtime generation, helper suites, artifact contract assertions, and invalid-config failure diagnostics. The slice also validated summary phrase presence (`monitoring`, `drift`, `stability`, `ranked change surface`, `not a forecast`) and forbidden predictive wording.

## Requirements Advanced

- R007 — Delivered and verified the required drift/trend characterization baseline without escalating to heavyweight forecasting.
- R012 — Added stable handoff language patterns for monitoring outputs and diagnostics.

## Requirements Validated

- R007 — Proven by repeatable runtime + pytest + artifact assertions over Track C monitoring surfaces.

## New Requirements Surfaced

- none.

## Requirements Invalidated or Re-scoped

- none.

## Deviations

T01 created the initial helper test module earlier than planned so first-task verification could run on a real regression surface.

## Known Limitations

Track C output is monitoring/trend characterization only; it does not provide predictive horizon forecasts and should not be interpreted as one.

## Follow-ups

- Preserve explicit non-forecast wording checks when evolving summary templates in M003/M004.
- If scoring weights or tie-break rules are changed, update D023 references and regenerate artifacts before integrated handoff tests.

## Files Created/Modified

- `src/modeling/track_c/baseline.py` — monitoring baseline runtime, score composition, artifact writing, and redaction checks.
- `src/modeling/track_c/__init__.py` — lightweight package export surface to avoid module execution noise.
- `tests/test_track_c_baseline_model.py` — helper tests for deterministic ranking, summary phrasing, and config snapshot keys.
- `outputs/modeling/track_c/drift_surface.parquet` — ranked change-surface artifact for downstream diagnostics.
- `outputs/modeling/track_c/summary.md` — monitoring-only narrative with explicit non-forecast framing.

## Forward Intelligence

### What the next slice should know
- Integrated checks depend on exact monitoring framing in `outputs/modeling/track_c/summary.md`; phrase drift can fail handoff tests even when metrics are unchanged.

### What's fragile
- Auto-mode command routing can differ across execution tools; verify Track C commands run in the active worktree before treating path/import failures as product bugs.

### Authoritative diagnostics
- `outputs/modeling/track_c/drift_surface.parquet` plus `metrics.csv` — these are the most reliable first signals for ranking/coverage regressions.

### What assumptions changed
- “Track C needs forecasting to be useful” — delivered contract confirmed monitoring/trend characterization is sufficient and aligned with R007 scope.
