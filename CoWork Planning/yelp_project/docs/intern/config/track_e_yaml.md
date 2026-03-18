# Config: `configs/track_e.yaml`

> **Last updated:** 2026-03-17
> **Related commit:** Add Track E configuration
> **Difficulty level:** Intermediate

## What You Need to Know First

- Read `../workflows/track_e_pipeline.md` first.

## The Big Picture

`configs/track_e.yaml` controls how strict the fairness audit is and which subgroup patterns the pipeline will surface.

Unlike Track A or Track D, these knobs do not define a prediction task. They define reporting thresholds, subgroup construction rules, and audit sensitivity.

## Section-by-Section

### `track`

- `name`
- `label`

These are metadata fields used by the dispatcher and logs.

### `subgroups`

- `min_group_size`: minimum size for any subgroup row that gets reported.
- `top_n_cities`: number of cities to emphasize in plots or pairwise comparisons.
- `min_city_reviews`: minimum review count for city-level focus.
- `category_aggregation`: currently `"primary"` so only the first category token is kept.
- `price_tier_labels`: maps Yelp price integers to readable labels.
- `price_tier_missing_label`: label used when price is unavailable.
- `review_volume_tier_boundaries`: defines buckets such as `<10`, `10-50`, `50+`.

### `disparity`

- `ks_test_significance`: p-value threshold used in Stage 3 KS testing.
- `min_pairwise_comparisons`: warning threshold for how many KS comparisons Stage 3 should produce.

### `imbalance`

- `gini_top_pct`
- `gini_bottom_pct`

These define how Stage 5 computes top-share and bottom-share concentration summaries.

### `proxy`

- `correlation_threshold`: minimum absolute point-biserial correlation required before a feature is flagged as proxy risk.
- `candidate_features`: numeric `_asof` features tested in Stage 6.

### `fairness`

- `demographic_parity_threshold`: threshold for star/useful parity gaps.
- `coverage_parity_min_ratio`: minimum acceptable minority/majority review-count ratio.

### `simpson`

- `enabled`: whether Stage 3 performs the Simpson's paradox check.
- `conditioning_variable`: subgroup column used for the conditioned comparison.

### `quality`

- `min_price_tier_coverage`: warning threshold for Stage 1 price-tier coverage.
- `min_subgroup_dimensions`: warning threshold for how many subgroup dimensions must be populated.
- `min_ks_comparisons`: expected minimum number of KS comparisons.

## Try It Yourself

Run one stage with the config:

```bash
python -m src.eda.track_e.coverage_profile --config configs/track_e.yaml
```
