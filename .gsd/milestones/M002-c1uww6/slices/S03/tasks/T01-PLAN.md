---
estimated_steps: 4
estimated_files: 6
skills_used:
  - coding-standards
  - backend-patterns
  - verification-loop
---

# T01: Implement the Track B baseline entrypoint and grouped artifact bundle

**Slice:** S03 — Track B snapshot ranking baseline
**Milestone:** M002-c1uww6

## Description

Turn the existing Track B EDA handoff into a runnable baseline entrypoint. This task creates the actual runtime code that loads the snapshot-safe inputs, preserves whole ranking groups during splitting, trains the pointwise baseline, and emits the standard modeling artifact bundle.

## Steps

1. Create `src/modeling/track_b/baseline.py` with the same outer structure as Track A: config loading, required-input checks, helper functions, run function, and CLI entrypoint.
2. Load `review_fact_track_b.parquet`, `snapshot_metadata.json`, and the Stage 4/6 Track B artifacts, then build a deterministic whole-group split keyed by `group_type|group_id|age_bucket`.
3. Train a pointwise `HistGradientBoostingRegressor` on `within_group_percentile`, compute grouped NDCG@10 and Recall@10 versus `text_length_only` and `review_stars_only`, and keep banned features out of the feature frame.
4. Write the full Track B artifact bundle under `outputs/modeling/track_b/`, including the missing scored-output parquet and a diagnostic figure.

## Must-Haves

- [ ] `src/modeling/track_b/baseline.py` is a runnable CLI entrypoint.
- [ ] The feature frame stays snapshot-safe and excludes `review.funny` and `review.cool`.
- [ ] The runtime writes `metrics.csv`, `config_snapshot.json`, `summary.md`, `scores_test.parquet`, and `figures/test_ndcg_by_age_bucket.png`.

## Verification

- `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
- `test -f outputs/modeling/track_b/summary.md && test -f outputs/modeling/track_b/metrics.csv && test -f outputs/modeling/track_b/config_snapshot.json && test -f outputs/modeling/track_b/scores_test.parquet && test -f outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`

## Observability Impact

- Signals added/changed: `outputs/modeling/track_b/metrics.csv`, `outputs/modeling/track_b/config_snapshot.json`, `outputs/modeling/track_b/scores_test.parquet`, `outputs/modeling/track_b/summary.md`, and `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png`
- How a future agent inspects this: rerun `python -m src.modeling.track_b.baseline --config configs/track_b.yaml` and inspect the generated bundle under `outputs/modeling/track_b/`
- Failure state exposed: missing Track B EDA artifacts, broken group splits, or empty metrics surface through CLI errors, absent artifact files, or malformed `metrics.csv`

## Inputs

- `configs/track_b.yaml` — Track B snapshot rules, labels, and quality thresholds
- `data/curated/review_fact_track_b.parquet` — snapshot-safe feature base for Track B
- `data/curated/snapshot_metadata.json` — canonical snapshot date and release tag
- `outputs/tables/track_b_s3_group_sizes_by_business_age.parquet` — qualifying business groups by age bucket
- `outputs/tables/track_b_s3_group_sizes_by_category_age.parquet` — qualifying fallback groups by age bucket
- `outputs/tables/track_b_s4_label_candidates.parquet` — primary Track B labels and group assignments
- `outputs/tables/track_b_s4_label_scheme_summary.parquet` — label-ranking evidence showing `within_group_percentile` is primary
- `outputs/tables/track_b_s6_pairwise_stats.parquet` — feasibility context for group reporting
- `outputs/tables/track_b_s6_listwise_stats.parquet` — listwise feasibility context for summary language

## Expected Output

- `src/modeling/track_b/baseline.py` — Track B baseline runtime entrypoint
- `outputs/modeling/track_b/summary.md` — Track B baseline summary
- `outputs/modeling/track_b/metrics.csv` — grouped ranking metrics and comparator results
- `outputs/modeling/track_b/config_snapshot.json` — resolved Track B run context
- `outputs/modeling/track_b/scores_test.parquet` — held-out scored ranking output
- `outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png` — Track B diagnostic figure
