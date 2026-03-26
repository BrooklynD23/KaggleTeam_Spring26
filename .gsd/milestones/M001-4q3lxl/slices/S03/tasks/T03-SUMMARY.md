---
id: T03
parent: S03
milestone: M001-4q3lxl
provides:
  - Agent-ready Track C and Track D feature-plan lanes with repo-grounded plan, sprint, phase, and regression coverage surfaces
key_files:
  - .gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md
  - .gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/SPRINT.md
  - .gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/phases/PHASE-01-drift-signal-baseline.md
  - .gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md
  - .gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/SPRINT.md
  - .gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/phases/PHASE-01-candidate-split-gate.md
  - tests/test_feature_plan_architecture.py
  - .gsd/milestones/M001-4q3lxl/slices/S03/tasks/T03-PLAN.md
  - .gsd/milestones/M001-4q3lxl/slices/S03/S03-PLAN.md
key_decisions:
  - Keep Track C explicitly framed as drift monitoring and keep Track D explicitly blocked on outputs/tables/track_a_s5_candidate_splits.parquet until that upstream artifact is real
patterns_established:
  - Monitoring and cold-start feature plans should pair current export manifests with clearly labeled future target folders while carrying forward blocker truth from manifests and command checklists verbatim
observability_surfaces:
  - .gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md
  - .gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md
  - tests/test_feature_plan_architecture.py
  - python inventory diagnostic for per-slug feature-plan/sprint/phase presence
duration: 48m
verification_result: passed
completed_at: 2026-03-21T21:31:44-07:00
blocker_discovered: false
---

# T03: Author Track C and Track D execution plans

**Added Track C and Track D feature-plan, sprint, and phase docs with drift-monitoring and Track-A-gated cold-start guardrails.**

## What Happened

I fixed the task-plan observability gap first by adding `## Observability Impact` to `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T03-PLAN.md`, so the task now explains how future agents should inspect Track C/Track D planning state and what drift in those surfaces should look like.

Then I authored the Track C lane under `.gsd/feature-plans/track-c-monitoring/`. The new feature plan, sprint doc, and phase doc are grounded in `src/eda/track_c/`, `outputs/exports/eda/tracks/track_c/manifest.json`, `outputs/tables/eda_command_checklist.md`, and `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md`. I kept the lane explicitly in drift/monitoring framing, tied the execution seam to `src/eda/track_c/drift_detection.py`, and made the docs reject generic forecasting language as a framing bug.

I also authored the Track D lane under `.gsd/feature-plans/track-d-onboarding/`. Those docs are grounded in `src/eda/track_d/`, `outputs/exports/eda/tracks/track_d/manifest.json`, `outputs/tables/eda_command_checklist.md`, and the upstream dependency path `outputs/tables/track_a_s5_candidate_splits.parquet`. I checked the local worktree before writing and confirmed that `outputs/tables/track_a_s5_candidate_splits.parquet` is currently missing, so the Track D docs treat it as a visible blocker and dependency gate rather than implying Track D can already execute end to end.

Finally, I extended `tests/test_feature_plan_architecture.py` with Track C and Track D assertions. The new coverage checks structure, milestone cross-links, future-folder labeling, Track C drift/monitoring language, and Track D's `track_a_s5_candidate_splits.parquet` dependency wording.

## Verification

I ran the task-level targeted pytest selection and the explicit content assertion from the task plan; both passed. I then ran the full current feature-plan pytest file, which now passes with root, Track A/B, and Track C/D coverage.

For slice-level verification, I ran the count-based structure check and the per-slug inventory command from S03. The count check still fails, as expected for an intermediate task, because only four of the seven canonical feature lanes exist so far. The inventory output now shows Track C and Track D as populated alongside Track A and Track B, with Track E, showcase, and multimodal still empty for T04-T05.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_feature_plan_architecture.py -k "track_c or track_d"` | 0 | ✅ pass | 0.43s |
| 2 | `python - <<'PY' ... assert 'drift' in track_c.lower() ... assert 'track_a_s5_candidate_splits.parquet' in track_d ... PY` | 0 | ✅ pass | 0.07s |
| 3 | `python -m pytest tests/test_feature_plan_architecture.py` | 0 | ✅ pass | 0.43s |
| 4 | `python - <<'PY' ... assert len(feature_plans) == 7 ... PY` | 1 | ❌ fail | 0.07s |
| 5 | `python - <<'PY' ... print per-slug feature_plan/sprint_docs/phase_docs inventory ... PY` | 0 | ✅ pass | 0.07s |

## Diagnostics

Inspect `.gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md` first for the drift/monitoring contract and `.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md` first for the Track A Stage 5 dependency gate. Use `tests/test_feature_plan_architecture.py` to catch drift in file layout, future-folder labeling, or framing language. For partial-slice debugging, rerun the S03 inventory command; it now shows Track A through Track D as populated and later canonical slugs as still pending.

## Deviations

I updated `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T03-PLAN.md` before implementation to add the missing `## Observability Impact` section required by the pre-flight fix.

## Known Issues

The slice-level count verification still fails because `track-e-accountability`, `showcase-system`, and `multimodal-experiments` have not been authored yet. In addition, `outputs/tables/track_a_s5_candidate_splits.parquet` is currently missing locally, so the Track D plan correctly remains dependency-gated on Track A Stage 5.

## Files Created/Modified

- `.gsd/feature-plans/track-c-monitoring/FEATURE_PLAN.md` — added the Track C execution plan with drift/monitoring guardrails, export evidence crosswalk, and future target folders
- `.gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/SPRINT.md` — added the first Track C sprint contract with commands, verification, blockers, and exit criteria
- `.gsd/feature-plans/track-c-monitoring/sprints/SPRINT-01-drift-baseline/phases/PHASE-01-drift-signal-baseline.md` — added the first Track C phase handoff for drift-signal execution
- `.gsd/feature-plans/track-d-onboarding/FEATURE_PLAN.md` — added the Track D execution plan with cold-start framing and explicit Track A Stage 5 dependency wording
- `.gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/SPRINT.md` — added the first Track D sprint contract with commands, verification, blockers, and exit criteria
- `.gsd/feature-plans/track-d-onboarding/sprints/SPRINT-01-cold-start-baseline/phases/PHASE-01-candidate-split-gate.md` — added the first Track D phase handoff for candidate-split-gated cold-start execution
- `tests/test_feature_plan_architecture.py` — extended the architecture regression file with Track C and Track D structure/content assertions
- `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T03-PLAN.md` — added the missing observability section required by the pre-flight fix
- `.gsd/milestones/M001-4q3lxl/slices/S03/S03-PLAN.md` — marked T03 done
