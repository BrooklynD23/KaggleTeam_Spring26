---
id: track_d_planning
title: Track D Planning — Cold-Start Recommender
version: "2026-03-18"
scope: track
tags: [track-d, cold-start, recommender, temporal-split, planning]

cross_dependencies:
  reads:
    - CoWork Planning/yelp_project/05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md
    - CoWork Planning/yelp_project/track_d/AGENTS.md
    - configs/base.yaml
    - data/curated/review_fact.parquet
    - data/curated/business.parquet
  writes:
    - outputs/tables/track_d_*.parquet
    - outputs/figures/track_d_*.png
    - outputs/logs/track_d_*.log
  siblings: [root, src_eda, track_a_planning]

toc:
  - section: "What This Is"
    anchor: "#what-this-is"
  - section: "Your Task"
    anchor: "#your-task"
  - section: "Quick Reference"
    anchor: "#quick-reference"
---

# Track D — Claude Code Context: Cold-Start Recommender

## What This Is

Track D of a Yelp Open Dataset semester project. The goal is EDA for **two separate cold-start recommendation tasks** — D1 business cold start and D2 user cold start — each compared against as-of popularity baselines.

## Your Task

Implement the 9-stage EDA pipeline defined in `05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md`. Read that file for full spec. Read `AGENTS.md` for constraints.

## Quick Reference

**Framing question:** Can separate business-cold-start and user-cold-start recommenders outperform explicit as-of popularity baselines without post-hoc leakage?

**Pipeline stages:**
1. Business lifecycle and review accrual curves
2. D1 business cold-start cohort construction
3. D1 business early-signal catalog
4. As-of popularity baseline construction
5. D2 user cold-start cohort construction
6. D2 user warm-up profile and feature coverage
7. D1/D2 evaluation cohort construction (within temporal splits)
8. Leakage check
9. Summary report

**Critical rules:**
- Define "new" **temporally** — never use lifetime aggregates for newness.
- Do NOT use lifetime `business.stars`, lifetime `business.review_count`, or post-hoc outcome fields.
- Only features that exist at cold-start time are valid.
- Uses Track A's temporal splits (T₁, T₂) from `configs/base.yaml`.
- D1 and D2 must be reported separately in every table and summary.

**Tech stack:** Python, Pandas/Polars, Parquet, matplotlib/seaborn, CLI entry points.

**Depends on shared stages:** `src.ingest.load_yelp_json`, `src.validate.schema_checks`, `src.curate.build_review_fact`. Also depends on Track A's split definitions.
