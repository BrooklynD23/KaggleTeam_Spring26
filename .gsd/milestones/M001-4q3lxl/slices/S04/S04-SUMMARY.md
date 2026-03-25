---
id: S04
parent: M001-4q3lxl
milestone: M001-4q3lxl
provides:
  - Export-grounded trust narrative and intern explainer workflow docs discoverable from the canonical showcase lane and protected by pytest
requires:
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/EXPORT_CONTRACT.md
  - outputs/exports/eda/tracks/track_d/manifest.json
  - outputs/exports/eda/tracks/track_e/manifest.json
  - CoWork Planning/yelp_project/docs_agent/AGENTS.md
  - CoWork Planning/yelp_project/docs/intern/README.md
affects:
  - .gsd/feature-plans/showcase-system/FEATURE_PLAN.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md
  - tests/test_trust_narrative_workflow.py
key_files:
  - .gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md
  - .gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md
  - .gsd/feature-plans/showcase-system/FEATURE_PLAN.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md
  - .gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md
  - tests/test_trust_narrative_workflow.py
key_decisions:
  - Keep the S04 content contract inside `.gsd/feature-plans/showcase-system/` rather than creating a parallel planning or intern-doc tree.
  - Ground the trust story in export-manifest truth, including `existing=6`, `missing=109`, the Track D blocker path, and Track E metadata-only validity evidence.
  - Treat the feature, sprint, and phase docs as the canonical discovery surface and use pytest to lock both cross-links and export-boundary language.
patterns_established:
  - Showcase narrative docs must cite exported evidence directly and preserve the `internal` + `aggregate-safe` governance boundary.
  - Intern explainer workflow docs should define invocation triggers, required read-first inputs, outputs, and guardrails using repo-local prior art instead of ad hoc prose.
  - Canonical showcase planning docs should label the S04 docs as the `S04-owned content contract` so later M004 agents discover them without re-research.
observability_surfaces:
  - python -m pytest tests/test_trust_narrative_workflow.py -q
  - .gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md
  - .gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md
  - .gsd/feature-plans/showcase-system/FEATURE_PLAN.md
  - outputs/exports/eda/manifest.json
  - outputs/exports/eda/tracks/track_d/manifest.json
  - outputs/exports/eda/tracks/track_e/manifest.json
duration: 75m
verification_result: passed
completed_at: 2026-03-22T00:12:31-07:00
---

# S04: Trust narrative and intern explainer workflow

**S04 turned the reserved showcase-story seam into a real, export-grounded content contract for later local-showcase work and validated `R004` in practice.**

## What Happened

S04 completed in two task steps.

### T01 — Author export-grounded trust narrative and explainer docs

S04 first created two dedicated showcase-lane documents under `.gsd/feature-plans/showcase-system/`:

- `TRUST_NARRATIVE.md`
- `INTERN_EXPLAINER_WORKFLOW.md`

The trust narrative maps the five story functions directly to the current track/export surfaces:

- prediction → Track A
- surfacing → Track B
- monitoring → Track C
- onboarding → Track D
- accountability → Track E

That document is intentionally honest about the current state. It cites the export bundle root and contract docs, carries forward `existing=6` and `missing=109`, names the Track D dependency on `outputs/tables/track_a_s5_candidate_splits.parquet`, and preserves Track E’s metadata-only validity evidence rather than implying a fuller fairness export than the repo actually has.

The intern explainer workflow formalizes when to invoke an explainer-style agent, what it must read first, what outputs it should produce, and what guardrails it must follow. It inherits the repo’s aggregate-safe/internal boundary and the prior-art expectations from `CoWork Planning/yelp_project/docs_agent/AGENTS.md` and `CoWork Planning/yelp_project/docs/intern/README.md`.

T01 also seeded `tests/test_trust_narrative_workflow.py` so the S04 contract could fail visibly if these new docs or their required evidence markers drifted.

### T02 — Link the showcase lane to the new docs and lock them with pytest

S04 then wired the canonical showcase planning docs back to the new S04 docs:

- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md`
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md`

Those docs now identify `TRUST_NARRATIVE.md` and `INTERN_EXPLAINER_WORKFLOW.md` as the **S04-owned content contract** and preserve the same export-driven local-hosting boundary introduced in S03: the future showcase is local-hosted/internal, reads exported JSON/CSV/PNG/MD artifacts, and does not query live `.parquet` files or DuckDB.

`tests/test_trust_narrative_workflow.py` was then tightened so it protects not just the existence of links, but the key trust and governance markers that make the showcase planning honest and reusable.

## Deliverables

- `TRUST_NARRATIVE.md` — the trust-marketplace story grounded in exported evidence rather than aspiration.
- `INTERN_EXPLAINER_WORKFLOW.md` — the repeatable explainer-agent contract for intern-facing process explanations.
- Updated showcase feature/sprint/phase docs that point future agents to the S04 contract docs immediately.
- `tests/test_trust_narrative_workflow.py` — a dedicated regression harness for the S04 narrative/workflow contract.

## Proof

S04’s contract proof is machine-checkable and passed at task completion:

- `python -m pytest tests/test_trust_narrative_workflow.py -q`
- marker checks for both S04 docs
- showcase-surface presence checks for the canonical feature/sprint/phase docs
- export-manifest diagnostics confirming:
  - `scope == internal`
  - `safety_boundary == aggregate-safe`
  - `status_totals == {'existing': 6, 'missing': 109}`
  - Track D blocker truth remains visible
  - Track E validity evidence remains `metadata_only`

## Diagnostics

Inspect these surfaces first if later work questions the S04 handoff:

- `tests/test_trust_narrative_workflow.py` — exact contract assertions for doc markers, links, and guardrails
- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` — trust-story source of truth
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` — explainer workflow source of truth
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — canonical discovery path into the S04 docs
- `outputs/exports/eda/manifest.json` — root completeness/governance truth
- `outputs/exports/eda/tracks/track_d/manifest.json` — Track D blocker visibility
- `outputs/exports/eda/tracks/track_e/manifest.json` — Track E metadata-only validity evidence

## Forward Intelligence

### What the next slice should know

- S05 should treat the S04 docs as real completion artifacts, not placeholders.
- `R004` is no longer just mapped; its validation story is the combination of S04’s dedicated pytest contract and the later integrated S05 handoff pass.
- Later M004 showcase work should discover S04 through the canonical showcase lane, not by scanning task summaries or prior-art intern docs manually.

### What is still intentionally constrained

- The showcase remains local-hosted and internal-only.
- No live `.parquet` or DuckDB reads were introduced by S04.
- No raw review text or copied `.parquet` / `.ndjson` / `.log` payloads were introduced into the planning surfaces.

### What remains for S05

- Rewrite the doctor-created S04 milestone artifacts into real completion docs.
- Mark `R004` validated in `.gsd/REQUIREMENTS.md` with concrete proof language.
- Run the integrated milestone handoff verification so S04, S05, and the export/planning layers agree in one pass.

## Files Created/Modified

- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` — added the export-grounded trust narrative
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` — added the intern explainer workflow contract
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — linked the canonical feature lane to the S04 contract docs
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md` — linked the sprint doc to the S04 contract docs and preserved guardrails
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md` — linked the phase doc to the S04 contract docs and preserved guardrails
- `tests/test_trust_narrative_workflow.py` — added and then hardened the S04 regression harness
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-PLAN.md` — recorded slice observability and marked T01/T02 complete
- `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T01-PLAN.md` — added missing observability notes during execution
- `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T02-PLAN.md` — added missing observability notes during execution
