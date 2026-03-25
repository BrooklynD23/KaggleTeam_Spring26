---
id: T02
parent: S03
milestone: M001-4q3lxl
provides:
  - Agent-ready Track A and Track B feature-plan lanes with repo-grounded plan, sprint, phase, and regression coverage surfaces
key_files:
  - .gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md
  - .gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/SPRINT.md
  - .gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/phases/PHASE-01-temporal-baseline-contract.md
  - .gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md
  - .gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/SPRINT.md
  - .gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/phases/PHASE-01-snapshot-baseline-contract.md
  - tests/test_feature_plan_architecture.py
  - .gsd/milestones/M001-4q3lxl/slices/S03/tasks/T02-PLAN.md
key_decisions:
  - Keep both feature plans honest about current export reality by treating missing Track A/B stage artifacts and missing local curated inputs as visible blockers instead of implying the baseline modeling surfaces already exist
patterns_established:
  - Feature-plan docs should pair current export evidence with clearly labeled future target folders and copy-forward guardrail language that downstream agents can reuse verbatim in implementation tasks
observability_surfaces:
  - .gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md
  - .gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md
  - tests/test_feature_plan_architecture.py
  - python inventory diagnostic for per-slug feature-plan/sprint/phase presence
duration: 52m
verification_result: passed
completed_at: 2026-03-21T21:31:44-07:00
blocker_discovered: false
---

# T02: Author Track A and Track B execution plans

**Added Track A and Track B feature-plan, sprint, and phase docs with constraint-aware regression coverage.**

## What Happened

I fixed the task-plan observability gap first by adding `## Observability Impact` to `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T02-PLAN.md`, so the task now explains how future agents inspect these first per-feature lanes and how content drift should fail.

Then I authored the first two real feature-plan folders under `.gsd/feature-plans/`. For Track A, I grounded the plan in `src/eda/track_a/`, `outputs/exports/eda/tracks/track_a/manifest.json`, `outputs/tables/eda_command_checklist.md`, `outputs/tables/track_a_s8_eda_summary.md`, and `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT-DRAFT.md`, while keeping the language explicitly temporal and as-of. The Track A docs also push future modeling work back to `data/curated/review_fact.parquet` and explicitly reject Track B snapshot shortcuts.

For Track B, I created the matching feature-plan, sprint, and phase docs with the same repo-grounded crosswalk, but kept the framing explicitly snapshot-only and age-controlled. The Track B docs name `data/curated/review_fact_track_b.parquet` and `data/curated/snapshot_metadata.json` as the baseline input contract, and they call vote-growth or temporal trend reframing a bug rather than a valid extension.

While authoring the docs, I adapted one local mismatch from the planner snapshot: this worktree has the exported Track A/B summary surfaces and manifests, but most stage artifacts and the local `data/curated/` inputs are absent. I kept the plans honest by describing those as required verification or regeneration inputs instead of pretending the full evidence bundle already exists.

Finally, I rewrote `tests/test_feature_plan_architecture.py` so it still checks the root README contract, allows only canonical feature directories, and now asserts the Track A/B file structure plus key content anchors: export manifests, M002 cross-links, commands, future-target labeling, and the temporal vs. snapshot framing rules.

## Verification

I ran the task-level targeted pytest selection and the explicit content check from the task plan; both passed. I also ran the full current architecture pytest file, which now passes with the root contract plus Track A/B coverage.

For slice-level verification, I ran the count-based structure check and the per-slug inventory command from S03. The count check still fails, as expected for an intermediate task, because only the Track A and Track B lanes exist so far. The inventory output confirms that those two lanes now have complete `FEATURE_PLAN.md`, `SPRINT.md`, and phase-doc surfaces while the remaining five canonical lanes are still empty for T03-T05.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_feature_plan_architecture.py -k "track_a or track_b"` | 0 | ✅ pass | 0.22s |
| 2 | `python - <<'PY' ... assert 'outputs/exports/eda/' in text ... assert 'M002-c1uww6' in text ... PY` | 0 | ✅ pass | 0.03s |
| 3 | `python -m pytest tests/test_feature_plan_architecture.py` | 0 | ✅ pass | 0.23s |
| 4 | `python - <<'PY' ... assert len(feature_plans) == 7 ... PY` | 1 | ❌ fail | 0.03s |
| 5 | `python - <<'PY' ... print per-slug feature_plan/sprint_docs/phase_docs inventory ... PY` | 0 | ✅ pass | 0.03s |

## Diagnostics

Inspect `.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md` first for the Track A temporal/as-of contract and `.gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md` first for the Track B snapshot-only/age-controlled contract. Use `tests/test_feature_plan_architecture.py` to catch drift in file layout or framing language. For partial-slice debugging, rerun the S03 inventory command; it shows which canonical slugs have their `FEATURE_PLAN.md`, sprint docs, and phase docs populated.

## Deviations

I updated `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T02-PLAN.md` before implementation to add the missing `## Observability Impact` section required by the task pre-flight instructions.

## Known Issues

The slice-level count verification still fails because `track-c-monitoring`, `track-d-onboarding`, `track-e-accountability`, `showcase-system`, and `multimodal-experiments` have not been authored yet. In addition, this worktree currently lacks local `data/curated/` inputs, so the Track A/B plans correctly describe curated-table availability as a prerequisite to real modeling execution.

## Files Created/Modified

- `.gsd/feature-plans/track-a-prediction/FEATURE_PLAN.md` — added the Track A execution plan with temporal/as-of guardrails, export evidence crosswalk, and future target folders
- `.gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/SPRINT.md` — added the first Track A sprint contract with commands, verification, blockers, and exit criteria
- `.gsd/feature-plans/track-a-prediction/sprints/SPRINT-01-baseline-modeling/phases/PHASE-01-temporal-baseline-contract.md` — added the first Track A phase handoff for temporal baseline execution
- `.gsd/feature-plans/track-b-surfacing/FEATURE_PLAN.md` — added the Track B execution plan with snapshot-only and age-controlled guardrails
- `.gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/SPRINT.md` — added the first Track B sprint contract with commands, verification, blockers, and exit criteria
- `.gsd/feature-plans/track-b-surfacing/sprints/SPRINT-01-snapshot-ranking-baseline/phases/PHASE-01-snapshot-baseline-contract.md` — added the first Track B phase handoff for snapshot ranking execution
- `tests/test_feature_plan_architecture.py` — replaced the temporary T01-only root test with root-plus-Track-A/B architecture coverage
- `.gsd/milestones/M001-4q3lxl/slices/S03/tasks/T02-PLAN.md` — added the missing observability section required by the pre-flight fix
- `.gsd/milestones/M001-4q3lxl/slices/S03/S03-PLAN.md` — marked T02 done
