---
id: src_eda_track_b
title: src/eda/track_b — Track B EDA Implementation (Snapshot Usefulness Ranking)
version: "2026-03-18"
scope: track
tags: [track-b, usefulness-ranking, snapshot, age-control, learning-to-rank, eda]

cross_dependencies:
  reads:
    - data/curated/review_fact_track_b.parquet
    - data/curated/snapshot_metadata.json
    - configs/base.yaml
    - configs/track_b.yaml
    - CoWork Planning/yelp_project/track_b/CLAUDE.md
  writes:
    - outputs/tables/track_b_s1_usefulness_distribution.parquet
    - outputs/tables/track_b_s2_age_confounding.parquet
    - outputs/tables/track_b_s3_ranking_group_analysis.parquet
    - outputs/tables/track_b_s4_label_construction.parquet
    - outputs/tables/track_b_s5_feature_correlates.parquet
    - outputs/tables/track_b_s6_training_feasibility.md
    - outputs/logs/track_b_s7_leakage_scope_check.log
    - outputs/tables/track_b_s8_eda_summary.md
    - outputs/figures/track_b_s1_*.png
    - outputs/figures/track_b_s2_*.png
  siblings: [src_eda, track_b_planning]

toc:
  - section: "What This Package Does"
    anchor: "#what-this-package-does"
  - section: "Pipeline Stages"
    anchor: "#pipeline-stages"
  - section: "Stage Module Map"
    anchor: "#stage-module-map"
  - section: "Critical Rules"
    anchor: "#critical-rules"
  - section: "CLI Usage"
    anchor: "#cli-usage"
---

# src/eda/track_b — Track B EDA Implementation (Snapshot Usefulness Ranking)

## What This Package Does

Implements the 8-stage EDA pipeline for **Track B: Snapshot Usefulness Ranking** — a single-snapshot, age-controlled learning-to-rank task. Reads only `data/curated/review_fact_track_b.parquet` and `data/curated/snapshot_metadata.json`.

**Framing question:** At a fixed dataset snapshot, can we rank comparatively useful reviews after controlling for review age?

## Pipeline Stages

| Stage | Name | Module | Output |
|---|---|---|---|
| S1 | Usefulness vote distribution | `usefulness_distribution.py` | Vote count distributions by category |
| S2 | Age confounding analysis | `age_confounding.py` | Vote accumulation vs. review age |
| S3 | Ranking group analysis | `ranking_group_analysis.py` | Group definition and sizing |
| S4 | Label construction | `label_construction.py` | Snapshot-safe binary/ordinal labels |
| S5 | Feature–usefulness correlates | `feature_correlates.py` | Feature correlation within age buckets |
| S6 | Training feasibility | `training_feasibility.py` | Pairwise/listwise feasibility report |
| S7 | Leakage and scope check | `leakage_scope_check.py` | Scans outputs for prohibited temporal claims |
| S8 | Summary report | `summary_report.py` | Consolidated markdown EDA summary |

## Stage Module Map

```
src/eda/track_b/
├── __init__.py
├── common.py                 ← shared helpers (snapshot date loading, age buckets)
├── usefulness_distribution.py
├── age_confounding.py
├── ranking_group_analysis.py
├── label_construction.py
├── feature_correlates.py
├── training_feasibility.py
├── leakage_scope_check.py
└── summary_report.py
```

## Critical Rules

- **`useful` is the target.** Do NOT use `funny` or `cool` as features — they are simultaneous-observation leakage columns.
- **Single-snapshot task.** Do not infer vote growth curves, stabilization windows, or `useful_at_t`.
- **Never re-infer the snapshot date.** Read `snapshot_reference_date` from `snapshot_metadata.json` via `common.py`.
- **Exposure-time bias** is the #1 confounder. Age control is mandatory in every group analysis.
- **Ranking groups** are business-first with category fallback, always within age buckets.
- **Pairwise feasibility formula:** `valid_pairs = C(n, 2) − tied_pairs` (ties computed from raw `useful` within each ranking group).
- **Stage 7** must also scan `outputs/tables/track_b_*` and `outputs/logs/track_b_*` for prohibited temporal language.
- All outputs are aggregate-only. No raw review text.

## CLI Usage

```bash
python scripts/run_pipeline.py --approach track_b
# or run individual stages:
python -m src.eda.track_b.usefulness_distribution
python -m src.eda.track_b.leakage_scope_check
```
