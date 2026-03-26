---
id: T01
parent: S04
milestone: M001-4q3lxl
provides:
  - Export-grounded trust narrative and explainer workflow docs for the showcase lane, plus the seeded pytest drift harness for later cross-link enforcement
key_files:
  - .gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md
  - .gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md
  - tests/test_trust_narrative_workflow.py
  - .gsd/milestones/M001-4q3lxl/slices/S04/S04-PLAN.md
  - .gsd/milestones/M001-4q3lxl/slices/S04/tasks/T01-PLAN.md
key_decisions:
  - Seed the slice pytest harness in T01 with final-state cross-link assertions so the contract fails visibly until T02 wires the canonical showcase docs
patterns_established:
  - Showcase narrative docs must cite export manifests and summaries directly, preserve internal aggregate-safe wording, and surface blockers/metadata-only evidence without paraphrase drift
observability_surfaces:
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/EXPORT_CONTRACT.md
  - outputs/exports/eda/tracks/track_d/manifest.json
  - outputs/exports/eda/tracks/track_e/manifest.json
  - tests/test_trust_narrative_workflow.py
duration: 45m
verification_result: partial
completed_at: 2026-03-21T21:31:44-07:00
blocker_discovered: false
---

# T01: Author export-grounded trust narrative and explainer docs

**Added export-grounded trust narrative and intern explainer workflow docs, and seeded the slice drift test with the expected pre-T02 cross-link failure.**

## What Happened

I read the current showcase lane plan, the export bundle contract, the per-track exported summaries/manifests, and the prior-art intern documentation guidance before drafting anything. I then fixed the pre-flight observability gaps in `.gsd/milestones/M001-4q3lxl/slices/S04/S04-PLAN.md` and `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T01-PLAN.md` so the slice now names its machine-checkable status surfaces, redaction constraints, and failure visibility.

For deliverables, I created `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` as the honest five-function story: prediction → surfacing → monitoring → onboarding → accountability mapped to `track_a` through `track_e`, with explicit references to `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `existing=6`, `missing=109`, the Track D blocker at `outputs/tables/track_a_s5_candidate_splits.parquet`, and Track E’s metadata-only validity evidence.

I also created `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` to formalize when an explainer-style agent should run, the required read-first inputs, the glossary-first/plain-language explanation order, expected outputs, and guardrails that preserve the internal aggregate-safe boundary and forbid raw review text or new live-data surfaces.

Because this is the first task in the slice and the slice verification already promised a dedicated pytest harness, I created `tests/test_trust_narrative_workflow.py` now rather than leaving the verification file missing. The test file validates the new docs and export honesty, and it intentionally asserts the final T02 cross-links from `FEATURE_PLAN.md`, `SPRINT.md`, and `PHASE-01-export-driven-experience-map.md`, so the suite fails visibly until T02 completes that wiring.

## Verification

I ran the task-level marker check for both new docs, a slice-level diagnostic check against the export manifests, the slice-level presence check for the showcase planning surfaces, and the newly created pytest harness.

Results:

- The new trust narrative and explainer workflow docs passed their required marker checks.
- The export-manifest diagnostics passed, confirming `internal`, `aggregate-safe`, `existing=6`, `missing=109`, Track D’s blocker path, and Track E’s `metadata_only` validity summary.
- The required showcase planning files are present.
- `python -m pytest tests/test_trust_narrative_workflow.py -q` fails in the expected place because the canonical showcase docs do not yet link to the new S04 docs; that work is owned by T02.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python - <<'PY' ... required marker check for TRUST_NARRATIVE.md and INTERN_EXPLAINER_WORKFLOW.md ... PY` | 0 | ✅ pass | 0.02s |
| 2 | `python - <<'PY' ... export manifest diagnostics for scope, safety boundary, status totals, Track D blocker, and Track E metadata_only validity ... PY` | 0 | ✅ pass | 0.03s |
| 3 | `python - <<'PY' ... showcase narrative surface presence check ... PY` | 0 | ✅ pass | 0.02s |
| 4 | `python -m pytest tests/test_trust_narrative_workflow.py -q` | 1 | ❌ fail | 0.18s |

## Diagnostics

Future agents can inspect the slice state from `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `outputs/exports/eda/tracks/track_d/manifest.json`, and `outputs/exports/eda/tracks/track_e/manifest.json`. The seeded regression surface is `tests/test_trust_narrative_workflow.py`: the first two tests confirm the new docs and export honesty, and the failing cross-link test shows exactly what T02 still needs to wire into `FEATURE_PLAN.md`, `SPRINT.md`, and `PHASE-01-export-driven-experience-map.md`.

## Deviations

I made one intentional execution adjustment: I created `tests/test_trust_narrative_workflow.py` during T01 even though T02 formally owns the finished harness, because the auto-mode instructions required the first task in the slice to create planned verification files rather than leaving the slice with a missing promised test.

## Known Issues

- `tests/test_trust_narrative_workflow.py` currently fails on the canonical-doc cross-link assertions because `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, `.../SPRINT.md`, and `.../PHASE-01-export-driven-experience-map.md` do not yet reference `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` and `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`.
- Full slice verification is therefore only partial at the end of T01, which is expected for this intermediate task.

## Files Created/Modified

- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` — New export-grounded trust narrative mapping the five trust functions to Tracks A–E with current-state honesty and governance guardrails.
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` — New workflow doc defining when to invoke the explainer, required inputs, explanation order, outputs, and guardrails.
- `tests/test_trust_narrative_workflow.py` — Seeded pytest drift harness covering doc markers, export diagnostics, and the still-failing T02 cross-link contract.
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-PLAN.md` — Added observability/diagnostics coverage, an inspectable diagnostic verification step, and marked T01 complete.
- `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T01-PLAN.md` — Added the missing Observability Impact section for future agents.
