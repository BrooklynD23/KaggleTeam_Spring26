# S02: Track A temporal baseline and audit-target handoff

**Goal:** Deliver the first real Track A baseline model using the recommended temporal split, Track A-safe as-of features, and explicit naïve comparators.
**Demo:** Running the Track A baseline entrypoint writes a summary, metrics file, config snapshot, and diagnostic figure under `outputs/modeling/track_a/`, and the test MAE beats the naïve mean baseline while preserving Track A leakage constraints.

## Must-Haves

- A reproducible Track A baseline entrypoint exists under `src/modeling/track_a/` and reads only Track A-safe curated/history surfaces.
- The baseline writes the standard artifact bundle under `outputs/modeling/track_a/`.
- Metrics include MAE and RMSE plus a naïve comparator; the summary explicitly records excluded banned fields and split provenance.
- The output is strong enough to remain the preferred default M003 fairness-audit target.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && test -f outputs/modeling/track_a/summary.md && test -f outputs/modeling/track_a/metrics.csv && test -f outputs/modeling/track_a/config_snapshot.json && test -f outputs/modeling/track_a/figures/predicted_vs_actual_test.png`
- `python - <<'PY'
import pandas as pd
metrics = pd.read_csv('outputs/modeling/track_a/metrics.csv')
model_mae = metrics.loc[(metrics.model_name == 'hist_gradient_boosting') & (metrics.split_name == 'test'), 'mae'].iloc[0]
mean_mae = metrics.loc[(metrics.model_name == 'naive_mean') & (metrics.split_name == 'test'), 'mae'].iloc[0]
assert model_mae < mean_mae, (model_mae, mean_mae)
print('track_a model beats naive mean on test MAE')
PY`
- `python - <<'PY'
import json
from pathlib import Path
summary = Path('outputs/modeling/track_a/summary.md').read_text(encoding='utf-8')
config = json.loads(Path('outputs/modeling/track_a/config_snapshot.json').read_text(encoding='utf-8'))
assert 'excluded banned fields' in summary.lower()
assert 'preferred default m003 audit target' in summary.lower()
assert 'banned_features' in config and config['banned_features']
print('track_a summary/config expose leakage guardrails and audit-target status')
PY`

## Observability / Diagnostics

- Runtime signals: `outputs/modeling/track_a/metrics.csv`, `outputs/modeling/track_a/config_snapshot.json`, and `outputs/modeling/track_a/summary.md`
- Inspection surfaces: `python -m src.modeling.track_a.baseline --config configs/track_a.yaml`, the Track A modeling output directory, and the Track A baseline helper tests
- Failure visibility: missing split artifacts, missing Stage 3 history inputs, or baseline/comparator metric regressions surface through the CLI command and test assertions
- Redaction constraints: no raw review text or banned snapshot-only fields in outputs or feature lists

## Integration Closure

- Upstream surfaces consumed: `data/curated/review_fact.parquet`, `outputs/tables/track_a_s3_user_history_asof.parquet`, `outputs/tables/track_a_s3_business_history_asof.parquet`, `outputs/tables/track_a_s5_candidate_splits.parquet`, `outputs/tables/track_a_s7_feature_availability.parquet`, `configs/track_a.yaml`
- New wiring introduced in this slice: `src/modeling/track_a/baseline.py` plus Track A modeling artifacts under `outputs/modeling/track_a/`
- What remains before the milestone is truly usable end-to-end: Track B, Track C, Track D1, and integrated milestone verification in S03–S06

## Tasks

- [x] **T01: Implement the Track A baseline entrypoint and artifact bundle** `est:1h 30m`
  - Why: M002 needs a real Track A baseline before any later audit/reporting work can attach to it.
  - Files: `src/modeling/track_a/baseline.py`, `src/modeling/README.md`, `outputs/modeling/track_a/`
  - Do: Build a reproducible baseline script that loads the recommended split, joins Stage 3 history features onto `review_fact.parquet`, uses Track A-safe as-of features only, fits a simple supervised baseline, evaluates against naïve comparators, and writes summary/metrics/config/figure artifacts into the Track A modeling output root.
  - Verify: `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && test -f outputs/modeling/track_a/summary.md && test -f outputs/modeling/track_a/metrics.csv && test -f outputs/modeling/track_a/config_snapshot.json`
  - Done when: Track A has a real modeling output bundle under `outputs/modeling/track_a/` and the summary names inputs, excluded features, split provenance, metrics, and the preferred M003 audit-target status.
- [x] **T02: Add helper regression tests for Track A baseline feature and metric logic** `est:45m`
  - Why: The first modeling slice should not rely on an untested script blob when pure helper behavior can be locked down cheaply.
  - Files: `tests/test_track_a_baseline_model.py`, `src/modeling/track_a/baseline.py`
  - Do: Add focused tests for derived feature construction and metric behavior so category counting, first-review flags, and clipped star metrics stay stable as the baseline evolves.
  - Verify: `python -m pytest tests/test_track_a_baseline_model.py`
  - Done when: Track A helper logic has deterministic regression coverage and future edits fail loudly if the artifact assumptions drift.
- [x] **T03: Verify Track A baseline quality against the naïve comparator** `est:30m`
  - Why: S02 is not done just because artifacts exist; the baseline must clear the milestone’s minimal quality bar.
  - Files: `outputs/modeling/track_a/metrics.csv`, `outputs/modeling/track_a/summary.md`, `outputs/modeling/track_a/config_snapshot.json`
  - Do: Run the baseline, confirm the test MAE beats the naïve mean comparator, and ensure the summary frames Track A as the preferred default M003 audit target while being honest about caps and limitations.
  - Verify: `python - <<'PY'
import pandas as pd
metrics = pd.read_csv('outputs/modeling/track_a/metrics.csv')
model_mae = metrics.loc[(metrics.model_name == 'hist_gradient_boosting') & (metrics.split_name == 'test'), 'mae'].iloc[0]
mean_mae = metrics.loc[(metrics.model_name == 'naive_mean') & (metrics.split_name == 'test'), 'mae'].iloc[0]
assert model_mae < mean_mae, (model_mae, mean_mae)
print('track_a model beats naive mean on test MAE')
PY`
  - Done when: the baseline demonstrably clears the naïve mean MAE bar and the resulting summary is usable as the default M003 audit handoff.

## Files Likely Touched

- `src/modeling/track_a/baseline.py`
- `src/modeling/README.md`
- `tests/test_track_a_baseline_model.py`
- `outputs/modeling/track_a/summary.md`
- `outputs/modeling/track_a/metrics.csv`
- `outputs/modeling/track_a/config_snapshot.json`
- `outputs/modeling/track_a/figures/predicted_vs_actual_test.png`
