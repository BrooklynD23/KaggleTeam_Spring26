---
id: T04
parent: S03
milestone: M001-4q3lxl
provides:
  - Agent-ready Track E and showcase-system feature-plan lanes with repo-grounded plan, sprint, phase, and regression coverage surfaces
key_files:
  - .gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md
  - .gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/SPRINT.md
  - .gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/phases/PHASE-01-upstream-model-gate.md
  - .gsd/feature-plans/showcase-system/FEATURE_PLAN.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md
  - tests/test_feature_plan_architecture.py
  - .gsd/milestones/M001-4q3lxl/slices/S03/tasks/T04-PLAN.md
  - .gsd/milestones/M001-4q3lxl/slices/S03/S03-PLAN.md
key_decisions:
  - Keep Track E explicitly gated on selecting a real upstream Track A or Track D model target before any fairness-mitigation work claims execution readiness, and keep showcase planning strictly bound to outputs/exports/eda instead of live analytical storage.
patterns_established:
  - Cross-boundary feature plans should pair current export evidence with milestone drafts and prior-art references while reserving later narrative workflow ownership instead of filling it in early.
observability_surfaces:
  - .gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md
  - .gsd/feature-plans/showcase-system/FEATURE_PLAN.md
  - tests/test_feature_plan_architecture.py
  - python inventory diagnostic for per-slug feature-plan/sprint/phase presence
duration: 46m
verification_result: passed
completed_at: 2026-03-21T21:31:44-07:00
blocker_discovered: false
---

# T04: Author Track E and showcase-system execution plans

**Added Track E and showcase-system feature-plan, sprint, and phase docs with upstream-audit and export-boundary guardrails.**

## What Happened

I fixed the task-plan observability gap first by adding `## Observability Impact` to `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T04-PLAN.md`, so the task now explains how future agents should inspect Track E/showcase planning state and what drift in those surfaces should look like.

Then I authored the Track E lane under `.gsd/feature-plans/track-e-accountability/`. The new feature plan, sprint doc, and phase doc are grounded in `src/eda/track_e/`, `outputs/exports/eda/tracks/track_e/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, and `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-CONTEXT-DRAFT.md`. I kept the lane explicitly framed as an upstream-model fairness and accountability layer tied to Track A or Track D, carried forward the local reality that most Track E artifacts are still missing, and made target selection plus fairness-versus-accuracy tradeoff measurement the first execution gate.

I also authored the showcase-system lane under `.gsd/feature-plans/showcase-system/`. Those docs are grounded in `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `outputs/exports/eda/manifest.csv`, `.gsd/milestones/M004-fjc2zy/M004-fjc2zy-CONTEXT-DRAFT.md`, `CoWork Planning/yelp_project/docs_agent/AGENTS.md`, and `CoWork Planning/yelp_project/docs/intern/README.md`. I kept the lane explicitly export-driven and local-hosted, treated `outputs/exports/eda/` as the only approved consumption boundary, and reserved the later S04 trust-narrative and intern-explainer surfaces by citing the prior-art docs without drafting that workflow here.

Finally, I extended `tests/test_feature_plan_architecture.py` with Track E and showcase assertions. The new coverage checks structure, milestone cross-links, future-folder labeling, Track E upstream-audit language, showcase export-boundary language, and the required prior-art references that mark the S03/S04 boundary.

## Verification

I ran the task-level targeted pytest selection and the explicit content assertion from the task plan; both passed. I then ran the full current feature-plan pytest file, which now passes with root plus Track A through Track E and showcase coverage.

For slice-level verification, I ran the count-based structure check and the per-slug inventory command from S03. The count check still fails, as expected for an intermediate task, because `multimodal-experiments` is intentionally deferred to T05. The inventory output shows Track E and showcase as populated alongside Tracks A through D, with only the multimodal lane still empty.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_feature_plan_architecture.py -k "track_e or showcase"` | 0 | ✅ pass | 0.07s |
| 2 | `python - <<'PY' ... assert 'M003-rdpeu4' in track_e ... assert 'outputs/exports/eda/manifest.json' in showcase ... assert 'CoWork Planning/yelp_project/docs_agent/AGENTS.md' in showcase ... PY` | 0 | ✅ pass | n/a |
| 3 | `python -m pytest tests/test_feature_plan_architecture.py` | 0 | ✅ pass | 0.03s |
| 4 | `python - <<'PY' ... assert len(feature_plans) == 7 ... PY` | 1 | ❌ fail | n/a |
| 5 | `python - <<'PY' ... print per-slug feature_plan/sprint_docs/phase_docs inventory ... PY` | 0 | ✅ pass | n/a |

## Diagnostics

Inspect `.gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md` first for the upstream-model fairness-audit contract and `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` first for the export-driven showcase boundary. Use `tests/test_feature_plan_architecture.py` to catch drift in file layout, milestone cross-links, prior-art references, or the Track E/showcase framing rules. For partial-slice debugging, rerun the S03 inventory command; it now shows Track A through Track E plus showcase as populated and only the multimodal lane as pending.

## Deviations

I updated `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T04-PLAN.md` before implementation to add the missing observability section required by the pre-flight fix.

## Known Issues

The slice-level count verification still fails because `multimodal-experiments` has not been authored yet. In addition, no upstream Track A or Track D model target is named locally yet for the first real Track E fairness audit, so the Track E plan correctly remains target-gated until T05 or later milestone work supplies that surface.

## Files Created/Modified

- `.gsd/feature-plans/track-e-accountability/FEATURE_PLAN.md` — added the Track E execution plan with upstream-model fairness-audit guardrails, export evidence crosswalk, and future target folders
- `.gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/SPRINT.md` — added the first Track E sprint contract with commands, verification, blockers, and exit criteria
- `.gsd/feature-plans/track-e-accountability/sprints/SPRINT-01-audit-target-selection/phases/PHASE-01-upstream-model-gate.md` — added the first Track E phase handoff for upstream-model-gated accountability execution
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — added the showcase-system execution plan with export-boundary guardrails and reserved S04 references
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md` — added the first showcase sprint contract with commands, verification, blockers, and exit criteria
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md` — added the first showcase phase handoff for export-driven local experience planning
- `tests/test_feature_plan_architecture.py` — extended the architecture regression file with Track E and showcase structure/content assertions
- `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T04-PLAN.md` — added the missing observability section required by the pre-flight fix
- `.gsd/milestones/M001-4q3lxl/slices/S03/S03-PLAN.md` — marked T04 done
