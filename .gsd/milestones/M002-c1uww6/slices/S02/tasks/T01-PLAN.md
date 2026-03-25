---
estimated_steps: 4
estimated_files: 3
skills_used:
  - coding-standards
  - verification-loop
---

# T01: Implement the Track A baseline entrypoint and artifact bundle

**Slice:** S02 — Track A temporal baseline and audit-target handoff
**Milestone:** M002-c1uww6

## Description

Build the first real Track A baseline entrypoint. This task turns the Track A EDA handoff into a reproducible supervised baseline with standardized modeling artifacts and explicit naïve comparators.

## Steps

1. Load the recommended split from the Track A Stage 5 artifact.
2. Join Track A-safe Stage 3 history features to `review_fact.parquet`.
3. Fit a simple baseline model and evaluate against naïve comparators.
4. Write summary, metrics, config snapshot, and a diagnostic figure under `outputs/modeling/track_a/`.

## Must-Haves

- [ ] The baseline uses only Track A-safe as-of features and records excluded banned fields in the summary.
- [ ] The standard artifact bundle exists under `outputs/modeling/track_a/`.
- [ ] The summary keeps Track A as the preferred default M003 audit target.

## Verification

- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
- `test -f outputs/modeling/track_a/summary.md && test -f outputs/modeling/track_a/metrics.csv && test -f outputs/modeling/track_a/config_snapshot.json && test -f outputs/modeling/track_a/figures/predicted_vs_actual_test.png`

## Inputs

- `configs/track_a.yaml` — Track A split and leakage rules
- `data/curated/review_fact.parquet` — Track A curated feature base
- `outputs/tables/track_a_s3_user_history_asof.parquet` — Track A user-history as-of features
- `outputs/tables/track_a_s3_business_history_asof.parquet` — Track A business-history as-of features
- `outputs/tables/track_a_s5_candidate_splits.parquet` — recommended temporal split source
- `outputs/tables/track_a_s7_feature_availability.parquet` — feature coverage context

## Expected Output

- `src/modeling/track_a/baseline.py` — Track A baseline entrypoint
- `outputs/modeling/track_a/summary.md` — Track A baseline summary
- `outputs/modeling/track_a/metrics.csv` — Track A baseline metrics
- `outputs/modeling/track_a/config_snapshot.json` — Track A baseline run context
- `outputs/modeling/track_a/figures/predicted_vs_actual_test.png` — Track A diagnostic figure

## Observability Impact

- Runtime signals added or updated: `outputs/modeling/track_a/metrics.csv`, `outputs/modeling/track_a/config_snapshot.json`, `outputs/modeling/track_a/summary.md`, and `outputs/modeling/track_a/figures/predicted_vs_actual_test.png`
- How a future agent inspects this task: rerun `python -m src.modeling.track_a.baseline --config configs/track_a.yaml`, then inspect the output bundle under `outputs/modeling/track_a/` and the helper regression tests in `tests/test_track_a_baseline_model.py`
- Failure state that becomes visible: missing Stage 3/5 inputs, banned-feature leakage, or comparator regressions surface through CLI errors, absent artifacts, and metric assertions against the generated `metrics.csv`
