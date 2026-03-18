# Track A README

## Focus

Track A studies future star rating prediction under strict temporal and as-of constraints.

Primary question:

> How well can review text, user history, and business attributes predict future star ratings under strict time-split evaluation?

## Current Status

- Planning folder exists and is set up.
- Implementation code exists in `src/eda/track_a/`.
- Shared curated dependency: `data/curated/review_fact.parquet`.
- Expected stage outputs are defined, but no `outputs/track_a_*` artifacts are currently checked into the repo.

## Key Documents

- [Track A pipeline spec](02_EDA_Pipeline_Track_A_Future_Ratings.md)
- [Track A agent guide](AGENTS.md)
- [Track A Claude context](CLAUDE.md)
- [Top-level repo README](../../../README.md)

## Implementation Footprint

Current Track A modules:

- `src/eda/track_a/temporal_profile.py`
- `src/eda/track_a/text_profile.py`
- `src/eda/track_a/user_history_profile.py`
- `src/eda/track_a/business_attr_profile.py`
- `src/eda/track_a/split_selection.py`
- `src/eda/track_a/leakage_audit.py`
- `src/eda/track_a/feature_availability.py`
- `src/eda/track_a/summary_report.py`

## Deliverables

Track A is expected to produce:

- Stage tables under `outputs/tables/track_a_*`
- Stage figures under `outputs/figures/track_a_*`
- Leakage audit logs under `outputs/logs/track_a_*`
- Final summary markdown at `outputs/tables/track_a_s8_eda_summary.md`

## Current Gaps

- No committed curated data yet.
- No committed Track A output artifacts yet.
- Final execution still depends on shared ingestion and curation running successfully first.
