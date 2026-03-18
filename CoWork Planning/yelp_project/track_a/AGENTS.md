# Track A — Agent Configuration: Future Star Rating Prediction

## Agent Purpose

This agent implements the EDA pipeline for **Track A: predicting future star ratings under strict time-split evaluation**. It is a data engineering and exploratory analysis agent — it does not train models.

## Context

You are working on a semester-scale data science project using the **Yelp Open Dataset**. Track A asks: *How well can review text, user history, and business attributes predict future star ratings under strict time-split evaluation?*

Your job is to execute the EDA pipeline defined in `02_EDA_Pipeline_Track_A_Future_Ratings.md` in this directory. Read that file first for the full specification.

## Agent Responsibilities

1. **Read** the `review_fact.parquet` curated table produced by the main agent's shared pipeline (ingestion, validation, and curation are main-agent-owned; see `src/ingest/*`, `src/validate/*`, `src/curate/*`).
2. **Profile** star distributions over time, text characteristics, user history depth, and business attribute completeness.
3. **Select** temporal split cutoffs (T₁, T₂) based on volume and distribution analysis.
4. **Audit** for target leakage across the full banned-field set and direct-query paths, not just output column names.
5. **Produce** a feature availability matrix and summary EDA report.

> **Note:** Shared ingestion, validation, and curation pipelines are owned by the main agent. Track A focuses exclusively on `src/eda/track_a/*`, `outputs/tables/track_a_*`, `outputs/figures/track_a_*`, and `outputs/logs/track_a_*`, and must not modify shared pipeline code.

## Key Constraints

- **Track A input contract**: read `data/curated/review_fact.parquet` only. Track A must never read `data/curated/review_fact_track_b.parquet` or query the DuckDB view `review_fact_track_b`.
- **Strict as-of semantics**: every feature computed for a review at time *t* must use only data available on strictly earlier dates.
- **Same-day rule**: the Yelp dataset exposes dates, not timestamps. Do not fabricate same-day ordering using `review_id` or any other surrogate. Aggregate to user-day and business-day, lag by one full day, then attach the same prior-history values to all reviews on that date.
- **Banned snapshot-only and lifetime fields**: `business.stars`, `business.review_count`, `business.is_open`, `user.average_stars`, `user.review_count`, `user.fans`, and `user.elite` must not be used unless an explicitly as-of version is computed.
- **Direct-join constraint**: if a stage reads raw entity Parquet files, it must not join or extract banned fields from any source, including raw entity files, `review_fact_track_b.parquet`, or DuckDB views.
- **First-review bucketing**: identify first-review rows with `user_prior_review_count = 0` and label that bucket `0 (first review)`. Do not rely on `IS NULL`.
- **No raw review text in outputs**: all text analysis uses aggregate statistics (length, sentiment score distributions), never raw text display.
- **CLI-first**: all stages are runnable as `python -m src.eda.track_a.<stage> --config configs/track_a.yaml`.
- **Leakage zero-tolerance**: the leakage audit must flag zero rows before EDA is considered done.

## Data Entities Needed

- `review` — central fact table (stars, date, text, user_id, business_id)
- `business` — dimensions (city, state, categories, attributes); banned snapshot-only fields remain off-limits unless re-derived as-of
- `user` — dimensions (yelping_since); lifetime aggregates and snapshot fields are banned unless re-derived as-of
- `tip`, `checkin` — supplementary temporal signals

## Output Directory

All outputs go to:
- `outputs/tables/track_a_*.parquet`
- `outputs/figures/track_a_*.png`
- `outputs/logs/track_a_*.log`

## Completion Signal

EDA is done when all exit criteria in the pipeline spec are met and `outputs/tables/track_a_s8_eda_summary.md` exists.
