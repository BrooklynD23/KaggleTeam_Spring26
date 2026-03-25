---
id: T02
parent: S05
milestone: M002-c1uww6
provides:
  - Track D helper-level regression guardrails for D1-only joins, comparator semantics, label-coverage denominators, and required D1/D2 contract wording
key_files:
  - tests/test_track_d_baseline_model.py
  - .gsd/milestones/M002-c1uww6/slices/S05/tasks/T02-PLAN.md
  - .gsd/milestones/M002-c1uww6/slices/S05/S05-PLAN.md
key_decisions:
  - Keep runtime implementation unchanged for T02 and harden the contract through helper-level regression tests rather than widening end-to-end-only assertions
patterns_established:
  - Track D helper tests now use synthetic Stage 3/4/7 parquet fixtures to verify strict subtrack filtering and join-key coverage in isolation
  - Label coverage is asserted alongside Recall@20/NDCG@10 so unlabeled candidate-set denominators remain explicit in grouped metrics
observability_surfaces:
  - python -m pytest tests/test_track_d_baseline_model.py
  - python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py
  - outputs/modeling/track_d/metrics.csv
  - outputs/modeling/track_d/summary.md
duration: 52m
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T02: Add Track D baseline helper regression tests

**Expanded Track D baseline helper tests to lock D1-only joins, comparator fallback semantics, and unlabeled-set denominator reporting while keeping required D1/D2 wording contract checks green.**

## What Happened

I expanded `tests/test_track_d_baseline_model.py` with dedicated helper-contract coverage for the gaps called out in T02: strict D1-only candidate assembly/filtering across Stage 3/4/7 joins, explicit comparator fallback behavior when `popularity_rank` is missing, and grouped-metric denominator semantics when unlabeled candidate sets are present.

I also completed the required pre-flight fix by adding `## Observability Impact` to `.gsd/milestones/M002-c1uww6/slices/S05/tasks/T02-PLAN.md` so the task now states what signals changed, how to inspect them, and what failures now surface earlier.

No runtime code changes were needed in `src/modeling/track_d/baseline.py`; the current implementation already satisfied the strengthened helper contracts.

## Verification

I ran both task-level verification commands from T02 and then the full S05 slice verification suite to confirm the new tests did not regress the runtime contract or artifact bundle semantics.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_track_d_baseline_model.py` | 0 | ✅ pass | 1s |
| 2 | `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py` | 0 | ✅ pass | 2s |
| 3 | `python -m pytest tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 1s |
| 4 | `python -m src.modeling.track_d.baseline --config configs/track_d.yaml && test -f outputs/modeling/track_d/metrics.csv && test -f outputs/modeling/track_d/scores_test.parquet && test -f outputs/modeling/track_d/config_snapshot.json && test -f outputs/modeling/track_d/summary.md && test -f outputs/modeling/track_d/figures/d1_recall_ndcg_by_cohort.png && test -f outputs/modeling/track_d/d2_optional_report.csv` | 0 | ✅ pass | 35s |
| 5 | `python - <<'PY' ... track_d metrics/scores/summary/config assertions ... PY` | 0 | ✅ pass | 1s |
| 6 | `python - <<'PY' ... invalid config path failure diagnostic assertion ... PY` | 0 | ✅ pass | 1s |

## Diagnostics

Primary inspection surface for this task is `tests/test_track_d_baseline_model.py`; failures now pinpoint D1 subtrack-filter/join drift, comparator fallback drift, denominator drift, or required wording drift at helper-test granularity.

Runtime artifact diagnostics remain available via `python -m src.modeling.track_d.baseline --config configs/track_d.yaml` and inspection of `outputs/modeling/track_d/{metrics.csv,summary.md,config_snapshot.json}`.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `tests/test_track_d_baseline_model.py` — added helper-level regression tests for D1-only join filtering, comparator fallback semantics, and unlabeled denominator coverage.
- `.gsd/milestones/M002-c1uww6/slices/S05/tasks/T02-PLAN.md` — added the missing `## Observability Impact` section required by the pre-flight check.
- `.gsd/milestones/M002-c1uww6/slices/S05/S05-PLAN.md` — marked T02 complete (`[x]`).
