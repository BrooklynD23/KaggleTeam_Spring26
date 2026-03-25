---
estimated_steps: 3
estimated_files: 3
skills_used:
  - verification-loop
---

# T03: Verify Track A baseline quality against the naïve comparator

**Slice:** S02 — Track A temporal baseline and audit-target handoff
**Milestone:** M002-c1uww6

## Description

Confirm that the Track A baseline is not just producing artifacts but actually clearing the milestone’s minimum quality bar against the naïve comparator.

## Steps

1. Read the generated metrics file.
2. Assert test MAE beats the naïve mean baseline.
3. Confirm the summary remains honest about caps, limitations, and audit-target suitability.

## Must-Haves

- [ ] Track A test MAE beats the naïve mean baseline.
- [ ] The summary remains honest about limits while preserving Track A as the preferred default audit target.

## Verification

- `python - <<'PY'
import pandas as pd
metrics = pd.read_csv('outputs/modeling/track_a/metrics.csv')
model_mae = metrics.loc[(metrics.model_name == 'hist_gradient_boosting') & (metrics.split_name == 'test'), 'mae'].iloc[0]
mean_mae = metrics.loc[(metrics.model_name == 'naive_mean') & (metrics.split_name == 'test'), 'mae'].iloc[0]
assert model_mae < mean_mae, (model_mae, mean_mae)
print('track_a model beats naive mean on test MAE')
PY`
- `rg -n "Known limitations|M003 audit suitability|Track A remains the preferred default" outputs/modeling/track_a/summary.md`

## Inputs

- `outputs/modeling/track_a/metrics.csv` — Track A baseline metrics to compare against the naïve baseline
- `outputs/modeling/track_a/summary.md` — Track A baseline narrative and audit-target handoff
- `outputs/modeling/track_a/config_snapshot.json` — Track A run context proving split and cap settings

## Expected Output

- `outputs/modeling/track_a/metrics.csv` — verified metric comparison surface
- `outputs/modeling/track_a/summary.md` — verified Track A audit-target handoff surface

## Observability Impact

- Signals touched: `outputs/modeling/track_a/metrics.csv` remains the metric-comparison surface, `outputs/modeling/track_a/summary.md` remains the audit-handoff narrative surface, and `outputs/modeling/track_a/config_snapshot.json` remains the cap/split provenance surface.
- How to inspect later: rerun `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`, then read the metrics row pair for `hist_gradient_boosting` vs `naive_mean` on `test` and confirm the summary includes both explicit limitations and the M003 audit-target framing.
- Failure visibility: comparator regressions surface as a failed MAE assertion, and dishonest or incomplete handoff language surfaces as missing summary markers for limitations, audit suitability, or preferred-default status.
