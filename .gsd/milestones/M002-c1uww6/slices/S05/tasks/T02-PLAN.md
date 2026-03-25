---
estimated_steps: 4
estimated_files: 3
skills_used:
  - tdd-workflow
  - test
  - coding-standards
---

# T02: Add Track D baseline helper regression tests

**Slice:** S05 — Track D1 cold-start baseline with optional D2 gate
**Milestone:** M002-c1uww6

## Description

Add a dedicated Track D modeling test suite that locks helper behavior before relying on full runtime outputs. The tests should guard D1 candidate assembly, comparator semantics, metric denominator clarity, and required optional-gate language.

## Steps

1. Create `tests/test_track_d_baseline_model.py` following the style used by `tests/test_track_a_baseline_model.py` and `tests/test_track_b_baseline_model.py`.
2. Add helper-focused tests for D1 candidate join coverage and strict D1-only filtering (`subtrack='D1'`) to prevent cross-subtrack mixing.
3. Add metric/comparator tests covering `Recall@20`, `NDCG@10`, and label-coverage semantics so unlabeled candidate sets are reported explicitly.
4. Add summary/config phrase tests asserting `D1 required`, `D2 optional`, and `non-blocking` wording, then run and fix until green.

## Must-Haves

- [ ] `tests/test_track_d_baseline_model.py` covers D1 helper contracts and comparator metric semantics.
- [ ] At least one test verifies required D1-required / D2-optional non-blocking phrasing.
- [ ] The suite passes with `python -m pytest tests/test_track_d_baseline_model.py`.

## Verification

- `python -m pytest tests/test_track_d_baseline_model.py`
- `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py`

## Inputs

- `src/modeling/track_d/baseline.py` — helper functions and summary/config writers under test
- `tests/test_track_a_baseline_model.py` — helper-test style reference for Track A
- `tests/test_track_b_baseline_model.py` — grouped ranking/comparator test style reference for Track B
- `tests/test_track_d_cohorts.py` — existing Track D cohort semantics and as-of constraints

## Expected Output

- `tests/test_track_d_baseline_model.py` — Track D modeling helper regression suite
- `src/modeling/track_d/baseline.py` — helper adjustments required to satisfy deterministic test coverage

## Observability Impact

- New signals: helper-level assertions for D1-only candidate assembly joins, comparator scoring/metric semantics, label-coverage denominator handling, and required D1/D2 wording contracts.
- How to inspect: run `python -m pytest tests/test_track_d_baseline_model.py` (and paired run with `tests/test_track_d_cohorts.py`) to see explicit failures tied to helper drift rather than only end-to-end runtime artifacts.
- Failure visibility: cross-subtrack mixing, join-key/schema drift, comparator-column drift, unlabeled-set denominator regressions, or wording-contract drift now fail as targeted test assertions with pinpointed failure messages.
