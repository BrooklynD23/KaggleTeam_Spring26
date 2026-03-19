# Track D README

## Focus

Track D studies recommendation under cold-start conditions, split into business cold start and user cold start.

Primary question:

> Can separate business-cold-start and user-cold-start recommenders outperform explicit as-of popularity baselines without using post-hoc information?

## Current Status

- Planning folder exists and is set up.
- Implementation folder exists under `src/eda/track_d/` with 9 EDA stages.
- Stage 7 (evaluation cohorts) uses bounded, deterministic construction with `evaluation.entity_cap_per_group` (default 10,000) to stay tractable on the Yelp dataset. D1 and D2 no longer use spill-heavy DuckDB joins.
- Track D depends on Track A Stage 5 split artifact; run Track A first.

## Key Documents

- [Track D pipeline spec](05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md)
- [Track D agent guide](AGENTS.md)
- [Track D Claude context](CLAUDE.md)
- [Top-level repo README](../../../README.md)

## Planned Implementation Area

When implementation starts, the expected code location is:

- `src/eda/track_d/`

## Expected Deliverables

Track D planning currently calls for:

- Business lifecycle and business cold-start cohort artifacts
- User cold-start cohort and warm-up profile artifacts
- As-of popularity baselines and evaluation cohorts
- Leakage checks for cold-start framing
- Final summary markdown report

## Current Gaps

- `track_d.leakage_check` (Stage 8) has a pre-existing hard-fail on `source::leakage_check.py::raw_json_read`; this is separate from the Stage 7 fix and blocks Stage 9 from running cleanly.
