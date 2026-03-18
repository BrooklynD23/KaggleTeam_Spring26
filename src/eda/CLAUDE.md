---
id: src_eda
title: src/eda — EDA Pipeline Parent Context
version: "2026-03-18"
scope: src
tags: [eda, exploratory-data-analysis, track-a, track-b, leakage, aggregate-only]

cross_dependencies:
  reads:
    - data/curated/review_fact.parquet
    - data/curated/review_fact_track_b.parquet
    - data/curated/snapshot_metadata.json
    - configs/track_a.yaml
    - configs/track_b.yaml
  writes:
    - outputs/tables/
    - outputs/figures/
    - outputs/logs/
  siblings: [src, src_curate]

toc:
  - section: "What This Package Does"
    anchor: "#what-this-package-does"
  - section: "Track Overview"
    anchor: "#track-overview"
  - section: "Shared EDA Rules"
    anchor: "#shared-eda-rules"
  - section: "Output Conventions"
    anchor: "#output-conventions"
---

# src/eda — EDA Pipeline Parent Context

## What This Package Does

Houses all Exploratory Data Analysis stage modules, organized into per-track sub-packages. This context covers rules shared by **all** EDA tracks.

**Upstream:** `src.curate` must have materialized all parquet artifacts.
**Downstream:** Outputs go to `outputs/tables/`, `outputs/figures/`, `outputs/logs/`.

## Track Overview

| Sub-package | CLAUDE.md id | Input parquet | Stages |
|---|---|---|---|
| `src.eda.track_a` | `src_eda_track_a` | `review_fact.parquet` | 8 |
| `src.eda.track_b` | `src_eda_track_b` | `review_fact_track_b.parquet` | 8 |
| `src.eda.track_e` | `src_eda_track_e` | `review_fact.parquet` + `business.parquet` + `user.parquet` | 9 |

Track A and Track B **never share** their primary parquet input. Cross-reading between tracks is a hard error.

## Shared EDA Rules

These apply to every stage in every track:

1. **No raw review text** in any output file (table, figure, log, or summary).
2. **All outputs are aggregate-only** — no individual review rows in deliverables.
3. **No future data leakage** — features must be available at the time of prediction.
4. **Config-driven paths** — read `configs/<track>.yaml` for all output paths. Never hardcode.
5. **CLI entry point pattern:** `python -m src.eda.<track>.<stage_module>` or via `scripts/run_pipeline.py` (launcher) / `scripts/pipeline_dispatcher.py` (execution engine).
6. **Idempotent stages** — re-running a stage must overwrite, not duplicate, its outputs.

## Output Conventions

| Output type | Path pattern | Description |
|---|---|---|
| Tables | `outputs/tables/<track>_s<N>_<name>.parquet` or `.md` | Stage N tabular deliverable |
| Figures | `outputs/figures/<track>_s<N>_<name>.png` | Stage N chart |
| Logs | `outputs/logs/<track>_s<N>_<name>.log` | Validation and audit logs |
| Summary | `outputs/tables/<track>_s8_eda_summary.md` | Final EDA report (Stage 8) |
