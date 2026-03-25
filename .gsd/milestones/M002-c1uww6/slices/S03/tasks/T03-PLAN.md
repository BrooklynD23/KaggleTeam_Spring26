---
estimated_steps: 4
estimated_files: 5
skills_used:
  - verification-loop
  - debug-like-expert
  - article-writing
---

# T03: Verify held-out ranking quality and freeze the Track B handoff summary

**Slice:** S03 — Track B snapshot ranking baseline
**Milestone:** M002-c1uww6

## Description

Close the slice by running the Track B verification loop against the new runtime outputs, proving the model beats the trivial comparators on held-out ranking quality, and tightening the summary/config wording so downstream slices can consume the artifacts without re-deriving scope guardrails.

## Steps

1. Run the Track B helper tests plus the relevant upstream Track B regression suites and rerun the baseline CLI entrypoint.
2. Confirm the Track B artifact bundle exists, especially `scores_test.parquet`, and inspect `metrics.csv` for held-out `ALL` NDCG@10 and Recall@10 behavior.
3. Update `summary.md` and, if needed, the config snapshot/entrypoint wording so snapshot framing, group split strategy, banned features, comparators, and the pointwise-only M002 scope ceiling are explicit.
4. Re-run the verification commands after any wording or runtime fixes.

## Must-Haves

- [ ] The held-out `ALL` test NDCG@10 for `pointwise_percentile_regressor` beats both trivial comparators.
- [ ] The summary names snapshot framing, grouping logic, banned features, comparators, and the pointwise scope ceiling.
- [ ] The final verification suite passes with the artifact bundle present under `outputs/modeling/track_b/`.

## Verification

- `python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py`
- `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
- `python - <<'PY'
import pandas as pd
metrics = pd.read_csv('outputs/modeling/track_b/metrics.csv')
model_ndcg = metrics.loc[(metrics.model_name == 'pointwise_percentile_regressor') & (metrics.split_name == 'test') & (metrics.age_bucket == 'ALL'), 'ndcg_at_10'].iloc[0]
text_ndcg = metrics.loc[(metrics.model_name == 'text_length_only') & (metrics.split_name == 'test') & (metrics.age_bucket == 'ALL'), 'ndcg_at_10'].iloc[0]
stars_ndcg = metrics.loc[(metrics.model_name == 'review_stars_only') & (metrics.split_name == 'test') & (metrics.age_bucket == 'ALL'), 'ndcg_at_10'].iloc[0]
assert model_ndcg > text_ndcg > stars_ndcg, (model_ndcg, text_ndcg, stars_ndcg)
print('track_b model beats both trivial comparators on held-out ALL NDCG@10')
PY`

## Observability Impact

- Signals added/changed: the final `outputs/modeling/track_b/metrics.csv`, `outputs/modeling/track_b/summary.md`, `outputs/modeling/track_b/config_snapshot.json`, and `outputs/modeling/track_b/scores_test.parquet`
- How a future agent inspects this: rerun the pytest + CLI commands above, then inspect the Track B artifact bundle for summary wording and metric regressions
- Failure state exposed: comparator regressions, missing scored outputs, or summary contract drift become visible via the explicit metric assertion and summary/config checks

## Inputs

- `src/modeling/track_b/baseline.py` — Track B baseline runtime to verify
- `tests/test_track_b_baseline_model.py` — Track B helper regression suite
- `tests/test_label_scheme_ranking.py` — upstream Stage 4 label-selection regression suite
- `tests/test_feasibility_signoff.py` — upstream Stage 6 feasibility regression suite
- `tests/test_m002_modeling_contract.py` — shared modeling scaffold contract checks
- `outputs/modeling/track_b/metrics.csv` — Track B ranking metrics to validate
- `outputs/modeling/track_b/config_snapshot.json` — Track B run context to validate
- `outputs/modeling/track_b/summary.md` — Track B handoff summary to tighten
- `outputs/modeling/track_b/scores_test.parquet` — Track B held-out scored output to confirm exists

## Expected Output

- `outputs/modeling/track_b/summary.md` — finalized Track B handoff summary
- `outputs/modeling/track_b/metrics.csv` — verified Track B ranking metrics
- `outputs/modeling/track_b/config_snapshot.json` — verified Track B run context
- `outputs/modeling/track_b/scores_test.parquet` — verified Track B scored output artifact
- `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png` — verified Track B diagnostic figure
