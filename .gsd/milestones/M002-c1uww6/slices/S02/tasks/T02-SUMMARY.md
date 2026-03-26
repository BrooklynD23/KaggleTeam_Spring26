---
id: T02
parent: S02
milestone: M002-c1uww6
provides:
  - Expanded deterministic regression coverage for Track A baseline feature derivation and clipped metric helpers
key_files:
  - tests/test_track_a_baseline_model.py
key_decisions:
  - Regress Track A helper behavior at the public helper boundary instead of adding brittle end-to-end-only assertions for category parsing, missing-feature backfills, and clipped metric math.
patterns_established:
  - When Track A baseline helpers evolve, extend pytest coverage around pure helper outputs so leakage-safe feature assumptions fail fast without rerunning the full modeling CLI.
observability_surfaces:
  - tests/test_track_a_baseline_model.py
  - python -m pytest tests/test_track_a_baseline_model.py
  - outputs/modeling/track_a/metrics.csv
  - outputs/modeling/track_a/summary.md
  - outputs/modeling/track_a/config_snapshot.json
duration: 18m
verification_result: passed
completed_at: 2026-03-23T15:42:55Z
blocker_discovered: false
---

# T02: Add helper regression tests for Track A baseline feature and metric logic

**Expanded Track A baseline helper tests to lock down category parsing, model-column backfills, and clipping-sensitive metric behavior.**

## What Happened

I inspected the existing `tests/test_track_a_baseline_model.py` that T01 had already created and treated T02 as an expansion pass rather than starting a brand-new test file.

I extended the regression surface in `tests/test_track_a_baseline_model.py` by adding:

- a parametrized category-edge-case test covering whitespace-only segments, empty strings, `None`, and non-string category values
- a derived-feature test that asserts `derive_track_a_features()` backfills every `MODEL_FEATURE_COLUMNS` entry, including missing-value indicator columns
- a zero-error metric test that verifies `compute_regression_metrics()` returns exact zero MAE/RMSE for already-valid perfect predictions

I kept the coverage at the public helper boundary, so the tests remain stable even if the baseline CLI internals change, while still failing loudly if feature semantics drift.

## Verification

I ran the task-level helper suite first, then reran the full slice verification gate to confirm the expanded test coverage did not break the Track A baseline CLI, artifact bundle, or leakage/quality assertions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_track_a_baseline_model.py` | 0 | ✅ pass | 1.33s |
| 2 | `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 1.61s |
| 3 | `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && test -f outputs/modeling/track_a/summary.md && test -f outputs/modeling/track_a/metrics.csv && test -f outputs/modeling/track_a/config_snapshot.json && test -f outputs/modeling/track_a/figures/predicted_vs_actual_test.png` | 0 | ✅ pass | 7.67s |
| 4 | `python - <<'PY' ... assert hist_gradient_boosting test MAE < naive_mean test MAE ... PY` | 0 | ✅ pass | 0.05s |
| 5 | `python - <<'PY' ... assert summary/config expose banned-field guardrails and preferred default M003 audit-target status ... PY` | 0 | ✅ pass | 0.04s |

## Diagnostics

Future agents can inspect this task by rerunning:

- `python -m pytest tests/test_track_a_baseline_model.py`
- `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py`

If helper behavior drifts, the likely failure surfaces are:

- category counting / `has_categories` expectations in the parametrized category test
- missing `MODEL_FEATURE_COLUMNS` backfill coverage in the derived-feature completeness test
- clipping-sensitive MAE/RMSE expectations in the metric helper tests

The broader Track A slice can still be spot-checked with:

- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
- `outputs/modeling/track_a/metrics.csv`
- `outputs/modeling/track_a/summary.md`
- `outputs/modeling/track_a/config_snapshot.json`

## Deviations

- T01 had already created the helper test file, so T02 expanded and hardened that existing regression surface instead of creating a new test module from scratch.
- I ran the full slice verification set in addition to the task plan’s pytest command so the task summary could record whether the broader Track A baseline contract still held after the test-only change.

## Known Issues

- The helper backfill test currently asserts NaN preservation for absent numeric source columns through a direct NaN check on `text_char_count`; if the baseline later adopts explicit imputation inside `derive_track_a_features()`, this regression test will need to be updated intentionally rather than treated as a surprise failure.

## Files Created/Modified

- `tests/test_track_a_baseline_model.py` — expanded helper regression coverage for category parsing, model-feature backfills, and clipped metric math
- `.gsd/milestones/M002-c1uww6/slices/S02/S02-PLAN.md` — marked T02 complete in the slice checklist
