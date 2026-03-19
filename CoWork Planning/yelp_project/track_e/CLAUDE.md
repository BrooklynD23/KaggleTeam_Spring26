---
id: track_e_planning
title: Track E Planning — Bias and Disparity
version: "2026-03-18"
scope: track
tags: [track-e, bias, disparity, fairness, audit, planning]

cross_dependencies:
  reads:
    - CoWork Planning/yelp_project/06_EDA_Pipeline_Track_E_Bias_Disparity.md
    - CoWork Planning/yelp_project/track_e/AGENTS.md
    - data/curated/review_fact.parquet
    - data/curated/business.parquet
  writes:
    - outputs/tables/track_e_*.parquet
    - outputs/figures/track_e_*.png
    - outputs/logs/track_e_*.log
  siblings: [root, src_eda]

toc:
  - section: "What This Is"
    anchor: "#what-this-is"
  - section: "Your Task"
    anchor: "#your-task"
  - section: "Quick Reference"
    anchor: "#quick-reference"
---

# Track E — Claude Code Context: Bias and Disparity

## What This Is

Track E of a Yelp Open Dataset semester project. The goal is EDA for a **fairness audit** — identifying bias and disparity patterns in ratings and recommendations.

## Your Task

Implement the 9-stage EDA pipeline defined in `06_EDA_Pipeline_Track_E_Bias_Disparity.md`. Read that file for full spec. Read `AGENTS.md` for constraints.

## Quick Reference

**Framing question:** What bias/disparity patterns exist across neighborhoods and categories, and how can models be corrected?

**Pipeline stages:**
1. Subgroup definition (geography, category, price tier)
2. Coverage profiling by subgroup
3. Star rating disparity analysis
4. Usefulness vote disparity analysis
5. Data imbalance measurement (Gini, concentration)
6. Proxy risk feature identification
7. Baseline fairness metrics computation
8. Mitigation candidate documentation
9. Summary report

**Critical rules:**
- **NO demographic inference** from names, text, or neighborhoods.
- All outputs are **aggregate-only** with minimum group size ≥ 10.
- No causal claims — document confounders, use careful language.
- Conduct at least one stratified check for Simpson's paradox.
- Price tier comes from `attributes.RestaurantsPriceRange2` — expect ≥ 30% null rate.

**Tech stack:** Python, Pandas/Polars, scipy (KS tests), Parquet, matplotlib/seaborn, CLI entry points.

**Depends on shared stages:** `src.ingest.load_yelp_json`, `src.validate.schema_checks`, `src.curate.build_review_fact`.
