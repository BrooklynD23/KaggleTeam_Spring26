---
id: root
title: KaggleTeam Spring 2026 — Yelp Open Dataset Project
version: "2026-03-18"
scope: repo
tags: [yelp, kaggle, semester-project, pipeline, eda, entry-point]

cross_dependencies:
  reads:
    - README.md
    - CONTEXT_SPEC.md
    - configs/base.yaml
    - configs/track_a.yaml
    - configs/track_b.yaml
  writes: []
  siblings: []

toc:
  - section: "Project Mission"
    anchor: "#project-mission"
  - section: "Repository Map"
    anchor: "#repository-map"
  - section: "Data Flow"
    anchor: "#data-flow"
  - section: "Key Constraints"
    anchor: "#key-constraints"
  - section: "How to Run"
    anchor: "#how-to-run"
  - section: "Context Loading Guide"
    anchor: "#context-loading-guide"
  - section: "All CLAUDE.md Files"
    anchor: "#all-claudemd-files"
---

# KaggleTeam Spring 2026 — Yelp Open Dataset Project

This is the **master context file** for the repository. Any agent working in this repo should read this file first, then follow the [Context Loading Guide](#context-loading-guide) to load only the sub-context files relevant to the current task.

## Project Mission

A semester-scale data science project analyzing the **Yelp Open Dataset** across five research tracks:

| Track | Focus |
|---|---|
| A | Future star rating prediction under strict temporal splits |
| B | Snapshot usefulness ranking with age-controlled review groups |
| C | Sentiment and topic drift over time and geography |
| D | Cold-start recommendation for businesses and users |
| E | Bias and disparity auditing across groups |

Tracks A and B are fully implemented. Tracks C, D, and E exist in planning documents only.

## Repository Map

```
KaggleTeam_Spring26/
├── CLAUDE.md                     ← YOU ARE HERE (repo root context)
├── CONTEXT_SPEC.md               ← frontmatter schema standard
├── README.md                     ← public-facing project overview
├── configs/
│   ├── base.yaml                 ← shared config (paths, DuckDB settings)
│   ├── track_a.yaml              ← Track A overrides
│   └── track_b.yaml              ← Track B overrides
├── data/
│   ├── raw/                      ← extracted Yelp NDJSON files
│   ├── interim/                  ← optional intermediate assets
│   └── curated/                  ← shared parquet artifacts consumed by all tracks
├── outputs/
│   ├── figures/                  ← generated charts per track and stage
│   ├── logs/                     ← pipeline and validation logs
│   └── tables/                   ← parquet and markdown deliverables
├── scripts/
│   ├── run_pipeline.py           ← canonical cross-platform launcher
│   ├── pipeline_dispatcher.py   ← execution engine (invoked by launcher)
│   ├── update_frontmatter.py     ← CLAUDE.md frontmatter validator/tool
│   ├── check_repo_readme_drift.py
│   └── check_docs_drift.py
├── src/
│   ├── ingest/                   ← JSON extraction → DuckDB loading
│   ├── validate/                 ← schema contract checks
│   ├── curate/                   ← shared curated table construction
│   └── eda/
│       ├── track_a/              ← 8-stage Track A EDA pipeline
│       └── track_b/              ← 8-stage Track B EDA pipeline
├── tests/                        ← regression and contract tests
└── CoWork Planning/
    └── yelp_project/             ← PRD, implementation plans, per-track planning docs
        ├── track_a/ … track_e/
        └── docs_agent/
```

## Data Flow

```
CoWork Planning/Dataset(Raw)/Yelp-JSON/yelp_dataset.tar
        │
        ▼  src.ingest.load_yelp_json
data/raw/   (NDJSON files)
        │
        ▼  src.validate.schema_checks
(validation logs in outputs/logs/)
        │
        ▼  src.curate.build_review_fact
data/curated/review_fact.parquet           ← Track A input
data/curated/review_fact_track_b.parquet   ← Track B input
data/curated/snapshot_metadata.json        ← Track B snapshot date
        │
        ├──▶  src.eda.track_a.*   → outputs/tables/track_a_*, outputs/figures/track_a_*
        └──▶  src.eda.track_b.*   → outputs/tables/track_b_*, outputs/figures/track_b_*
```

**Execution order matters.** Always run shared → Track A/B. Never run track stages before curation is complete.

## Key Constraints

These apply **everywhere** in the repo. Violations are caught by tests or the leakage audit stages.

1. **No raw review text** in any output artifact, figure, table, or log file.
2. **No future data leakage** — Track A features must be strictly as-of the review date.
3. **Track A** reads only `review_fact.parquet`. Never `review_fact_track_b.parquet`.
4. **Track B** is a single-snapshot task. Do not infer vote growth or temporal trends.
5. **Banned snapshot-only fields for Track A features:** `business.stars`, `business.review_count`, `business.is_open`, `user.average_stars`, `user.review_count`, `user.fans`, `user.elite` (unless explicitly computed as-of).
6. Config lives in `configs/`. Do not hardcode paths in source files.
7. All CLI entry points use `python -m src.<module>` or `python scripts/run_pipeline.py` (launcher) / `python scripts/pipeline_dispatcher.py` (execution engine).

## How to Run

```bash
# Install dependencies (into runtime-matched venv: .venv-wsl, .venv-win, or .venv-linux)
pip install -r requirements.txt

# Run via canonical launcher (interactive or explicit)
python scripts/run_pipeline.py
python scripts/run_pipeline.py --approach shared
python scripts/run_pipeline.py --approach track_a
python scripts/run_pipeline.py --approach track_b

# Or via OS wrappers
./run_pipeline.sh shared
# Windows: .\run_pipeline.ps1 track_a

# Validate README drift
python scripts/check_repo_readme_drift.py --check

# Validate all CLAUDE.md frontmatter
python scripts/update_frontmatter.py --check
```

## Context Loading Guide

Load **only** the CLAUDE.md files needed for your current task. Start from the outermost and work inward.

| Task | Load these CLAUDE.md files (in order) |
|---|---|
| Working on any source code | `CLAUDE.md` → `src/CLAUDE.md` → relevant sub-package |
| Working on Track A code | `CLAUDE.md` → `src/CLAUDE.md` → `src/eda/CLAUDE.md` → `src/eda/track_a/CLAUDE.md` |
| Working on Track B code | `CLAUDE.md` → `src/CLAUDE.md` → `src/eda/CLAUDE.md` → `src/eda/track_b/CLAUDE.md` |
| Working on Track E code | `CLAUDE.md` → `src/CLAUDE.md` → `src/eda/CLAUDE.md` → `src/eda/track_e/CLAUDE.md` |
| Working on ingestion | `CLAUDE.md` → `src/CLAUDE.md` → `src/ingest/CLAUDE.md` |
| Working on planning docs | `CLAUDE.md` → `CoWork Planning/CLAUDE.md` → relevant track |
| Adding/editing docs | `CLAUDE.md` → `CoWork Planning/yelp_project/docs_agent/CLAUDE.md` |
| Running scripts only | `CLAUDE.md` → `scripts/CLAUDE.md` |
| Writing/running tests | `CLAUDE.md` → `tests/CLAUDE.md` |

## All CLAUDE.md Files

Complete inventory. Use `python scripts/update_frontmatter.py --list` to see live versions.

| id | Path | Scope |
|---|---|---|
| `root` | `CLAUDE.md` | repo |
| `src` | `src/CLAUDE.md` | src |
| `src_ingest` | `src/ingest/CLAUDE.md` | src |
| `src_validate` | `src/validate/CLAUDE.md` | src |
| `src_curate` | `src/curate/CLAUDE.md` | src |
| `src_eda` | `src/eda/CLAUDE.md` | src |
| `src_eda_track_a` | `src/eda/track_a/CLAUDE.md` | track |
| `src_eda_track_b` | `src/eda/track_b/CLAUDE.md` | track |
| `src_eda_track_e` | `src/eda/track_e/CLAUDE.md` | track |
| `cowork_planning` | `CoWork Planning/CLAUDE.md` | cowork |
| `track_a_planning` | `CoWork Planning/yelp_project/track_a/CLAUDE.md` | track |
| `track_b_planning` | `CoWork Planning/yelp_project/track_b/CLAUDE.md` | track |
| `track_c_planning` | `CoWork Planning/yelp_project/track_c/CLAUDE.md` | track |
| `track_d_planning` | `CoWork Planning/yelp_project/track_d/CLAUDE.md` | track |
| `track_e_planning` | `CoWork Planning/yelp_project/track_e/CLAUDE.md` | track |
| `docs_agent` | `CoWork Planning/yelp_project/docs_agent/CLAUDE.md` | cowork |
| `scripts` | `scripts/CLAUDE.md` | scripts |
| `tests` | `tests/CLAUDE.md` | tests |
