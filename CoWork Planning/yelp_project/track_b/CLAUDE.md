---
id: track_b_planning
title: Track B Planning — Snapshot Usefulness Ranking
version: "2026-03-18"
scope: track
tags: [track-b, usefulness-ranking, snapshot, age-control, learning-to-rank, planning]

cross_dependencies:
  reads:
    - CoWork Planning/yelp_project/03_EDA_Pipeline_Track_B_Usefulness_Ranking.md
    - CoWork Planning/yelp_project/track_b/AGENTS.md
    - configs/track_b.yaml
    - data/curated/review_fact_track_b.parquet
    - data/curated/snapshot_metadata.json
  writes:
    - outputs/tables/track_b_s1_usefulness_distribution.parquet
    - outputs/tables/track_b_s8_eda_summary.md
    - outputs/logs/track_b_s7_leakage_scope_check.log
  siblings: [root, src_eda_track_b]

toc:
  - section: "What This Is"
    anchor: "#what-this-is"
  - section: "Your Task"
    anchor: "#your-task"
  - section: "Quick Reference"
    anchor: "#quick-reference"
---

# Track B — Claude Code Context: Usefulness Ranking

## What This Is

Track B of a Yelp Open Dataset semester project. The goal is EDA for a **snapshot, age-controlled learning-to-rank task** that surfaces comparatively useful reviews.

## Your Task

Implement the 8-stage EDA pipeline defined in `03_EDA_Pipeline_Track_B_Usefulness_Ranking.md`. Read that file for full spec. Read `AGENTS.md` for constraints.

## Quick Reference

**Framing question:** At a fixed dataset snapshot, can we rank comparatively useful reviews after controlling for review age?

**Pipeline stages:**
1. Usefulness vote distribution profiling
2. Review-age confounding analysis
3. Ranking group definition and sizing
4. Snapshot-safe label construction
5. Feature-usefulness analysis within age buckets
6. Pairwise/listwise training data feasibility
7. Leakage and scope check
8. Summary report

**Data input:** Track B reads `data/curated/review_fact_track_b.parquet` and `data/curated/snapshot_metadata.json`.

**Critical rules:**
- `useful` is the target. Do NOT use `funny`/`cool` as features; they are simultaneous-observation leakage columns and their appearance in generated label tables is a Stage 7 failure.
- This is a **single-snapshot** task. Do not infer vote growth curves, stabilization windows, or `useful_at_t`.
- Do not re-infer the snapshot date inside each stage. Read `snapshot_reference_date` from `snapshot_metadata.json`.
- Exposure-time bias is the #1 confounder. Age control is mandatory.
- Ranking groups are business-first with category fallback, always within age buckets.
- Pairwise feasibility uses `valid_pairs = C(n, 2) - tied_pairs`, with ties computed from raw `useful` within each ranking group.
- Stage 7 must also scan `outputs/tables/track_b_*` and `outputs/logs/track_b_*` for unsupported temporal claims using the prohibited regex list in the pipeline spec.
- Outputs are aggregate-only. No raw review text.

**Tech stack:** Python, Pandas/Polars, Parquet, matplotlib/seaborn, CLI entry points.

**Depends on shared stages:** `src.ingest.load_yelp_json`, `src.validate.schema_checks`, `src.curate.build_review_fact`.
