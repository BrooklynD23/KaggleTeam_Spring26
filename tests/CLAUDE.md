---
id: tests
title: tests/ — Regression and Contract Tests
version: "2026-03-18"
scope: tests
tags: [tests, regression, contracts, leakage, feasibility, pytest]

cross_dependencies:
  reads:
    - data/curated/review_fact.parquet
    - data/curated/review_fact_track_b.parquet
    - data/curated/snapshot_metadata.json
    - configs/base.yaml
    - README.md
  writes:
    - outputs/logs/
  siblings: [root, src_validate, src_eda_track_a, src_eda_track_b]

toc:
  - section: "What Is In Here"
    anchor: "#what-is-in-here"
  - section: "Test Inventory"
    anchor: "#test-inventory"
  - section: "Running Tests"
    anchor: "#running-tests"
  - section: "Adding Tests"
    anchor: "#adding-tests"
---

# tests/ — Regression and Contract Tests

## What Is In Here

Regression and contract tests for pipeline integrity. **No model training or full pipeline execution** happens here — tests assert on schema, logic, and constraints only.

## Test Inventory

| File | What it tests |
|---|---|
| `test_check_repo_readme_drift.py` | README drift detector logic |
| `test_feasibility_signoff.py` | Track B pairwise training feasibility thresholds |
| `test_label_scheme_ranking.py` | Track B label construction logic |
| `test_leakage_scope_check.py` | Track B leakage regex rules |
| `test_load_candidate_splits.py` | Track A split loading and T₁/T₂ format |
| `test_sentiment_semijoin.py` | Track B feature semi-join correctness |
| `test_split_selection_columns.py` | Track A split output column schema |

## Running Tests

```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_feasibility_signoff.py -v

# Run with output capture disabled (useful for debugging print statements)
pytest tests/ -s
```

Tests should pass before any merge to `main`. The pre-commit hook does **not** run the full test suite (too slow), but CI does.

## Adding Tests

- Place new test files in `tests/` with the `test_` prefix.
- Use `pytest` fixtures and parametrize where possible.
- Contract tests (schema, column presence) live here. Performance benchmarks do not.
- Tests must not write to `data/curated/` — mock or use small fixtures.
