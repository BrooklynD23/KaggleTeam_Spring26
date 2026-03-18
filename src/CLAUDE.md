---
id: src
title: src/ — Python Source Package Overview
version: "2026-03-18"
scope: src
tags: [source, packages, pipeline, module-layout, dependency-order]

cross_dependencies:
  reads:
    - configs/base.yaml
    - configs/track_a.yaml
    - configs/track_b.yaml
  writes: []
  siblings: [root]

toc:
  - section: "Package Layout"
    anchor: "#package-layout"
  - section: "Dependency Order"
    anchor: "#dependency-order"
  - section: "Module Loading Rules"
    anchor: "#module-loading-rules"
  - section: "Sub-Package Contexts"
    anchor: "#sub-package-contexts"
---

# src/ — Python Source Package Overview

This directory contains all pipeline source code. Load this file before loading any sub-package CLAUDE.md.

## Package Layout

```
src/
├── __init__.py
├── common/
│   ├── artifacts.py      ← artifact path helpers shared by all stages
│   └── config.py         ← config loading utility (reads configs/*.yaml)
├── ingest/
│   ├── load_yelp_json.py         ← tar extraction + DuckDB load
│   └── validate_json_structure.py ← structural checks before loading
├── validate/
│   └── schema_checks.py  ← post-load schema contract enforcement
├── curate/
│   └── build_review_fact.py ← materializes shared curated parquet tables
└── eda/
    ├── track_a/          ← 8-stage Track A EDA pipeline
    └── track_b/          ← 8-stage Track B EDA pipeline (+ common.py)
```

## Dependency Order

Packages must be consumed in this order. A downstream package **must not** be run before all its upstream dependencies have succeeded.

```
src.ingest
    └─▶ src.validate
            └─▶ src.curate
                    └─▶ src.eda.track_a
                    └─▶ src.eda.track_b
```

`src.common` is a utility layer with no pipeline dependencies — it can be imported by any package.

## Module Loading Rules

- All CLI entry points use `python -m src.<module>` or go through `scripts/run_pipeline.py` (launcher) / `scripts/pipeline_dispatcher.py` (execution engine).
- Config is always loaded via `src.common.config` — never hardcode paths.
- Output paths are resolved via `src.common.artifacts` helpers.
- Each stage writes to `outputs/` only. Never write back to `data/raw/` or `data/curated/` except in `src.curate`.

## Sub-Package Contexts

| Package | CLAUDE.md id | Key responsibility |
|---|---|---|
| `src.ingest` | `src_ingest` | Extract tar → NDJSON → DuckDB |
| `src.validate` | `src_validate` | Schema contracts before curation |
| `src.curate` | `src_curate` | Materialize shared parquet artifacts |
| `src.eda` | `src_eda` | EDA parent context |
| `src.eda.track_a` | `src_eda_track_a` | 8-stage Track A EDA |
| `src.eda.track_b` | `src_eda_track_b` | 8-stage Track B EDA |
