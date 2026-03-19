---
id: track_c_planning
title: Track C Planning — Sentiment and Topic Drift
version: "2026-03-18"
scope: track
tags: [track-c, sentiment, topic-drift, nlp, geo-temporal, planning]

cross_dependencies:
  reads:
    - CoWork Planning/yelp_project/04_EDA_Pipeline_Track_C_Sentiment_Topic_Drift.md
    - CoWork Planning/yelp_project/track_c/AGENTS.md
    - data/curated/review_fact.parquet
    - data/curated/review.parquet
    - data/curated/business.parquet
  writes:
    - outputs/tables/track_c_*.parquet
    - outputs/figures/track_c_*.png
    - outputs/logs/track_c_*.log
  siblings: [root, src_eda]

toc:
  - section: "What This Is"
    anchor: "#what-this-is"
  - section: "Your Task"
    anchor: "#your-task"
  - section: "Quick Reference"
    anchor: "#quick-reference"
---

# Track C — Claude Code Context: Sentiment and Topic Drift

## What This Is

Track C of a Yelp Open Dataset semester project. The goal is EDA for **geo-temporal sentiment and topic drift analysis** across cities.

## Your Task

Implement the 9-stage EDA pipeline defined in `04_EDA_Pipeline_Track_C_Sentiment_Topic_Drift.md`. Read that file for full spec. Read `AGENTS.md` for constraints.

## Quick Reference

**Framing question:** How does sentiment/topic prevalence shift over time across cities, and what events correlate?

**Pipeline stages:**
1. Geographic coverage mapping
2. Temporal bin definition
3. Text normalization profiling
4. Sentiment baseline computation
5. Topic/keyword prevalence analysis
6. Drift detection (city × period)
7. Event and business change candidates
8. Check-in volume correlation
9. Summary report

**Critical rules:**
- All geographic outputs use city/neighborhood aggregation — never individual reviews publicly.
- Minimum review count per bin before computing aggregates (avoid small-sample noise).
- Include closed businesses in temporal analysis to avoid survivorship bias.
- Validate sentiment proxy against stars (Spearman > 0.3 expected).
- Keyword list should be domain-relevant and temporally appropriate.

**Tech stack:** Python, Pandas/Polars, TextBlob or VADER, TF-IDF (scikit-learn), Parquet, matplotlib/seaborn, CLI entry points.

**Depends on shared stages:** `src.ingest.load_yelp_json`, `src.validate.schema_checks`, `src.curate.build_review_fact`.
