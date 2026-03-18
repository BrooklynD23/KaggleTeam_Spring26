---
id: src_eda_track_a
title: src/eda/track_a — Track A EDA Implementation (Future Star Rating Prediction)
version: "2026-03-18"
scope: track
tags: [track-a, star-rating, temporal-split, leakage-audit, as-of-features, eda]

cross_dependencies:
  reads:
    - data/curated/review_fact.parquet
    - configs/base.yaml
    - configs/track_a.yaml
    - CoWork Planning/yelp_project/track_a/CLAUDE.md
  writes:
    - outputs/tables/track_a_s1_temporal_profile.parquet
    - outputs/tables/track_a_s2_text_profile.parquet
    - outputs/tables/track_a_s3_user_history_profile.parquet
    - outputs/tables/track_a_s4_business_attr_profile.parquet
    - outputs/tables/track_a_s5_split_selection.md
    - outputs/logs/track_a_s6_leakage_audit.log
    - outputs/tables/track_a_s7_feature_availability.parquet
    - outputs/tables/track_a_s8_eda_summary.md
    - outputs/figures/track_a_s1_*.png
    - outputs/figures/track_a_s2_*.png
  siblings: [src_eda, track_a_planning]

toc:
  - section: "What This Package Does"
    anchor: "#what-this-package-does"
  - section: "Pipeline Stages"
    anchor: "#pipeline-stages"
  - section: "Stage Module Map"
    anchor: "#stage-module-map"
  - section: "Banned Fields"
    anchor: "#banned-fields"
  - section: "Critical Rules"
    anchor: "#critical-rules"
  - section: "CLI Usage"
    anchor: "#cli-usage"
---

# src/eda/track_a — Track A EDA Implementation (Future Star Rating Prediction)

## What This Package Does

Implements the 8-stage EDA pipeline for **Track A: Future Star Rating Prediction** under strict temporal evaluation. Reads only `data/curated/review_fact.parquet`.

**Framing question:** Can review text, user history, and business attributes predict future star ratings under a strict time-split?

## Pipeline Stages

| Stage | Name | Module | Output |
|---|---|---|---|
| S1 | Temporal profile | `temporal_profile.py` | Star rating distributions over time |
| S2 | Text profile | `text_profile.py` | Review length and sentiment proxy stats |
| S3 | User history profile | `user_history_profile.py` | As-of user history depth per review |
| S4 | Business attribute profile | `business_attr_profile.py` | Attribute completeness across categories |
| S5 | Split selection | `split_selection.py` | T₁/T₂ temporal cutoffs with row counts |
| S6 | Leakage audit | `leakage_audit.py` | Flags banned field usage in code and outputs |
| S7 | Feature availability matrix | `feature_availability.py` | Coverage report across the selected splits |
| S8 | Summary report | `summary_report.py` | Consolidated markdown EDA summary |

## Stage Module Map

```
src/eda/track_a/
├── __init__.py
├── temporal_profile.py
├── text_profile.py
├── user_history_profile.py
├── business_attr_profile.py
├── split_selection.py
├── leakage_audit.py
├── feature_availability.py
└── summary_report.py
```

## Banned Fields

The following fields are banned from Track A feature construction unless an explicitly **as-of** version is computed:

- `business.stars`
- `business.review_count`
- `business.is_open`
- `user.average_stars`
- `user.review_count`
- `user.fans`
- `user.elite`

The ban applies regardless of whether the field is accessed via parquet files, raw entity files, or DuckDB views. Stage 6 (leakage audit) verifies both output column names and code-level query paths.

## Critical Rules

- All features must be **as-of** (strictly earlier dates only). Do not use same-day `review_id` ordering as a surrogate.
- First-review rows are identified by `user_prior_review_count = 0`, with bucket label `0 (first review)`.
- Never read from `review_fact_track_b.parquet`.
- All outputs are aggregate-only. No raw review text in figures or tables.

## CLI Usage

```bash
python scripts/run_pipeline.py --approach track_a
# or run individual stages:
python -m src.eda.track_a.temporal_profile
python -m src.eda.track_a.leakage_audit
```
