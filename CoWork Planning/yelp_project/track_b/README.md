# Track B README

## Focus

Track B studies snapshot usefulness ranking, not future usefulness prediction.

Primary question:

> At a fixed Yelp dataset snapshot, which reviews are comparatively more useful within the same business or category after controlling for review age?

## Current Status

- Planning folder exists and is set up.
- Implementation code exists in `src/eda/track_b/`.
- Shared curated dependencies: `data/curated/review_fact_track_b.parquet` and `data/curated/snapshot_metadata.json`.
- Expected Track B outputs are defined, but no `outputs/track_b_*` artifacts are currently checked into the repo.

## Key Documents

- [Track B pipeline spec](03_EDA_Pipeline_Track_B_Usefulness_Ranking.md)
- [Track B agent guide](AGENTS.md)
- [Track B Claude context](CLAUDE.md)
- [Top-level repo README](../../../README.md)

## Implementation Footprint

Current Track B modules:

- `src/eda/track_b/usefulness_distribution.py`
- `src/eda/track_b/age_confounding.py`
- `src/eda/track_b/ranking_group_analysis.py`
- `src/eda/track_b/label_construction.py`
- `src/eda/track_b/feature_correlates.py`
- `src/eda/track_b/training_feasibility.py`
- `src/eda/track_b/leakage_scope_check.py`
- `src/eda/track_b/summary_report.py`

## Deliverables

Track B is expected to produce:

- Stage tables under `outputs/tables/track_b_*`
- Stage figures under `outputs/figures/track_b_*`
- Leakage and scope logs under `outputs/logs/track_b_*`
- Final summary markdown at `outputs/tables/track_b_s8_eda_summary.md`

## Current Gaps

- No committed curated data yet.
- No committed Track B output artifacts yet.
- Track B execution still depends on the shared pipeline running first.
