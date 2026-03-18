# Track E Code: What the Modules Do

> **Last updated:** 2026-03-17
> **Related commit:** Implement Track E fairness audit pipeline
> **Difficulty level:** Intermediate

## What You Need to Know First

- Read `../workflows/track_e_pipeline.md` first.
- Read `src/eda/track_e/CLAUDE.md` for the hard rules the modules share.

## The Big Picture

Track E is organized as a small pipeline package under `src/eda/track_e/`.

Each file owns one stage or a set of shared helpers. The design keeps stage logic narrow so interns can inspect one concern at a time.

## Module Map

### `common.py`

Shared Track E helpers:

- path resolution with `TrackEPaths`
- output-directory setup
- parquet writing with banned-column guards
- minimum group-size filtering
- placeholder figure creation

### `subgroup_definition.py`

Stage 1. Builds the business-to-subgroup mapping and writes:

- `track_e_s1_subgroup_definitions.parquet`
- `track_e_s1_subgroup_summary.parquet`
- `track_e_s1_price_tier_diagnostic.parquet`

### `coverage_profile.py`

Stage 2. Aggregates review/business/user coverage by subgroup and renders the main coverage bar charts.

### `star_disparity.py`

Stage 3. Computes star-summary statistics, KS test comparisons, and Simpson's paradox flags.

### `usefulness_disparity.py`

Stage 4. Summarizes useful-vote patterns and flags visibility deserts.

### `imbalance_analysis.py`

Stage 5. Computes Gini coefficients, top-share/bottom-share concentration metrics, and Lorenz-curve figures.

### `proxy_risk.py`

Stage 6. Builds `_asof` business features and correlates them with subgroup indicators to identify proxy-risk signals.

### `fairness_baseline.py`

Stage 7. Converts previous stage outputs into data-level fairness metrics.

### `mitigation_candidates.py`

Stage 8. Produces the mitigation markdown brief tied to evidence from Stages 5-7.

### `summary_report.py`

Stage 9. Generates the final summary markdown and logs the soft validity scan.

## Testing

- Track E regression tests live in `tests/test_track_e_*.py`.
- Helper regressions from the Track D promotion live in `tests/test_common_helpers_promoted.py` and `tests/test_track_d_import_migration.py`.
- Every stage module is expected to remain importable outside the dispatcher and expose `run(config: dict)`.
