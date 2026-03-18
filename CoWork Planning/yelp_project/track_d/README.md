# Track D README

## Focus

Track D studies recommendation under cold-start conditions, split into business cold start and user cold start.

Primary question:

> Can separate business-cold-start and user-cold-start recommenders outperform explicit as-of popularity baselines without using post-hoc information?

## Current Status

- Planning folder exists and is set up.
- No implementation folder exists yet under `src/eda/track_d/`.
- This track is currently documentation-only inside the repo.

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

- No code modules yet.
- No track-specific config file yet.
- No output artifacts yet.
