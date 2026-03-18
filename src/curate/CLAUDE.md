---
id: src_curate
title: src/curate — Shared Curated Table Construction
version: "2026-03-18"
scope: src
tags: [curate, parquet, review-fact, shared-layer, curation]

cross_dependencies:
  reads:
    - data/yelp.duckdb
    - configs/base.yaml
  writes:
    - data/curated/review_fact.parquet
    - data/curated/review_fact_track_b.parquet
    - data/curated/review.parquet
    - data/curated/business.parquet
    - data/curated/snapshot_metadata.json
  siblings: [src, src_validate, src_eda]

toc:
  - section: "What This Package Does"
    anchor: "#what-this-package-does"
  - section: "Files"
    anchor: "#files"
  - section: "Curated Artifacts"
    anchor: "#curated-artifacts"
  - section: "Track Ownership"
    anchor: "#track-ownership"
  - section: "CLI Usage"
    anchor: "#cli-usage"
  - section: "Critical Rules"
    anchor: "#critical-rules"
---

# src/curate — Shared Curated Table Construction

## What This Package Does

Materializes the **shared curated parquet layer** consumed by all tracks. This is the single point where raw DuckDB entity tables are joined, cleaned, and written to disk as parquet files.

**Upstream:** `src.validate.schema_checks` must pass first.
**Downstream:** `src.eda.track_a` and `src.eda.track_b` read from this layer exclusively.

## Files

| File | Purpose |
|---|---|
| `build_review_fact.py` | Joins review + business + user entities, computes as-of features, writes all curated parquet artifacts |

## Curated Artifacts

| Artifact | Consumed by | Description |
|---|---|---|
| `data/curated/review_fact.parquet` | Track A only | Review rows with as-of business/user features, temporal columns |
| `data/curated/review_fact_track_b.parquet` | Track B only | Snapshot-safe version; includes `useful`, excludes temporal leakage fields |
| `data/curated/review.parquet` | All tracks | Flattened review entity (text, useful, funny, cool, stars, date) |
| `data/curated/business.parquet` | All tracks | Flattened business entity (snapshot attributes) |
| `data/curated/snapshot_metadata.json` | Track B | Contains `snapshot_reference_date` used by Track B stages |

## Track Ownership

**Track A** must only read `review_fact.parquet`. It must never touch `review_fact_track_b.parquet`.

**Track B** must only read `review_fact_track_b.parquet` and `snapshot_metadata.json`. It must never infer the snapshot date from data — read it from `snapshot_metadata.json`.

## CLI Usage

```bash
python scripts/run_pipeline.py --approach shared
```

## Critical Rules

- Never write back to `data/yelp.duckdb` from this package — curate is read-only from DuckDB.
- As-of features for Track A must use strictly earlier dates only. No same-day surrogate ordering.
- The snapshot date for Track B must be written to `snapshot_metadata.json` — never hardcoded in stage scripts.
