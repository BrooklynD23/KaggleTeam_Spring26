---
estimated_steps: 3
estimated_files: 2
skills_used:
  - test
---

# T02: Add helper regression tests for Track A baseline feature and metric logic

**Slice:** S02 — Track A temporal baseline and audit-target handoff
**Milestone:** M002-c1uww6

## Description

Add focused tests around the pure helper logic in the Track A baseline so the first modeling slice has a stable regression surface instead of relying only on end-to-end CLI runs.

## Steps

1. Add tests for derived feature behavior.
2. Add tests for clipped star-metric behavior.
3. Run the new Track A baseline helper tests.

## Must-Haves

- [ ] Derived feature logic has deterministic regression coverage.
- [ ] Metric helper behavior is tested independently of a full model run.

## Verification

- `python -m pytest tests/test_track_a_baseline_model.py`

## Inputs

- `src/modeling/track_a/baseline.py` — Track A baseline helper logic to test

## Expected Output

- `tests/test_track_a_baseline_model.py` — regression tests for Track A baseline helper behavior
