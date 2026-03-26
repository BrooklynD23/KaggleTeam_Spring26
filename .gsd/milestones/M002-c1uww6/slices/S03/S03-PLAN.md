# S03: Track B snapshot ranking baseline

**Goal:** Deliver a real Track B snapshot-only usefulness ranking baseline that scores reviews within age-controlled groups, writes the standard modeling artifact bundle, and documents the grouped evaluation contract clearly enough for downstream reporting.
**Demo:** Running the Track B baseline entrypoint writes `metrics.csv`, `config_snapshot.json`, `summary.md`, `scores_test.parquet`, and `figures/test_ndcg_by_age_bucket.png` under `outputs/modeling/track_b/`, and the held-out `ALL` test NDCG@10 beats both trivial comparators while preserving Track B snapshot guardrails.

## Must-Haves

- A reproducible Track B baseline entrypoint exists under `src/modeling/track_b/` and uses only snapshot-safe inputs plus the Stage 3/4/6 Track B handoff surfaces.
- Evaluation keeps whole ranking groups together, reports grouped NDCG@10 and Recall@10 by age bucket plus `ALL`, and stays explicitly pointwise for M002.
- The Track B artifact bundle under `outputs/modeling/track_b/` includes a scored-output artifact, config snapshot, summary, metrics, and diagnostic figure.
- The summary explicitly records snapshot framing, grouping logic, trivial comparators, banned features, and why pairwise/listwise learning remains out of scope for this slice.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_b.baseline --config configs/track_b.yaml && test -f outputs/modeling/track_b/summary.md && test -f outputs/modeling/track_b/metrics.csv && test -f outputs/modeling/track_b/config_snapshot.json && test -f outputs/modeling/track_b/scores_test.parquet && test -f outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`
- `python - <<'PY'
import pandas as pd
metrics = pd.read_csv('outputs/modeling/track_b/metrics.csv')
model_ndcg = metrics.loc[(metrics.model_name == 'pointwise_percentile_regressor') & (metrics.split_name == 'test') & (metrics.age_bucket == 'ALL'), 'ndcg_at_10'].iloc[0]
text_ndcg = metrics.loc[(metrics.model_name == 'text_length_only') & (metrics.split_name == 'test') & (metrics.age_bucket == 'ALL'), 'ndcg_at_10'].iloc[0]
stars_ndcg = metrics.loc[(metrics.model_name == 'review_stars_only') & (metrics.split_name == 'test') & (metrics.age_bucket == 'ALL'), 'ndcg_at_10'].iloc[0]
assert model_ndcg > text_ndcg > stars_ndcg, (model_ndcg, text_ndcg, stars_ndcg)
print('track_b model beats both trivial comparators on held-out ALL NDCG@10')
PY`
- `python - <<'PY'
import json
from pathlib import Path
summary = Path('outputs/modeling/track_b/summary.md').read_text(encoding='utf-8').lower()
config = json.loads(Path('outputs/modeling/track_b/config_snapshot.json').read_text(encoding='utf-8'))
required_phrases = [
    'snapshot',
    'group split strategy',
    'text_length_only',
    'review_stars_only',
    'review.funny',
    'review.cool',
    'pointwise',
]
for phrase in required_phrases:
    assert phrase in summary, phrase
assert config['target_label'] == 'within_group_percentile'
assert 'feature_columns' in config and config['feature_columns']
print('track_b summary/config expose snapshot guardrails, comparators, and target label')
PY`
- `python - <<'PY'
import subprocess
import sys
cmd = [sys.executable, '-m', 'src.modeling.track_b.baseline', '--config', 'configs/does_not_exist.yaml']
proc = subprocess.run(cmd, capture_output=True, text=True)
assert proc.returncode != 0
combined = f"{proc.stdout}\n{proc.stderr}".lower()
assert 'does_not_exist.yaml' in combined or 'no such file' in combined
print('track_b baseline exposes inspectable failure diagnostics for invalid config path')
PY`

## Observability / Diagnostics

- Runtime signals: `outputs/modeling/track_b/metrics.csv`, `outputs/modeling/track_b/config_snapshot.json`, `outputs/modeling/track_b/scores_test.parquet`, `outputs/modeling/track_b/summary.md`, and `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`
- Inspection surfaces: `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`, the Track B modeling output root, and `tests/test_track_b_baseline_model.py`
- Failure visibility: missing Stage 3/4/6 artifacts, group-split leakage, degenerate ranking metrics, or missing scored-output artifacts surface through the CLI run, pytest assertions, and metric comparisons against trivial baselines
- Redaction constraints: no raw review text, no future-usefulness reconstruction, and no banned `review.funny` / `review.cool` features in outputs or summaries

## Integration Closure

- Upstream surfaces consumed: `configs/track_b.yaml`, `data/curated/review_fact_track_b.parquet`, `data/curated/snapshot_metadata.json`, `outputs/tables/track_b_s3_group_sizes_by_business_age.parquet`, `outputs/tables/track_b_s3_group_sizes_by_category_age.parquet`, `outputs/tables/track_b_s4_label_candidates.parquet`, `outputs/tables/track_b_s4_label_scheme_summary.parquet`, `outputs/tables/track_b_s6_pairwise_stats.parquet`, `outputs/tables/track_b_s6_listwise_stats.parquet`
- New wiring introduced in this slice: `src/modeling/track_b/baseline.py`, Track B helper tests, and the Track B modeling artifact bundle under `outputs/modeling/track_b/`
- What remains before the milestone is truly usable end-to-end: Track C, Track D1, and integrated milestone verification in S04–S06

## Tasks

- [x] **T01: Implement the Track B baseline entrypoint and grouped artifact bundle** `est:1h 30m`
  - Why: S03 is blocked on real runtime code because `src/modeling/track_b/` currently lacks the entrypoint that turns the existing EDA handoff into reproducible ranking evidence.
  - Files: `src/modeling/track_b/baseline.py`, `outputs/modeling/track_b/summary.md`, `outputs/modeling/track_b/metrics.csv`, `outputs/modeling/track_b/config_snapshot.json`, `outputs/modeling/track_b/scores_test.parquet`, `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`
  - Do: Build a Track B baseline script that loads snapshot metadata and Stage 4 label candidates, joins snapshot-safe numeric features from `review_fact_track_b.parquet`, performs a deterministic whole-group split on `group_type|group_id|age_bucket`, fits a pointwise `HistGradientBoostingRegressor` on `within_group_percentile`, evaluates grouped ranking metrics plus trivial comparators, and writes the full artifact bundle including the missing scored-output artifact.
  - Verify: `python -m src.modeling.track_b.baseline --config configs/track_b.yaml && test -f outputs/modeling/track_b/scores_test.parquet && test -f outputs/modeling/track_b/metrics.csv`
  - Done when: Track B has a runnable baseline entrypoint and a complete modeling bundle under `outputs/modeling/track_b/` that includes grouped metrics, a scored-output parquet, a config snapshot, a summary, and a diagnostic figure.
- [x] **T02: Add regression tests for Track B split, comparator, and ranking metric helpers** `est:1h`
  - Why: The first Track B modeling slice needs deterministic coverage for pure helper logic so later edits do not silently break group integrity or metric computation.
  - Files: `tests/test_track_b_baseline_model.py`, `src/modeling/track_b/baseline.py`
  - Do: Add focused pytest coverage for deterministic group splitting, comparator scoring, grouped NDCG/Recall helper behavior, and any small artifact-summary helpers that can be verified without rerunning the full baseline.
  - Verify: `python -m pytest tests/test_track_b_baseline_model.py`
  - Done when: the core helper logic behind the Track B baseline fails loudly under pytest if group-level evaluation, comparator outputs, or ranking metrics drift.
- [x] **T03: Verify held-out ranking quality and freeze the Track B handoff summary** `est:45m`
  - Why: S03 is only complete if the runtime outputs are both correct and communicative enough for downstream M003/M004 work.
  - Files: `outputs/modeling/track_b/summary.md`, `outputs/modeling/track_b/metrics.csv`, `outputs/modeling/track_b/config_snapshot.json`, `outputs/modeling/track_b/scores_test.parquet`, `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`
  - Do: Run the Track B pytest + CLI verification suite, confirm the held-out `ALL` test NDCG@10 beats `text_length_only` and `review_stars_only`, and tighten the summary/config wording so snapshot framing, banned features, grouping logic, and the pointwise-only M002 scope ceiling are explicit.
  - Verify: `python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py && python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
  - Done when: the Track B baseline demonstrably clears the trivial-comparator ranking bar and the artifact bundle is ready for downstream narrative/reporting consumption without archaeology.

## Files Likely Touched

- `src/modeling/track_b/baseline.py`
- `tests/test_track_b_baseline_model.py`
- `outputs/modeling/track_b/summary.md`
- `outputs/modeling/track_b/metrics.csv`
- `outputs/modeling/track_b/config_snapshot.json`
- `outputs/modeling/track_b/scores_test.parquet`
- `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`
