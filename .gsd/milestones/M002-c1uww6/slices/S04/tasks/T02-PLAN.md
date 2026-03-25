---
estimated_steps: 4
estimated_files: 3
skills_used:
  - tdd-workflow
  - test
  - coding-standards
---

# T02: Add Track C baseline helper regression tests

**Slice:** S04 — Track C monitoring baseline
**Milestone:** M002-c1uww6

## Description

Add a dedicated Track C modeling test file that locks helper behavior before relying on full-run outputs. This task guards score composition, ranking determinism, and summary contract language so future refactors cannot silently drift S04 acceptance logic.

## Steps

1. Create `tests/test_track_c_baseline_model.py` following the style used by `tests/test_track_a_baseline_model.py` and `tests/test_track_b_baseline_model.py`.
2. Add helper-focused tests for topic-drift rollups, rolling stability calculations, and deterministic `monitoring_change_score` ordering.
3. Add assertions that summary/config helpers include required monitoring phrases and exclude forecasting framing.
4. Run the new test file and adjust helper code or test fixtures until the suite passes cleanly.

## Must-Haves

- [ ] `tests/test_track_c_baseline_model.py` covers the main pure-helper paths behind scoring and ranking.
- [ ] At least one test verifies required monitoring-only summary language.
- [ ] The suite passes with `python -m pytest tests/test_track_c_baseline_model.py`.

## Verification

- `python -m pytest tests/test_track_c_baseline_model.py`
- `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py`

## Observability Impact

- Signals changed: helper-regression visibility in `tests/test_track_c_baseline_model.py` now explicitly covers topic rollups, rolling stability, deterministic ranking, and monitoring-only summary/config framing.
- How to inspect: run `python -m pytest tests/test_track_c_baseline_model.py` for focused helper diagnostics; run `python -m pytest tests/test_track_c_baseline_model.py tests/test_track_c_common.py` for Track C helper + shared contract alignment.
- Failure state surfaced: score/ranking drift, summary phrase regressions, and config-snapshot drift key regressions fail with direct assertion errors naming the broken helper contract.

## Inputs

- `src/modeling/track_c/baseline.py` — helper functions and summary/config writers under test
- `tests/test_track_a_baseline_model.py` — helper-test style reference for Track A
- `tests/test_track_b_baseline_model.py` — grouped/ranking helper-test style reference for Track B

## Expected Output

- `tests/test_track_c_baseline_model.py` — Track C monitoring helper regression suite
- `src/modeling/track_c/baseline.py` — helper adjustments required to satisfy deterministic test coverage
