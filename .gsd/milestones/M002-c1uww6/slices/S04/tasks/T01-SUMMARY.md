---
id: T01
parent: S04
milestone: M002-c1uww6
provides:
  - Runnable Track C monitoring baseline that emits ranked drift/stability artifacts under outputs/modeling/track_c.
key_files:
  - src/modeling/track_c/baseline.py
  - src/modeling/track_c/__init__.py
  - tests/test_track_c_baseline_model.py
  - outputs/modeling/track_c/drift_surface.parquet
  - outputs/modeling/track_c/summary.md
key_decisions:
  - D023 fixed Track C monitoring score composition weights and deterministic ranking tie-breaks.
patterns_established:
  - Track C modeling writes fail fast when required Stage 4/6/8 inputs or required columns are missing.
  - Track C artifacts enforce banned raw-text-column checks before persistence.
observability_surfaces:
  - outputs/modeling/track_c/metrics.csv
  - outputs/modeling/track_c/drift_surface.parquet
  - outputs/modeling/track_c/config_snapshot.json
  - outputs/modeling/track_c/summary.md
  - outputs/modeling/track_c/figures/monitoring_change_by_city.png
duration: 1h 20m
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T01: Implement Track C monitoring baseline runtime and artifact bundle

**Implemented a runnable Track C monitoring baseline that builds a deterministic ranked city change surface and writes the full `outputs/modeling/track_c/` artifact bundle with monitoring-only framing.**

## What Happened

Implemented `src/modeling/track_c/baseline.py` with Track A/B-style runtime flow: config loading, required-input checks, strict required-column validation, Stage 4/6/8 parquet loading, city-level feature assembly, deterministic monitoring scoring, artifact writing, and CLI entrypoint (`python -m src.modeling.track_c.baseline --config ...`).

The runtime now computes rolling stability features from Stage 4, sentiment and topic drift rollups from Stage 6, and check-in correlation context from Stage 8, then composes a weighted `monitoring_change_score` and ranks descending with deterministic tie-breaks. Output artifacts (`metrics.csv`, `drift_surface.parquet`, `config_snapshot.json`, `summary.md`, and `figures/monitoring_change_by_city.png`) are emitted under `outputs/modeling/track_c/` and enforce banned text-column redaction checks.

Added `tests/test_track_c_baseline_model.py` in this task (ahead of T02) to satisfy first-task slice verification expectations and lock core helper behavior now: topic rollup significance counting, rolling-window stability feature generation, deterministic ranking order, and required monitoring-only summary phrases.

Adjusted `src/modeling/track_c/__init__.py` to export the package surface without eager baseline import so `python -m src.modeling.track_c.baseline` runs without runpy module-preload warnings.

Recorded D023 for the score-composition contract and appended a related non-obvious import/runtime warning guardrail to `.gsd/KNOWLEDGE.md`.

## Verification

Ran both task-level and slice-level checks after implementation:

- Baseline runtime command succeeds and writes all required Track C modeling artifacts.
- Helper + contract pytest suite passes (`test_track_c_baseline_model.py`, `test_track_c_common.py`, `test_m002_modeling_contract.py`).
- Artifact integrity snippet verifies non-empty ranked surface, monotonic descending `monitoring_change_score`, required metric columns, required summary phrases (`monitoring`, `drift`, `stability`, `ranked change surface`, `not a forecast`), and drift config snapshot keys.
- Invalid config path check confirms inspectable failure diagnostics.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 1.03s |
| 2 | `python -m src.modeling.track_c.baseline --config configs/track_c.yaml && test -f outputs/modeling/track_c/summary.md && test -f outputs/modeling/track_c/metrics.csv && test -f outputs/modeling/track_c/config_snapshot.json && test -f outputs/modeling/track_c/drift_surface.parquet && test -f outputs/modeling/track_c/figures/monitoring_change_by_city.png` | 0 | ✅ pass | 2.23s |
| 3 | `python - <<'PY' ...artifact contract assertions for drift_surface/metrics/summary/config... PY` | 0 | ✅ pass | 0.58s |
| 4 | `python - <<'PY' ...invalid config path failure visibility check... PY` | 0 | ✅ pass | 0.84s |

## Diagnostics

Primary inspection surfaces for this task:

- `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
- `outputs/modeling/track_c/metrics.csv`
- `outputs/modeling/track_c/drift_surface.parquet`
- `outputs/modeling/track_c/config_snapshot.json`
- `outputs/modeling/track_c/summary.md`
- `outputs/modeling/track_c/figures/monitoring_change_by_city.png`

Failure visibility added/preserved:

- Missing Stage 4/6/8 inputs fail with explicit `FileNotFoundError` naming missing artifacts.
- Malformed drift/source schema fails with explicit missing-column `ValueError` including available columns.
- Invalid config path remains inspectable via `load_config` error text containing the missing path.
- Banned text-column leakage fails before write via artifact-level redaction guards.

## Deviations

- Created `tests/test_track_c_baseline_model.py` in T01 instead of waiting for T02 so first-task slice verification had the declared test surface immediately.

## Known Issues

- None.

## Files Created/Modified

- `src/modeling/track_c/baseline.py` — added full Track C monitoring baseline runtime, helper logic, scoring, artifact writers, and CLI.
- `src/modeling/track_c/__init__.py` — set lightweight package export surface (`baseline`) to avoid eager-import runtime warnings.
- `tests/test_track_c_baseline_model.py` — added helper regression tests for rollups, stability, deterministic ranking, and summary framing.
- `outputs/modeling/track_c/metrics.csv` — generated machine-readable monitoring metrics.
- `outputs/modeling/track_c/drift_surface.parquet` — generated ranked monitoring change surface with `monitoring_change_score`.
- `outputs/modeling/track_c/config_snapshot.json` — generated resolved run configuration snapshot with drift settings.
- `outputs/modeling/track_c/summary.md` — generated monitoring-only summary with non-forecast framing.
- `outputs/modeling/track_c/figures/monitoring_change_by_city.png` — generated ranked city monitoring figure.
- `.gsd/DECISIONS.md` — appended D023 (Track C monitoring score composition contract).
- `.gsd/KNOWLEDGE.md` — appended Track C `__init__` eager-import/runpy warning guardrail.
- `.gsd/milestones/M002-c1uww6/slices/S04/S04-PLAN.md` — marked T01 complete.
