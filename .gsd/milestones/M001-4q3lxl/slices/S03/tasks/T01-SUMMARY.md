---
id: T01
parent: S03
milestone: M001-4q3lxl
provides:
  - Stable .gsd/feature-plans root contract with canonical slugs, naming rules, and root-level regression coverage
key_files:
  - .gsd/feature-plans/README.md
  - tests/test_feature_plan_architecture.py
  - .gsd/milestones/M001-4q3lxl/slices/S03/S03-PLAN.md
  - .gsd/milestones/M001-4q3lxl/slices/S03/tasks/T01-PLAN.md
key_decisions:
  - Keep T01 scoped to the root architecture contract only; do not create placeholder feature folders before T02-T05 author real plan content
patterns_established:
  - Feature plans must cite real repo paths, outputs/exports/eda surfaces, and milestone drafts while labeling future targets explicitly as future
observability_surfaces:
  - .gsd/feature-plans/README.md
  - tests/test_feature_plan_architecture.py
  - python inventory diagnostic for per-slug feature-plan/sprint/phase presence
duration: 35m
verification_result: passed
completed_at: 2026-03-21T21:31:44-07:00
blocker_discovered: false
---

# T01: Lock the feature-plan root contract and verification harness

**Added the feature-plan root README contract, root-only pytest coverage, and explicit observability hooks for later slice work.**

## What Happened

I fixed the plan-level observability gaps first so S03 and T01 now describe how later agents inspect planning state and incomplete-slice failures. Then I created `.gsd/feature-plans/README.md` as the canonical root contract for the seven approved feature slugs, the required `FEATURE_PLAN.md` / `SPRINT.md` / `PHASE-*.md` naming pattern, the requirement to cite real repo seams plus `outputs/exports/eda/manifest.json` and `outputs/exports/eda/EXPORT_CONTRACT.md`, and the boundary that reserves S04-owned trust-narrative and intern-explainer writing.

I also added `tests/test_feature_plan_architecture.py` with root-only regression checks for the index file, slug inventory, naming/layout convention, and the explicit S03/S04 boundary language. To keep T01 honest about scope, the initial test suite asserts that `.gsd/feature-plans/` contains only the root index during this task rather than empty placeholder feature folders.

## Verification

I ran the task-level pytest target and README slug check from the task plan, then ran the broader slice verification commands. The root contract checks passed. The slice-wide count check failed exactly as expected because T02-T05 have not created the seven feature folders yet, and the new diagnostic inventory command made that partial state explicit instead of leaving only a bare assertion failure.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_feature_plan_architecture.py -k 'root_index'` | 0 | ✅ pass | 0.160s |
| 2 | `python - <<'PY' ... assert slug in readme ... PY` | 0 | ✅ pass | 0.027s |
| 3 | `python -m pytest tests/test_feature_plan_architecture.py` | 0 | ✅ pass | 0.179s |
| 4 | `python - <<'PY' ... assert len(feature_plans) == 7 ... PY` | 1 | ❌ fail | 0.031s |
| 5 | `python - <<'PY' ... print per-slug feature_plan/sprint_docs/phase_docs inventory ... PY` | 0 | ✅ pass | 0.029s |

## Diagnostics

Inspect `.gsd/feature-plans/README.md` first for the canonical slug list, file-layout contract, evidence handoff references, and S03/S04 boundary rules. Run `python -m pytest tests/test_feature_plan_architecture.py` for mechanical drift checks on the root contract. For partial-slice debugging, run the per-slug inventory command added to S03 verification; it prints whether each canonical slug has its `FEATURE_PLAN.md`, sprint docs, and phase docs yet.

## Deviations

None.

## Known Issues

The slice-level structure-count verification still fails because the seven feature-plan folders and their sprint/phase docs are intentionally deferred to T02-T05.

## Files Created/Modified

- `.gsd/feature-plans/README.md` — added the canonical root architecture contract for long-lived feature planning
- `tests/test_feature_plan_architecture.py` — added root-level regression coverage for the feature-plan contract
- `.gsd/milestones/M001-4q3lxl/slices/S03/S03-PLAN.md` — added observability/diagnostics and a per-slug inventory verification command; marked T01 done
- `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T01-PLAN.md` — added the missing Observability Impact section
