---
id: src_ingest
title: src/ingest — Yelp JSON Extraction and DuckDB Loading
version: "2026-03-18"
scope: src
tags: [ingest, duckdb, json, tar, extraction, load]

cross_dependencies:
  reads:
    - CoWork Planning/Dataset(Raw)/Yelp-JSON/Yelp JSON/yelp_dataset.tar
    - configs/base.yaml
  writes:
    - data/raw/yelp_academic_dataset_review.json
    - data/raw/yelp_academic_dataset_business.json
    - data/raw/yelp_academic_dataset_user.json
    - data/raw/yelp_academic_dataset_tip.json
    - data/raw/yelp_academic_dataset_checkin.json
    - data/yelp.duckdb
    - outputs/logs/
  siblings: [src, src_validate]

toc:
  - section: "What This Package Does"
    anchor: "#what-this-package-does"
  - section: "Files"
    anchor: "#files"
  - section: "CLI Usage"
    anchor: "#cli-usage"
  - section: "Outputs"
    anchor: "#outputs"
  - section: "Failure Modes"
    anchor: "#failure-modes"
---

# src/ingest — Yelp JSON Extraction and DuckDB Loading

## What This Package Does

Handles the first pipeline stage: extract the Yelp tar archive into NDJSON files, then load each entity into a DuckDB database at `data/yelp.duckdb`.

**Upstream:** Raw tar archive at `CoWork Planning/Dataset(Raw)/`.
**Downstream:** `src.validate.schema_checks` runs immediately after to verify DuckDB contents.

## Files

| File | Purpose |
|---|---|
| `load_yelp_json.py` | Extracts tar → NDJSON, then loads into DuckDB entity tables |
| `validate_json_structure.py` | Pre-load structural check on NDJSON line format before committing to DuckDB |

## CLI Usage

```bash
# Run via launcher (recommended; handles venv and approach selection)
python scripts/run_pipeline.py --approach shared

# Run module directly
python -m src.ingest.load_yelp_json
```

Config keys consumed from `configs/base.yaml`:
- `raw_dir` — destination for extracted NDJSON
- `duckdb_path` — path to `data/yelp.duckdb`
- `archive_path` — source tar location

## Outputs

| Artifact | Description |
|---|---|
| `data/raw/*.json` | Extracted NDJSON entity files (5 files) |
| `data/yelp.duckdb` | DuckDB database with one table per entity |
| `outputs/logs/ingest_*.log` | Row counts, timing, any extraction errors |

## Failure Modes

- **Missing archive:** Raises `FileNotFoundError` with the expected path. Check `configs/base.yaml → archive_path`.
- **NDJSON malformed:** `validate_json_structure.py` catches this before DuckDB load and writes an error log.
- **DuckDB locked:** Only one process should write to `data/yelp.duckdb` at a time.
