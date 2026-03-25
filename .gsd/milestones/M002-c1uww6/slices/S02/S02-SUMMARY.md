---
id: S02
parent: M002-c1uww6
milestone: M002-c1uww6
provides:
  - Track A baseline runtime with leakage-safe temporal features, comparator metrics, and reproducible artifact bundle under outputs/modeling/track_a/.
requires:
  - slice: M001-4q3lxl/S01
    provides: Curated Stage 3/5 evidence surfaces consumed by the Track A baseline runner.
affects:
  - S06
  - M003-rdpeu4
key_files:
  - src/modeling/track_a/baseline.py
  - tests/test_track_a_baseline_model.py
  - outputs/modeling/track_a/metrics.csv
  - outputs/modeling/track_a/config_snapshot.json
  - outputs/modeling/track_a/summary.md
  - outputs/modeling/track_a/predictions_test.parquet
key_decisions:
  - D020: Use HistGradientBoostingRegressor with naive_mean, naive_business_prior_avg, and naive_user_prior_avg comparators for the first Track A baseline contract.
patterns_established:
  - Keep Track A feature derivation bounded to review_fact + as-of history artifacts and fail helper regressions at pure-function boundaries before full runtime drift reaches integrated gates.
observability_surfaces:
  - python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000
  - python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py
  - outputs/modeling/track_a/metrics.csv
  - outputs/modeling/track_a/config_snapshot.json
  - outputs/modeling/track_a/summary.md
drill_down_paths:
  - .gsd/milestones/M002-c1uww6/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S02/tasks/T03-SUMMARY.md
duration: 1h 57m
verification_result: passed
completed_at: 2026-03-23
---

# S02: Track A baseline modeling contract

**Shipped a leakage-safe Track A baseline bundle with explicit comparator truth checks and helper-level regression coverage for as-of feature semantics.**

## What Happened

S02 implemented and stabilized `src/modeling/track_a/baseline.py` as a real CLI that loads Stage 5 splits plus Stage 3 history artifacts, derives safe numeric features, trains a baseline model, evaluates against three comparators, and writes the full artifact bundle to `outputs/modeling/track_a/`.

Task work then expanded regression coverage in `tests/test_track_a_baseline_model.py` for category parsing edge cases, complete model-column backfills, and clipping-aware metric behavior. Slice close regenerated artifacts and hardened summary wording so the runtime output itself carries required handoff markers (`Known limitations`, `M003 audit suitability`) rather than relying on manual edits.

Concrete verification artifacts for this slice are the passing command outputs from:
- `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
- `outputs/modeling/track_a/metrics.csv` comparator rows (including test MAE vs `naive_mean`).

## Verification

Across T01–T03, Track A slice verification repeatedly passed on helper tests, runtime generation, comparator assertions, and summary/config guardrail assertions. Artifacts were regenerated in-worktree and checked for presence and contract wording.

## Requirements Advanced

- R005 — Delivered and repeatedly verified the Track A baseline runtime and comparator evidence surface.
- R012 — Added reusable slice-level narrative/diagnostic conventions for future handoff docs.

## Requirements Validated

- R005 — Slice-level proof includes passing runtime + comparator assertions and persisted artifact bundle under `outputs/modeling/track_a/`.

## New Requirements Surfaced

- none.

## Requirements Invalidated or Re-scoped

- none.

## Deviations

T01 created the initial Track A helper test module earlier than originally planned for T02 so slice verification had immediate regression coverage.

## Known Limitations

The capped baseline reliably beats `naive_mean` but still trails `naive_business_prior_avg` on test MAE; this remains a meaningful benchmark risk for downstream model upgrades.

## Follow-ups

- In M003, keep Track A as the default fairness audit target (R009 support path) unless a stronger justified swap is documented.
- If Track A feature logic changes, extend helper-level tests first, then rerun full baseline CLI to refresh artifact truth.

## Files Created/Modified

- `src/modeling/track_a/baseline.py` — runtime entrypoint, feature assembly, comparator evaluation, artifact writing, and summary contract markers.
- `tests/test_track_a_baseline_model.py` — helper regression coverage for category handling, feature backfills, and metric clipping behavior.
- `outputs/modeling/track_a/metrics.csv` — comparator and model metrics used for quality assertions.
- `outputs/modeling/track_a/config_snapshot.json` — run metadata, split provenance, selected features, and banned field guardrails.
- `outputs/modeling/track_a/summary.md` — runtime-generated handoff narrative for limitations and M003 audit suitability.

## Forward Intelligence

### What the next slice should know
- Track A quality gating in this milestone is `hist_gradient_boosting` test MAE versus `naive_mean`; do not silently change that comparator gate without updating integrated tests.

### What's fragile
- Summary marker strings in `outputs/modeling/track_a/summary.md` — integrated handoff checks rely on them and will fail if headings drift.

### Authoritative diagnostics
- `outputs/modeling/track_a/metrics.csv` — it is the fastest trustworthy source for comparator regressions before rerunning heavy downstream checks.

### What assumptions changed
- “Model should beat business prior quickly” — capped-run evidence showed business-prior remains stronger than expected, so comparator interpretation must stay explicit.
