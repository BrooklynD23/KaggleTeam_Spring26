---
id: T02
parent: S04
milestone: M001-4q3lxl
provides:
  - Canonical showcase-doc cross-links plus a pytest contract that locks S04 ownership and export-boundary guardrails to the aggregate-safe export bundle
key_files:
  - .gsd/feature-plans/showcase-system/FEATURE_PLAN.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md
  - tests/test_trust_narrative_workflow.py
  - .gsd/milestones/M001-4q3lxl/slices/S04/tasks/T02-PLAN.md
  - .gsd/milestones/M001-4q3lxl/slices/S04/S04-PLAN.md
key_decisions:
  - Treat the feature, sprint, and phase docs as the canonical discovery surface for the S04 docs and enforce their export-boundary language with pytest markers instead of link-only checks
patterns_established:
  - Showcase handoff docs should name S04-owned contract docs explicitly and pair those links with local-hosted, no-live-parquet/DuckDB guardrail assertions in regression tests
observability_surfaces:
  - tests/test_trust_narrative_workflow.py
  - .gsd/feature-plans/showcase-system/FEATURE_PLAN.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/tracks/track_e/manifest.json
duration: 30m
verification_result: passed
completed_at: 2026-03-22T00:12:31-07:00
blocker_discovered: false
---

# T02: Link the showcase lane to the new docs and lock them with pytest

**Linked the canonical showcase docs to the S04 contract and hardened pytest to catch boundary or trust-drift regressions.**

## What Happened

I first verified the local state against the task contract, prior T01 summary, and the existing pytest style in `tests/test_feature_plan_architecture.py`. The seeded S04 regression file already existed and the showcase feature/sprint/phase docs already contained baseline links in this worktree, so I adapted the task to tighten the written contract instead of redoing the same wiring blindly.

I updated `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, `.../SPRINT.md`, and `.../PHASE-01-export-driven-experience-map.md` so each explicitly calls the trust narrative and intern explainer docs the **S04-owned content contract**. I preserved the existing S03/S04 boundary language: the showcase stays local-hosted and internal, reads exported JSON/CSV/PNG/MD artifacts only, and does not query live `.parquet` files or DuckDB.

I then strengthened `tests/test_trust_narrative_workflow.py`. Instead of checking only that the three canonical docs contain the two S04 links, the test now also asserts the discovery docs preserve the export-governance seams and guardrail phrasing that matter for honest showcase planning: the S04 ownership label, export-contract reference, local-hosted/internal framing, and no-live-parquet/DuckDB boundary language, while still protecting Track D blocker truth and Track E metadata-only validity evidence from the export manifests.

Finally, I fixed the pre-flight plan gap by adding `## Observability Impact` to `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T02-PLAN.md`, making the failure surfaces explicit for future agents: pytest now points to the exact missing link or missing guardrail marker, and the source-of-truth exports remain inspectable through `status_totals`, `blocked_by`, and `metadata_summaries`.

## Verification

I ran the dedicated pytest harness required by the task, the task-plan link-marker check, and the two slice-level verification snippets from `S04-PLAN.md`. All passed. The pytest suite confirms the S04 docs exist and retain their required markers, the canonical showcase docs point back to them and preserve the export boundary, and the export manifests still surface `internal`, `aggregate-safe`, `existing=6`, `missing=109`, the Track D blocker path, and Track E metadata-only validity evidence.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/usr/bin/time -f 'DURATION:%e' python -m pytest tests/test_trust_narrative_workflow.py` | 0 | ✅ pass | 0.20s |
| 2 | `/usr/bin/time -f 'DURATION:%e' python - <<'PY' ... link_targets/markers check for TRUST_NARRATIVE.md and INTERN_EXPLAINER_WORKFLOW.md ... PY` | 0 | ✅ pass | 0.03s |
| 3 | `/usr/bin/time -f 'DURATION:%e' python - <<'PY' ... showcase narrative surface presence check ... PY` | 0 | ✅ pass | 0.04s |
| 4 | `/usr/bin/time -f 'DURATION:%e' python - <<'PY' ... export manifest diagnostics for scope, safety boundary, status totals, Track D blocker, and Track E metadata_only validity ... PY` | 0 | ✅ pass | 0.04s |

## Diagnostics

The fastest regression surface is `tests/test_trust_narrative_workflow.py`: it now fails on exact missing markers in the feature/sprint/phase docs rather than only telling a future agent that "something drifted." To inspect the evidence side directly, read `outputs/exports/eda/manifest.json` for `scope`, `safety_boundary`, `status_totals`, and Track D `blocked_by`, then read `outputs/exports/eda/tracks/track_e/manifest.json` for the `metadata_summaries` entry with `export_mode: metadata_only`.

## Deviations

The local worktree already contained baseline cross-links from the canonical showcase docs to the S04 docs before I edited it, so I treated the main implementation gap as contract-hardening rather than initial link insertion. I still updated the three docs to make the S04 ownership explicit and expanded the pytest assertions so the task now enforces the stronger final-state contract described in the plan.

## Known Issues

None.

## Files Created/Modified

- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — Strengthened the showcase root doc to label the trust narrative and intern explainer as the S04-owned content contract.
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md` — Strengthened the sprint handoff wording so S04 ownership is explicit alongside the export-driven boundary.
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md` — Strengthened the phase handoff wording to preserve the same S04 ownership and boundary language.
- `tests/test_trust_narrative_workflow.py` — Expanded the regression harness to assert canonical-doc guardrails, not just S04 cross-link presence.
- `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T02-PLAN.md` — Added the missing Observability Impact section called out by the pre-flight contract.
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-PLAN.md` — Marked T02 complete in the slice task checklist.
