---
id: T01
parent: S02
milestone: M002-c1uww6
provides:
  - Track A baseline CLI, comparator artifact bundle, and helper regression coverage
key_files:
  - src/modeling/track_a/baseline.py
  - tests/test_track_a_baseline_model.py
  - outputs/modeling/track_a/summary.md
key_decisions:
  - D020: Use HistGradientBoostingRegressor with naive_mean, naive_business_prior_avg, and naive_user_prior_avg comparators for the first Track A baseline bundle.
patterns_established:
  - Model Track A only from review_fact plus Stage 3 as-of history artifacts, then persist metrics/config/summary/predictions/figure under outputs/modeling/track_a/.
observability_surfaces:
  - outputs/modeling/track_a/metrics.csv
  - outputs/modeling/track_a/config_snapshot.json
  - outputs/modeling/track_a/summary.md
  - outputs/modeling/track_a/predictions_test.parquet
  - outputs/modeling/track_a/figures/predicted_vs_actual_test.png
duration: 1h 5m
verification_result: passed
completed_at: 2026-03-23T08:40:00Z
blocker_discovered: false
---

# T01: Implement the Track A baseline entrypoint and artifact bundle

**Added the Track A baseline CLI with leakage-safe as-of features, explicit comparators, and a reproducible artifact bundle.**

## What Happened

I first applied the required pre-flight observability fixes to `.gsd/milestones/M002-c1uww6/slices/S02/S02-PLAN.md` and `.gsd/milestones/M002-c1uww6/slices/S02/tasks/T01-PLAN.md` so the slice/task contracts explicitly covered failure visibility and inspection surfaces.

I then implemented `src/modeling/track_a/baseline.py` as a real CLI entrypoint that:

- loads the recommended Stage 5 temporal split
- joins `review_fact.parquet` to the Stage 3 user/business as-of history artifacts in DuckDB
- derives Track A-safe numeric features only
- trains a `HistGradientBoostingRegressor`
- evaluates against `naive_mean`, `naive_business_prior_avg`, and `naive_user_prior_avg`
- writes `metrics.csv`, `config_snapshot.json`, `summary.md`, `predictions_test.parquet`, and `figures/predicted_vs_actual_test.png` under `outputs/modeling/track_a/`

I also added `tests/test_track_a_baseline_model.py` to lock down the helper behavior the later slice tasks depend on, specifically category counting, first-review flags, and clipped star-metric computation.

The generated summary explicitly records the excluded banned fields and keeps Track A framed as the preferred default M003 audit target, while honestly noting that the learned model beats `naive_mean` but still trails `naive_business_prior_avg` on this capped run.

## Verification

I ran the slice test gate, the real baseline CLI, the artifact existence checks, the explicit test-MAE-vs-`naive_mean` assertion, and the added observability/guardrail check against the generated summary/config bundle.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 2.01s |
| 2 | `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && test -f outputs/modeling/track_a/summary.md && test -f outputs/modeling/track_a/metrics.csv && test -f outputs/modeling/track_a/config_snapshot.json && test -f outputs/modeling/track_a/figures/predicted_vs_actual_test.png` | 0 | ✅ pass | 9.30s |
| 3 | `python - <<'PY' ... assert hist_gradient_boosting test MAE < naive_mean test MAE ... PY` | 0 | ✅ pass | 0.35s |
| 4 | `python - <<'PY' ... assert summary/config expose banned-field guardrails and preferred default M003 audit-target status ... PY` | 0 | ✅ pass | 0.04s |

## Diagnostics

Future agents can inspect this task by rerunning:

- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
- `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py`

Then inspect:

- `outputs/modeling/track_a/metrics.csv` for comparator regressions
- `outputs/modeling/track_a/config_snapshot.json` for split provenance, caps, selected features, and banned fields
- `outputs/modeling/track_a/summary.md` for the leakage/audit-target narrative
- `outputs/modeling/track_a/predictions_test.parquet` and `outputs/modeling/track_a/figures/predicted_vs_actual_test.png` for behavior inspection

If Stage 3/5 inputs go missing or leakage guardrails drift, the CLI now fails early with missing-input errors or downstream metric/assertion failures.

## Deviations

- I added `tests/test_track_a_baseline_model.py` during T01 instead of waiting for T02 because this was the first execution task in the slice and the slice verification already depended on that helper regression surface.
- I also emitted `outputs/modeling/track_a/predictions_test.parquet` even though the task checklist only required metrics/config/summary/figure, because the modeling README contract expects an inspectable scored-output artifact in the baseline bundle.

## Known Issues

- On the capped verification run, `hist_gradient_boosting` beats `naive_mean` on test MAE but does **not** beat `naive_business_prior_avg`. This does not block S02’s stated quality bar, but downstream work should treat the business-history comparator as a serious benchmark rather than a throwaway baseline.

## Files Created/Modified

- `src/modeling/track_a/baseline.py` — implemented the Track A baseline CLI, feature derivation helpers, comparator evaluation, and artifact writing
- `tests/test_track_a_baseline_model.py` — added deterministic regression tests for Track A baseline helper logic
- `.gsd/milestones/M002-c1uww6/slices/S02/S02-PLAN.md` — added an explicit observability-oriented slice verification check
- `.gsd/milestones/M002-c1uww6/slices/S02/tasks/T01-PLAN.md` — added the missing `## Observability Impact` section
- `outputs/modeling/track_a/metrics.csv` — persisted Track A model and comparator metrics
- `outputs/modeling/track_a/config_snapshot.json` — persisted run context, split provenance, selected features, and banned fields
- `outputs/modeling/track_a/summary.md` — persisted the Track A baseline narrative and audit-target handoff notes
- `outputs/modeling/track_a/predictions_test.parquet` — persisted test-split predictions for inspection
- `outputs/modeling/track_a/figures/predicted_vs_actual_test.png` — persisted the test diagnostic figure
