---
id: track_a_planning
title: Track A Planning — Future Star Rating Prediction
version: "2026-03-18"
scope: track
tags: [track-a, star-rating, temporal-split, leakage, planning, pipeline-spec]

cross_dependencies:
  reads:
    - CoWork Planning/yelp_project/02_EDA_Pipeline_Track_A_Future_Ratings.md
    - CoWork Planning/yelp_project/track_a/AGENTS.md
    - configs/track_a.yaml
    - data/curated/review_fact.parquet
  writes:
    - outputs/tables/track_a_s1_temporal_profile.parquet
    - outputs/tables/track_a_s8_eda_summary.md
    - outputs/logs/track_a_s6_leakage_audit.log
  siblings: [root, src_eda_track_a]

toc:
  - section: "What This Is"
    anchor: "#what-this-is"
  - section: "Your Task"
    anchor: "#your-task"
  - section: "Quick Reference"
    anchor: "#quick-reference"
---

# Track A — Claude Code Context: Future Star Rating Prediction

## What This Is

Track A of a Yelp Open Dataset semester project. The goal is exploratory data analysis for a **star rating prediction** task with strict temporal evaluation.

## Your Task

Implement the 8-stage EDA pipeline defined in `02_EDA_Pipeline_Track_A_Future_Ratings.md`. Read that file for the full specification. Read `AGENTS.md` for agent responsibilities and constraints.

## Quick Reference

**Framing question:** Can review text, user history, and business attributes predict future star ratings under strict time-split?

**Pipeline stages:**
1. Temporal profile — star distributions over time
2. Text profile — length and sentiment proxy stats
3. User history profile — as-of history depth
4. Business attribute profile — attribute completeness
5. Split selection — choose T₁/T₂ cutoffs
6. Leakage audit — flag pre-aggregated and future-leaking features
7. Feature availability matrix — coverage report
8. Summary report — consolidated markdown

**Data input:** Track A reads `data/curated/review_fact.parquet` exclusively. Track A must never read from `review_fact_track_b.parquet` or the DuckDB view `review_fact_track_b`.

**Banned fields (snapshot-only / lifetime aggregates):**
The following fields are banned from the Track A base table and from Track A feature construction unless an explicitly as-of version is computed:
- `business.stars`
- `business.review_count`
- `business.is_open`
- `user.average_stars`
- `user.review_count`
- `user.fans`
- `user.elite`

**Direct-join constraint:** Track A stages that read raw entity Parquet files (e.g., `review.parquet` for text sampling in Stage 2) must not join or extract banned snapshot-only fields from any source. The ban applies regardless of whether the field is accessed via `review_fact_track_b.parquet`, raw entity files, or DuckDB views. Leakage audits must verify both output column names and code-level query paths.

**Critical rules:**
- All features must be as-of (no future data leakage).
- All Track A history features must use strictly earlier dates only. Do not invent same-day ordering with `review_id` or any other surrogate.
- First-review rows are identified by `user_prior_review_count = 0`, with bucket label `0 (first review)`.
- Outputs are aggregate-only. No raw review text in figures or tables.
- Config lives in `configs/track_a.yaml`. Shared config in `configs/base.yaml`.

**Tech stack:** Python, Pandas/Polars, Parquet, matplotlib/seaborn, CLI entry points via `python -m`.

**Depends on shared stages:** `src.ingest.load_yelp_json`, `src.validate.schema_checks`, `src.curate.build_review_fact`.
