---
id: src_eda_track_e
title: Track E EDA Context — Bias and Disparity Audit
version: "2026-03-18"
scope: src
tags: [track-e, eda, fairness, bias, disparity, audit, subgroup, proxy]
cross_dependencies:
  reads:
    - configs/track_e.yaml
    - data/curated/review_fact.parquet
    - data/curated/business.parquet
    - data/curated/user.parquet
    - outputs/tables/track_e_*.parquet
  writes:
    - src/eda/track_e/
    - outputs/tables/track_e_*.parquet
    - outputs/tables/track_e_*.md
    - outputs/figures/track_e_*.png
    - outputs/logs/track_e_*.log
  siblings: [src_eda, src_common]
toc:
  - section: "Stage Map"
    anchor: "#stage-map"
  - section: "Critical Rules"
    anchor: "#critical-rules"
  - section: "CLI Pattern"
    anchor: "#cli-pattern"
---

# Track E — Bias and Disparity Audit

Track E is the fairness-audit EDA pipeline. It profiles subgroup coverage, rating disparities, usefulness disparities, imbalance, proxy risk, and data-level fairness baselines before any downstream model is trained.

## Stage Map

1. `subgroup_definition.py`
2. `coverage_profile.py`
3. `star_disparity.py`
4. `usefulness_disparity.py`
5. `imbalance_analysis.py`
6. `proxy_risk.py`
7. `fairness_baseline.py`
8. `mitigation_candidates.py`
9. `summary_report.py`

## Critical Rules

- No demographic inference from names, neighborhoods, text, or derived proxies.
- All outputs are aggregate-only and must respect `subgroups.min_group_size` (default `10`).
- No causal claims. Findings are descriptive diagnostics, not explanations of why disparities exist.
- Stage 3 must run a Simpson's paradox check and persist `_simpson_flag`.
- `user.parquet` is read only in Stage 6 proxy analysis, never in subgroup definition.
- Banned text columns (`text`, `review_text`, `raw_text`) and forbidden demographic columns (`gender`, `race`, `income`, `ethnicity`, `nationality`) must never appear in parquet outputs.
- Stage 9 is a soft audit. It logs findings but does not hard-fail the pipeline.

## CLI Pattern

```bash
python -m src.eda.track_e.<stage> --config configs/track_e.yaml
```
