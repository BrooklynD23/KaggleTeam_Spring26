---
id: S03
parent: M002-c1uww6
milestone: M002-c1uww6
provides:
  - Track B baseline ranking runtime with grouped quality metrics and snapshot-safe artifact bundle under outputs/modeling/track_b/.
requires:
  - slice: M001-4q3lxl/S01
    provides: Snapshot/candidate surfaces and upstream EDA assets consumed by Track B modeling.
affects:
  - S06
  - M003-rdpeu4
key_files:
  - src/modeling/track_b/baseline.py
  - tests/test_track_b_baseline_model.py
  - outputs/modeling/track_b/metrics.csv
  - outputs/modeling/track_b/config_snapshot.json
  - outputs/modeling/track_b/summary.md
  - outputs/modeling/track_b/scores_test.parquet
key_decisions:
  - Extract comparator scoring into add_trivial_comparator_scores() so comparator semantics stay directly testable outside end-to-end runtime orchestration.
patterns_established:
  - Treat missing failure-path diagnostics as a plan-level defect and patch the slice/task contract before accepting runtime verification as complete.
observability_surfaces:
  - python -m src.modeling.track_b.baseline --config configs/track_b.yaml
  - python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py
  - outputs/modeling/track_b/metrics.csv
  - outputs/modeling/track_b/config_snapshot.json
  - outputs/modeling/track_b/scores_test.parquet
  - outputs/modeling/track_b/summary.md
drill_down_paths:
  - .gsd/milestones/M002-c1uww6/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002-c1uww6/slices/S03/tasks/T03-SUMMARY.md
duration: 45m
verification_result: passed
completed_at: 2026-03-23
---

# S03: Track B baseline modeling contract

**Validated and froze the Track B snapshot ranking baseline with comparator-ordering guarantees, helper regression coverage, and explicit failure-path diagnostics.**

## What Happened

S03 verified the existing Track B runtime in local reality, then hardened helper-level contracts and slice diagnostics around grouped ranking behavior. The baseline CLI repeatedly regenerated `outputs/modeling/track_b/` artifacts while tests enforced deterministic split logic, comparator assignment, grouped metric lookup semantics, and held-out comparator ordering.

Task execution also added/locked an explicit invalid-config-path failure check in the slice verification flow so diagnostics stay inspectable rather than inferred.

Concrete verification artifacts for this slice are:
- `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
- `python -m pytest tests/test_track_b_baseline_model.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_m002_modeling_contract.py`
- `outputs/modeling/track_b/metrics.csv` showing held-out `ALL` NDCG@10 ordering (`pointwise_percentile_regressor > text_length_only > review_stars_only`).

## Verification

All T01–T03 checks passed: baseline runtime and required artifact presence, helper/integration pytest suites, comparator ordering assertions, summary/config guardrail assertions, and invalid-config failure-path assertions.

## Requirements Advanced

- R006 — Implemented and validated the Track B snapshot ranking baseline with comparator and grouped metric surfaces.
- R012 — Improved cross-slice narrative integrity by ensuring Track B handoff diagnostics are explicit and replayable.

## Requirements Validated

- R006 — Slice evidence includes repeated successful runtime runs plus persisted grouped ranking metrics and comparator ordering assertions.

## New Requirements Surfaced

- none.

## Requirements Invalidated or Re-scoped

- none.

## Deviations

Planner snapshot expected fresh baseline authoring, but the runtime already existed in this worktree; execution adapted by validating and hardening test/diagnostic surfaces without unnecessary rewrite.

## Known Limitations

This slice focuses on pointwise percentile ranking baselines; it does not prove listwise optimization or richer feature families beyond the current scope.

## Follow-ups

- Keep summary/config wording stable until integrated S06/T03 closure is complete because the handoff harness checks phrase-level contracts.
- If Track B feature sets are extended in M003, preserve the invalid-config diagnostic check and comparator ordering assertions as regression anchors.

## Files Created/Modified

- `src/modeling/track_b/baseline.py` — introduced reusable comparator helper and retained runtime generation logic.
- `tests/test_track_b_baseline_model.py` — expanded deterministic split/comparator/grouped-metric helper coverage.
- `outputs/modeling/track_b/metrics.csv` — held-out grouped ranking metrics and comparator ordering evidence.
- `outputs/modeling/track_b/config_snapshot.json` — snapshot guardrails, banned features, and resolved config truth.
- `outputs/modeling/track_b/summary.md` — frozen snapshot framing and model-scope narrative.

## Forward Intelligence

### What the next slice should know
- The canonical quality check is the held-out `ALL` NDCG@10 comparator ordering in `outputs/modeling/track_b/metrics.csv`; integrated tests assume this schema and ordering.

### What's fragile
- Any schema drift from wide `ndcg_at_10`/`recall_at_10` rows to a different metric layout can break downstream contract checks quickly.

### Authoritative diagnostics
- Invalid-config-path execution (`configs/does_not_exist.yaml`) — this is the fastest way to confirm failure-path diagnostics remain user-actionable.

### What assumptions changed
- “Track B needs large runtime rewrites” — local execution showed the runtime was already mature; the critical risk was contract and diagnostic drift, not missing core implementation.
