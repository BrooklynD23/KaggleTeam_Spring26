---
id: T03
parent: S01
milestone: M002-c1uww6
provides:
  - A stricter M002 modeling-contract regression test that now enforces milestone scope-lock markers, scaffold presence, and README artifact-contract markers
key_files:
  - tests/test_m002_modeling_contract.py
  - .gsd/milestones/M002-c1uww6/slices/S01/tasks/T03-PLAN.md
  - .gsd/milestones/M002-c1uww6/slices/S01/S01-PLAN.md
key_decisions:
  - No new architectural decision was recorded; this task hardened the existing shared modeling contract instead of changing it.
patterns_established:
  - Shared contract tests for M002 should assert both filesystem surfaces and README/milestone contract markers so future drift fails mechanically.
observability_surfaces:
  - tests/test_m002_modeling_contract.py
  - src/modeling/README.md
  - .gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md
  - .gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md
  - python -m pytest tests/test_m002_modeling_contract.py
duration: 20m
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T03: Add shared modeling-contract verification

**Hardened the M002 modeling contract test to enforce README artifact markers, scaffold presence, and milestone scope-lock language.**

## What Happened

I started by reading the existing contract surfaces and confirming the local `tests/test_m002_modeling_contract.py` already covered the milestone docs, current input visibility, and shared modeling directories. To satisfy the task plan’s remaining gap, I extended that regression test so it also asserts the shared artifact-contract language remains present in `src/modeling/README.md`, including the required artifact bundle, summary contract, track-specific notes, canonical `outputs/modeling/<track>/` surface, and the D1-required / D2-optional Track D wording.

Before implementation, I also applied the task plan’s flagged pre-flight fix by adding an `## Observability Impact` section to `.gsd/milestones/M002-c1uww6/slices/S01/tasks/T03-PLAN.md`. That section now explains which signals this task strengthens, how a future agent inspects the contract, and what concrete failure state becomes visible.

While rerunning pytest, I introduced then fixed a real regression in the test file: my first edit referenced a README-path/marker constant mismatch, which immediately failed under pytest. I corrected the missing constant definition/list and reran the suite until the contract test passed cleanly with the new assertions in place.

## Verification

I ran the task-level verification checks and the full slice-level verification set after hardening the test. The dedicated pytest target now passes with four assertions, the existence check for the test file passes, the milestone scope-lock grep still passes, the current-worktree curated-input diagnostic still passes, and the shared `src/modeling/*` / `outputs/modeling/*` directory check still passes.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 1.917s |
| 2 | `python - <<'PY'\nfrom pathlib import Path\nassert Path('tests/test_m002_modeling_contract.py').exists()\nprint('M002 modeling contract test exists')\nPY` | 0 | ✅ pass | 0.038s |
| 3 | `test -f .gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md && test -f .gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md && rg -n "D1 required|D2 optional|Track A preferred" .gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md .gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md` | 0 | ✅ pass | 0.000s |
| 4 | `python - <<'PY'\nfrom pathlib import Path\nrequired = [\n    Path('data/curated/review_fact.parquet'),\n    Path('data/curated/review_fact_track_b.parquet'),\n    Path('data/curated/review.parquet'),\n    Path('data/curated/business.parquet'),\n    Path('data/curated/user.parquet'),\n    Path('data/curated/snapshot_metadata.json'),\n    Path('outputs/tables/track_a_s5_candidate_splits.parquet'),\n]\nmissing = [p.as_posix() for p in required if not p.exists()]\nprint({'required_count': len(required), 'missing': missing})\nassert not missing, missing\nprint('repo-state truth inputs/artifacts present')\nPY` | 0 | ✅ pass | 0.055s |
| 5 | `test -d src/modeling/common && test -d src/modeling/track_a && test -d src/modeling/track_b && test -d src/modeling/track_c && test -d src/modeling/track_d && test -d outputs/modeling/track_a && test -d outputs/modeling/track_b && test -d outputs/modeling/track_c && test -d outputs/modeling/track_d` | 0 | ✅ pass | 0.000s |

## Diagnostics

A future agent can inspect `tests/test_m002_modeling_contract.py` to see the exact enforced contract markers and then run `python -m pytest tests/test_m002_modeling_contract.py` to get precise missing-marker or missing-path assertion messages. The paired inspection surfaces remain `src/modeling/README.md` for the artifact bundle contract and `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md` plus `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md` for the D1-required / D2-optional / Track A preferred scope lock.

## Deviations

- I updated `.gsd/milestones/M002-c1uww6/slices/S01/tasks/T03-PLAN.md` before finishing the test changes because the execution contract explicitly flagged its missing `## Observability Impact` section as a pre-flight fix.

## Known Issues

- None.

## Files Created/Modified

- `tests/test_m002_modeling_contract.py` — expanded the regression suite to enforce the README artifact-contract markers in addition to milestone markers and scaffold presence.
- `.gsd/milestones/M002-c1uww6/slices/S01/tasks/T03-PLAN.md` — added the missing `## Observability Impact` section required by the execution contract.
- `.gsd/milestones/M002-c1uww6/slices/S01/S01-PLAN.md` — marked T03 complete.
- `.gsd/milestones/M002-c1uww6/slices/S01/tasks/T03-SUMMARY.md` — recorded execution details and verification evidence for the task.
