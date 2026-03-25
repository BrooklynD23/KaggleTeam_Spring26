---
estimated_steps: 3
estimated_files: 2
skills_used:
  - test
  - tdd-workflow
  - coding-standards
---

# T02: Add regression tests for Track B split, comparator, and ranking metric helpers

**Slice:** S03 — Track B snapshot ranking baseline
**Milestone:** M002-c1uww6

## Description

Add focused pytest coverage around the Track B baseline helper logic so the slice has stable regression protection for its most failure-prone pieces: group splitting, comparator scoring, and grouped ranking metrics.

## Steps

1. Identify the pure helper functions in `src/modeling/track_b/baseline.py` that can be tested without a full baseline run.
2. Add `tests/test_track_b_baseline_model.py` coverage for deterministic group splitting, comparator behavior, grouped NDCG/Recall helpers, and any summary/config helpers with stable string or schema expectations.
3. Run the new Track B helper suite and keep it green.

## Must-Haves

- [ ] Group-level split logic has deterministic regression coverage.
- [ ] Comparator scoring and grouped ranking metric helpers are tested independently of a full CLI run.
- [ ] The tests use small synthetic data and do not require full-data model training.

## Verification

- `python -m pytest tests/test_track_b_baseline_model.py`

## Inputs

- `src/modeling/track_b/baseline.py` — Track B helper logic to test

## Expected Output

- `tests/test_track_b_baseline_model.py` — regression tests for Track B baseline helper behavior
- `src/modeling/track_b/baseline.py` — helper extraction/refinement needed to make the new tests practical

## Observability Impact

- Signals changed: helper-level failures in Track B split assignment, trivial comparator scoring, and grouped ranking metric aggregation now surface as targeted pytest failures instead of only appearing in end-to-end baseline runs.
- Inspection path for future agents: run `python -m pytest tests/test_track_b_baseline_model.py` to isolate deterministic helper regressions before invoking the full baseline CLI.
- Failure visibility added: deterministic split drift, comparator rank-order drift, or grouped NDCG/Recall helper regressions now fail with unit-scale synthetic fixtures that identify the exact helper contract break.
