---
id: src_validate
title: src/validate — Schema Contract Checks
version: "2026-03-18"
scope: src
tags: [validate, schema, contracts, duckdb, leakage-prevention]

cross_dependencies:
  reads:
    - data/yelp.duckdb
    - configs/base.yaml
  writes:
    - outputs/logs/
  siblings: [src, src_ingest, src_curate]

toc:
  - section: "What This Package Does"
    anchor: "#what-this-package-does"
  - section: "Files"
    anchor: "#files"
  - section: "Contract Definitions"
    anchor: "#contract-definitions"
  - section: "CLI Usage"
    anchor: "#cli-usage"
  - section: "What Breaks Downstream if This Fails"
    anchor: "#what-breaks-downstream-if-this-fails"
---

# src/validate — Schema Contract Checks

## What This Package Does

Enforces schema contracts on the raw DuckDB tables **before** curation runs. Acts as a gate: if validation fails, the pipeline should not proceed to `src.curate`.

**Upstream:** `src.ingest.load_yelp_json` — DuckDB must be populated first.
**Downstream:** `src.curate.build_review_fact` — reads validated DuckDB tables.

## Files

| File | Purpose |
|---|---|
| `schema_checks.py` | Row count minimums, required column presence, null-rate thresholds, referential integrity between entities |

## Contract Definitions

Contracts enforced by `schema_checks.py`:

| Check | Description |
|---|---|
| Required columns | Verifies `review_id`, `business_id`, `user_id`, `stars`, `date`, `text`, `useful` exist in `review` |
| Null rate | `review.stars` null rate must be < 1% |
| Referential integrity | Every `review.business_id` must exist in `business.business_id` |
| Row count floor | `review` table must have > 1 million rows |
| Date format | `review.date` must parse as `YYYY-MM-DD HH:MM:SS` |

## CLI Usage

```bash
python scripts/run_pipeline.py --approach shared
# Validation is automatically included in the shared approach

# Run module directly
python -m src.validate.schema_checks
```

## What Breaks Downstream if This Fails

- `src.curate.build_review_fact` will silently produce incorrect parquet artifacts if referential integrity is not enforced here.
- Track A leakage audit (Stage 6) assumes upstream schema is clean — contaminated data can produce false negatives.
- Track B label construction assumes `useful` column is fully populated.
