---
id: T02
parent: S03
milestone: M002-c1uww6
provides:
  - Added deterministic helper-level regression coverage for Track B group splits, comparator scoring, grouped ranking metrics, and metric lookup contracts
  - Extracted comparator scoring into a dedicated helper to keep comparator behavior independently testable
key_files:
  - src/modeling/track_b/baseline.py
  - tests/test_track_b_baseline_model.py
  - .gsd/milestones/M002-c1uww6/slices/S03/S03-PLAN.md
key_decisions:
  - Introduced `add_trivial_comparator_scores()` so comparator-score behavior can be validated without relying on end-to-end CLI orchestration
patterns_established:
  - For Track B ranking helpers, keep comparator transformations in a pure helper and assert comparator score identity directly in unit tests
observability_surfaces:
  - python -m pytest tests/test_track_b_baseline_model.py
  - python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py
  - outputs/modeling/track_b/metrics.csv
  - outputs/modeling/track_b/config_snapshot.json
  - outputs/modeling/track_b/scores_test.parquet
duration: 0h 12m
verification_result: passed
completed_at: 2026-03-23T09:36:44-07:00
blocker_discovered: false
---

# T02: Add regression tests for Track B split, comparator, and ranking metric helpers

**Added helper-level Track B regression coverage and extracted comparator scoring into a pure helper so split/metric/comparator drift fails fast under pytest.**

## What Happened

I first applied the pre-flight fix by adding `## Observability Impact` to `.gsd/milestones/M002-c1uww6/slices/S03/tasks/T02-PLAN.md`. Then I expanded `tests/test_track_b_baseline_model.py` from 4 to 7 tests, adding coverage for input-order-independent deterministic splits, one/two-group stratum split behavior, comparator score derivation, grouped metric lookup contracts, and `evaluate_models()` comparator/test-score outputs using synthetic frames.

To make comparator behavior independently testable, I extracted comparator assignment from `evaluate_models()` into `add_trivial_comparator_scores()` in `src/modeling/track_b/baseline.py`, then routed runtime code through that helper.

## Verification

I ran the task-specific helper suite and then the full S03 verification commands. All checks passed, including the full Track B baseline runtime, comparator ordering assertion, summary/config guardrail assertions, and invalid-config-path diagnostic behavior.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_track_b_baseline_model.py` | 0 | ✅ pass | 2.08s |
| 2 | `python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 2.05s |
| 3 | `python -m src.modeling.track_b.baseline --config configs/track_b.yaml && test -f outputs/modeling/track_b/summary.md && test -f outputs/modeling/track_b/metrics.csv && test -f outputs/modeling/track_b/config_snapshot.json && test -f outputs/modeling/track_b/scores_test.parquet && test -f outputs/modeling/track_b/figures/test_ndcg_by_age_bucket.png` | 0 | ✅ pass | 258.84s |
| 4 | Held-out comparator ordering assertion snippet on `outputs/modeling/track_b/metrics.csv` (`pointwise_percentile_regressor > text_length_only > review_stars_only`) | 0 | ✅ pass | 0.41s |
| 5 | Summary/config guardrail assertion snippet on `outputs/modeling/track_b/summary.md` + `outputs/modeling/track_b/config_snapshot.json` | 0 | ✅ pass | 0.03s |
| 6 | Invalid-config-path diagnostic snippet (`configs/does_not_exist.yaml` must fail with inspectable error text) | 0 | ✅ pass | 1.38s |

## Diagnostics

To inspect what this task added later:

- Run `python -m pytest tests/test_track_b_baseline_model.py` to validate helper contracts directly.
- Open `tests/test_track_b_baseline_model.py` for synthetic comparator/split/metric regression fixtures.
- Run `python -m src.modeling.track_b.baseline --config configs/track_b.yaml` and inspect:
  - `outputs/modeling/track_b/metrics.csv`
  - `outputs/modeling/track_b/config_snapshot.json`
  - `outputs/modeling/track_b/scores_test.parquet`

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `.gsd/milestones/M002-c1uww6/slices/S03/tasks/T02-PLAN.md` — added the missing `## Observability Impact` section required by pre-flight checks.
- `src/modeling/track_b/baseline.py` — added `add_trivial_comparator_scores()` and reused it in `evaluate_models()`.
- `tests/test_track_b_baseline_model.py` — expanded regression coverage for deterministic splits, comparator scoring, grouped metric helpers, and evaluation outputs.
- `.gsd/milestones/M002-c1uww6/slices/S03/S03-PLAN.md` — marked T02 as complete (`[x]`).
- `.gsd/milestones/M002-c1uww6/slices/S03/tasks/T02-SUMMARY.md` — recorded T02 execution and verification evidence.
