# S06: Integrated modeling handoff and milestone verification — UAT

**Milestone:** M002-c1uww6  
**Written:** 2026-03-23

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: S06 acceptance depends on one executable cross-track gate (pytest + four baseline CLIs), plus semantic handoff/doc-hygiene assertions and replay evidence for fresh-agent continuation.

## Preconditions

- `data/curated/` artifacts required by Track A/B/C/D baselines are present.
- Python environment can run project modules and pytest.
- `outputs/modeling/track_a/`, `track_b/`, `track_c/`, and `track_d/` are writable.

## Integrated Replay Command Chain

1. `python -m pytest tests/test_track_a_baseline_model.py tests/test_track_b_baseline_model.py tests/test_track_c_baseline_model.py tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py tests/test_m002_handoff_verification.py -q`
2. `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && python -m src.modeling.track_b.baseline --config configs/track_b.yaml && python -m src.modeling.track_c.baseline --config configs/track_c.yaml && python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
3. `python - <<'PY' ...` semantic script from `S06-PLAN.md` verification block.
4. `rg -n "test_m002_handoff_verification|track_a.baseline|track_b.baseline|track_c.baseline|track_d.baseline" .gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md`

## Smoke Test

Run the full replay command chain above from repo root. The chain is considered healthy when:

- Integrated pytest gate is green.
- All four baseline CLIs exit 0 and rewrite bundle artifacts under `outputs/modeling/track_*/`.
- Semantic checks report either pass or an explicit state-surface dependency owned by follow-on work.

## Test Cases

### 1) Integrated pytest contract gate

Run:

```bash
python -m pytest tests/test_track_a_baseline_model.py tests/test_track_b_baseline_model.py tests/test_track_c_baseline_model.py tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py tests/test_m002_handoff_verification.py -q
```

Expected: all tests pass.

### 2) Cross-track baseline rerun

Run:

```bash
python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && \
python -m src.modeling.track_b.baseline --config configs/track_b.yaml && \
python -m src.modeling.track_c.baseline --config configs/track_c.yaml && \
python -m src.modeling.track_d.baseline --config configs/track_d.yaml
```

Expected: all commands pass and rewrite `metrics.csv`, `config_snapshot.json`, `summary.md` for each track.

### 3) T03-owned semantic contract assertions

Run:

```bash
python - <<'PY'
from pathlib import Path
import pandas as pd

root = Path('.')
for sid in ['S02', 'S03', 'S04', 'S05']:
    summary = root / f'.gsd/milestones/M002-c1uww6/slices/{sid}/{sid}-SUMMARY.md'
    uat = root / f'.gsd/milestones/M002-c1uww6/slices/{sid}/{sid}-UAT.md'
    assert summary.exists() and summary.read_text(encoding='utf-8').strip()
    assert 'Recovery placeholder' not in uat.read_text(encoding='utf-8')

a = pd.read_csv(root / 'outputs/modeling/track_a/metrics.csv')
a_model = float(a.loc[(a.model_name == 'hist_gradient_boosting') & (a.split_name == 'test'), 'mae'].iloc[0])
a_naive = float(a.loc[(a.model_name == 'naive_mean') & (a.split_name == 'test'), 'mae'].iloc[0])
assert a_model < a_naive

b = pd.read_csv(root / 'outputs/modeling/track_b/metrics.csv')
def b_ndcg(model):
    return float(b.loc[(b.model_name == model) & (b.split_name == 'test') & (b.age_bucket == 'ALL'), 'ndcg_at_10'].iloc[0])
assert b_ndcg('pointwise_percentile_regressor') > b_ndcg('text_length_only') > b_ndcg('review_stars_only')

c = pd.read_csv(root / 'outputs/modeling/track_c/metrics.csv').set_index('metric_name')['metric_value']
assert c['significant_sentiment_city_count'] > 0 and c['significant_topic_city_count'] > 0

d = pd.read_csv(root / 'outputs/modeling/track_d/metrics.csv')
extract = lambda model: float(d.loc[(d.subtrack == 'D1') & (d.model_name == model) & (d.split_name == 'test') & (d.cohort_label == 'ALL') & (d.metric_name == 'ndcg_at_10'), 'metric_value'].iloc[0])
assert extract('d1_pointwise_baseline') > extract('asof_popularity_baseline')

print('Cross-track semantic assertions (T03-owned) passed')
PY
```

Expected: script prints pass message and exits 0.

### 4) Slice-level semantic script (from S06 plan)

Run the exact verification script from `S06-PLAN.md`.

Observed behavior in T03: fails with `AssertionError: R005 not validated` until T04 updates state surfaces (`.gsd/REQUIREMENTS.md` / roadmap closure).

### 5) UAT command-presence check

Run:

```bash
rg -n "test_m002_handoff_verification|track_a.baseline|track_b.baseline|track_c.baseline|track_d.baseline" .gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md
```

Expected: all command references are present in this file.

## Executed Evidence (2026-03-23)

| # | Command | Exit | Duration | Key Evidence |
|---|---|---|---|---|
| 1 | Integrated pytest gate (run 2) | 0 | 9.50s | `69 passed in 8.04s` |
| 2 | Baseline chain A→B→C→D (run 2) | 0 | 340.50s | All four CLIs wrote `metrics.csv`, `config_snapshot.json`, `summary.md`; Track D also wrote `d2_optional_report.csv` |
| 3 | T03-owned semantic assertions | 0 | 2.34s | Printed `Cross-track semantic assertions (T03-owned) passed` |
| 4 | S06 plan semantic script | 1 | 0.04s | `AssertionError: R005 not validated` (owned by T04 state-surface closure) |
| 5 | UAT regex presence check | 0 | 0.00s | `rg` found integrated gate command references |

## Key Metrics Snapshot (from run 2 artifacts)

- **Track A:** test MAE `hist_gradient_boosting=1.108903` vs `naive_mean=1.320011` (model better).
- **Track B:** ALL/test NDCG@10 `pointwise_percentile_regressor=0.917341` > `text_length_only=0.878155` > `review_stars_only=0.795782`.
- **Track C:** `significant_sentiment_city_count=21`, `significant_topic_city_count=39`, `mean_monitoring_change_score=0.166447`.
- **Track D (D1 ALL/test):** NDCG@10 `d1_pointwise_baseline=0.053397` vs `asof_popularity_baseline=0.050816`.

## Failure Signals

- Any non-zero exit from integrated pytest or baseline chain.
- Missing rewritten bundles under `outputs/modeling/track_*/` after baseline rerun.
- Comparator regressions in metric ordering checks (Track A/B/D) or Track C monitoring counts collapsing to zero.
- Slice-level semantic script failing for reasons other than known T04-owned requirement/roadmap state updates.

## Requirements Proved By This UAT

- Runtime/contract execution evidence for Track A/B/C/D baseline bundles used by R005–R008 integration closure.
- Handoff doc hygiene from S02–S05 (non-placeholder UATs + non-empty summaries) as consumed by S06.

## Not Proven By This UAT

- Final requirement status text (`Status: validated` for R005–R008) and roadmap closure assertion in `.gsd` state files; these are completed under T04.

## Notes for Tester

If the semantic script from `S06-PLAN.md` fails with requirement-status assertions while runtime gates pass, inspect `.gsd/REQUIREMENTS.md` and `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md` before touching modeling code.