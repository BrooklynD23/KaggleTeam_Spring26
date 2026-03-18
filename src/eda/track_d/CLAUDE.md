---
id: src_eda_track_d
title: Track D EDA Implementation Context
version: "2026-03-18"
scope: track
tags: [track-d, cold-start, eda, recommender, leakage, audit]
cross_dependencies:
  reads:
    - configs/track_d.yaml
    - data/curated/review_fact.parquet
    - data/curated/business.parquet
    - data/curated/user.parquet
    - data/curated/checkin_expanded.parquet
    - data/curated/tip.parquet
  writes:
    - outputs/tables/track_d_*.parquet
    - outputs/figures/track_d_*.png
    - outputs/logs/track_d_*.log
  siblings: [src_eda, track_d_planning, track_a_planning]
toc:
  - section: "What This Covers"
    anchor: "#what-this-covers"
  - section: "Stage Map"
    anchor: "#stage-map"
  - section: "Critical Rules"
    anchor: "#critical-rules"
  - section: "CLI Pattern"
    anchor: "#cli-pattern"
---

# Track D — Cold-Start Recommender

## What This Covers

Track D implements the cold-start EDA pipeline for two separate subtracks:

- `D1`: business cold start
- `D2`: user cold start

## Stage Map

1. `business_lifecycle.py`
2. `business_cold_start.py`
3. `business_early_signals.py`
4. `popularity_baseline.py`
5. `user_cold_start.py`
6. `user_warmup_profile.py`
7. `evaluation_cohorts.py`
8. `leakage_check.py`
9. `summary_report.py`

## Critical Rules

- Keep D1 and D2 separate in tables, metrics, and summaries.
- Define cold start strictly from information available before `as_of_date`.
- Never use lifetime snapshot fields like `business.stars`, `business.review_count`, `business.is_open`, `user.average_stars`, `user.review_count`, `user.fans`, or `user.elite` as features.
- Candidate sets for D2 must exclude businesses already reviewed before the evaluation point.
- Stage 8 is a hard gate and must raise on `FAIL`.

## CLI Pattern

```bash
python -m src.eda.track_d.<stage> --config configs/track_d.yaml
```
