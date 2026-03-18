---
id: src_eda_track_c
title: Track C EDA Implementation Context
version: "2026-03-18"
scope: track
tags: [track-c, eda, sentiment, topic-drift, city-level, nlp]

cross_dependencies:
  reads:
    - configs/track_c.yaml
    - data/curated/review_fact.parquet
    - data/curated/review.parquet
    - data/curated/business.parquet
    - data/curated/checkin_expanded.parquet
  writes:
    - outputs/tables/track_c_*.parquet
    - outputs/figures/track_c_*.png
    - outputs/logs/track_c_*.log
  siblings: [src_eda, track_c_planning]

toc:
  - section: "What This Is"
    anchor: "#what-this-is"
  - section: "Stage Map"
    anchor: "#stage-map"
  - section: "Critical Rules"
    anchor: "#critical-rules"
---

# Track C EDA Implementation Context

## What This Is

Track C implements the city-level sentiment and topic drift EDA pipeline for the Yelp semester project.

## Stage Map

1. `geo_coverage.py`
2. `temporal_binning.py`
3. `text_normalization.py`
4. `sentiment_baseline.py`
5. `topic_prevalence.py`
6. `drift_detection.py`
7. `event_candidates.py`
8. `checkin_correlation.py`
9. `summary_report.py`

## Critical Rules

- Read raw text only from `review.parquet`.
- Restrict text stages with a semijoin against `review_fact.parquet` review IDs.
- Never persist raw text columns to parquet outputs.
- Use `city` and `state` only. Do not introduce neighborhood outputs.
- Keep the Stage 9 leak scan soft and documentation-oriented.
