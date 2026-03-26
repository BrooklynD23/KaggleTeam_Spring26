# M004-fjc2zy: Local showcase, report, and presentation system

**Vision:** Deliver a local, demo-ready showcase system where the website, final report, and final deck all tell one coherent trust-marketplace story from the same exported evidence surfaces.

## Decomposition Reasoning

This roadmap is ordered by failure risk, not by implementation comfort:

1. The highest risk is **handoff-surface drift** (research already found missing expected M001–M003 paths in this worktree), so Slice 1 ships a real user-facing showcase shell with explicit intake status and blocked-state visibility.
2. Once intake truth is visible and stable, Slice 2 ships the real executive story flow through the same static artifact path.
3. Slice 3 adds track drill-downs so the hybrid IA (executive-first, drill-down-second) becomes a usable product, not just a landing page.
4. Slice 4 enforces narrative continuity by making report/deck consume the same canonical story/evidence source as the website.
5. Slice 5 is the explicit integration/hardening slice proving end-to-end assembled reality in the local runtime with governance-safe boundaries.

This grouping ensures each slice is demoable through the real interface and establishes a stable downstream contract.

## Success Criteria

- Running one local command boots a Next.js showcase that renders with real exported artifacts (or explicit blocked states when artifacts are missing).
- The site presents a trust-marketplace executive narrative first and supports track drill-down pages second.
- Every major claim shown on site/report/deck has an evidence pointer to concrete exported artifacts.
- The final report and presentation deck are generated from the same canonical narrative/evidence contract as the website.
- Local demo verification proves the assembled system works without cloud hosting and without live parquet/duckdb/database queries at request time.
- Governance boundaries remain visible and enforced (internal-only, aggregate-safe, no raw review text).

## Current Worktree Baseline

- No existing Next.js scaffold is present.
- M001–M003 handoff artifacts described in milestone history are not fully materialized in this worktree snapshot.
- The codebase is Python-first and contract-driven; this pattern should be reused for showcase intake and validation.

## Key Risks / Unknowns

- **Intake drift risk:** expected M001–M003 evidence surfaces may be absent or inconsistent in this worktree.
- **Narrative fragmentation risk:** site/report/deck can diverge without a single canonical story source.
- **Static-boundary regression risk:** accidental runtime analytics querying would violate local showcase constraints.
- **Demo fragility risk:** no clear smoke path means a polished UI can still fail in live presentation.

## Proof Strategy

- Prove intake truth through a real showcase shell that visibly reports readiness/blocked diagnostics from a canonical intake manifest.
- Prove user value early by shipping a real executive narrative page backed by exported artifacts.
- Prove hybrid IA by shipping track drill-down pages tied to evidence pointers.
- Prove continuity by generating report/deck from the exact same narrative/evidence contract as the site.
- Prove launchability via an end-to-end local demo runbook plus explicit no-live-query and governance assertions.

## Verification Classes

- **Contract verification:** intake manifest schema, required-path diagnostics, evidence-pointer validity.
- **Integration verification:** local app runtime + static artifact loading across executive and track views.
- **Continuity verification:** parity checks that site/report/deck sections and evidence anchors agree.
- **Operational verification:** local demo smoke checks and failure visibility when inputs are missing.
- **Governance verification:** no raw-text leakage and internal/aggregate-safe boundary assertions.

## Milestone Definition of Done

This milestone is complete only when all are true:

- all roadmap slices are complete
- a local-hosted website runs with the hybrid executive-first + drill-down IA
- the website consumes exported/static artifacts and does not perform live analytics queries at runtime
- the final report and deck exist and are materially aligned to the same trust narrative and evidence anchors as the site
- local demo runbook + smoke checks pass and surface failures explicitly when artifacts are missing
- governance-safe/internal-only boundaries are preserved across site/report/deck outputs

## Requirement Coverage

### Primary mapping

| Requirement | Disposition in M004 | Primary owner | Supporting slices | Notes |
|---|---|---|---|---|
| R011 | mapped | S02 | S01,S03,S05 | Local-hosted Next.js + Motion showcase using exported artifacts. |
| R012 | mapped | S04 | S02,S03,S05 | Single-source trust narrative continuity across site/report/deck. |
| R013 | mapped (governance continuity) | S05 | S01,S02,S03,S04 | Keep internal-only + aggregate-safe boundary visible and enforced in all surfaces. |
| R022 | mapped (conditional continuity) | S05 | S01 | Preserve closeout compute-escalation semantics as consumed evidence in showcase narrative/runbook. |
| R009 | mapped (read-only upstream continuity) | S03 | S02,S04 | Fairness+mitigation story is consumed from M003 evidence, not reimplemented in M004. |
| R010 | mapped (read-only upstream continuity) | S03 | S02,S04 | Stronger-model materiality/adoption evidence is consumed from M003 comparator outputs. |

### Coverage summary

- Active requirements with M004 relevance mapped: **R011, R012, R013, R022, R009, R010**
- Deferred from M004: **none**
- Blocked: **none (but S01 must make missing upstream artifacts explicit in UI + diagnostics)**
- Out of scope for this milestone: **public hosting and live analytics backend behavior (R030/R031/R032 boundaries remain excluded)**

## Slices

- [x] **S01: Intake-locked showcase shell with visible readiness and blocked states** `risk:high` `depends:[]`
  > After this: stakeholders can run the local app and see a real homepage shell that reads a canonical showcase intake manifest, listing ready/missing evidence surfaces and explicit blocked diagnostics instead of silent placeholders.

- [x] **S02: Executive trust-story flow from real exported artifacts** `risk:high` `depends:[S01]`
  > After this: stakeholders can navigate an executive-first narrative (prediction, surfacing, onboarding, monitoring, accountability) with real charts/tables/summary content loaded from static exports and motion-enhanced transitions that remain usable with reduced-motion preferences.

- [x] **S03: Track drill-down experience with canonical evidence pointers** `risk:medium` `depends:[S02]`
  > After this: stakeholders can open per-track drill-down pages and inspect canonical metrics/figures plus explicit evidence pointers back to exported artifacts and M003 closeout surfaces.

- [x] **S04: Report and deck generated from shared narrative/evidence source** `risk:medium` `depends:[S02,S03]`
  > After this: stakeholders can build the final report and presentation deck that mirror site section ordering, claims, and evidence anchors from one shared narrative contract rather than parallel manually curated copies.

- [x] **S05: Integrated local demo hardening and governance gate** `risk:medium` `depends:[S01,S02,S03,S04]`
  > After this: one end-to-end local demo path proves website + report + deck assembled reality, including smoke checks, parity checks, no-live-query assertions, and governance-safe output verification.

## Boundary Map

### S01 → S02

Produces:
- canonical showcase intake manifest (required/optional surfaces, readiness, blocked diagnostics)
- UI-visible blocked/fallback state contract
- configured artifact-root resolution contract for local runtime

Consumes:
- upstream M001–M003 exported/modeling evidence surfaces

### S02 → S03

Produces:
- executive narrative section schema and ordering
- artifact loader primitives for static JSON/CSV/PNG/MD surfaces
- motion/accessibility baseline patterns for page transitions

Consumes from S01:
- intake readiness diagnostics and canonical artifact roots

### S02,S03 → S04

Produces:
- canonical story/evidence mapping contract reused by report/deck generation
- claim-to-evidence pointer surfaces verified against real artifacts

Consumes:
- executive flow and track drill-down evidence structures

### S04 → S05

Produces:
- final report artifact
- final deck artifact
- parity-check outputs against website story/evidence map

Consumes:
- shared narrative/evidence source and website section map

### S01,S02,S03,S04 → S05

Produces:
- integrated local-demo runbook and smoke verification outputs
- governance/no-live-query verification evidence
- final handoff checklist for milestone closeout

Consumes:
- all prior slice outputs through the real local entrypoint

## Planned Observability Surfaces

- Showcase intake manifest + validation report under a dedicated showcase artifacts path.
- Local smoke-check command outputs for site startup, route visibility, and asset-load failures.
- Narrative parity check output comparing website/report/deck claims and evidence anchors.
- Governance check output confirming no raw review text and internal/aggregate-safe markers.

## Skill Discovery Notes

Directly relevant installed skills (already available):
- `frontend-design`
- `react-best-practices`
- `frontend-patterns`
- `frontend-slides`
- `article-writing`

Potential external Motion depth skill (not installed, optional):
- `npx skills add patricio0312rev/skills@framer-motion-animator`

## Out-of-Scope Guardrails

- No public cloud hosting setup as part of M004 delivery.
- No live analytics backend/API that queries parquet/duckdb/database at request time.
- No publication of raw Yelp data or row-level derived content.
- No re-implementation of M003 fairness/comparator modeling logic inside showcase runtime.
