# M004-fjc2zy — Research

**Date:** 2026-03-24

## Summary

M004 should begin with a **handoff-surface integrity gate**, not with UI coding.

This worktree currently has strong Python EDA/orchestration code, but the milestone-critical M001–M003 showcase inputs described in project state are **not present here**:

- no `outputs/exports/eda/`
- no `outputs/modeling/`
- no `.gsd/feature-plans/showcase-system/`
- no `src/modeling/`
- no web scaffold (`package.json`, Next.js app)

So the first thing to prove is: **what is the authoritative, reproducible input contract for M004 in this worktree** (or how it will be rehydrated), before deciding IA, animation, or deck tooling.

If that gate is resolved, the natural implementation order is:
1. lock a canonical showcase input contract,
2. scaffold an export-driven local Next.js site,
3. establish single-source narrative continuity for site/report/deck,
4. finish with local-demo verification and governance checks.

---

## Key Findings (Codebase Reality)

### 1) M004 dependencies described in `.gsd` are not materialized in this worktree

Verified missing paths:

- `src/modeling`
- `outputs/exports/eda`
- `outputs/modeling`
- `.gsd/feature-plans`
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`
- `scripts/package_eda_exports.py`
- `scripts/report_eda_completeness.py`
- `tests/test_m002_modeling_contract.py`
- `tests/test_m003_milestone_closeout_gate.py`

Implication: roadmap must include an early **state reconciliation slice** so M004 planning doesn’t depend on references that are absent in this branch/worktree snapshot.

### 2) Current repo is Python-pipeline centric with no web runtime surface yet

Observed:

- No `package.json`, no `next.config.*`, no `app/` or `pages/` frontend tree.
- Existing entrypoints (`scripts/run_pipeline.py`, `scripts/pipeline_dispatcher.py`) orchestrate shared + Track A/B/C/D/E EDA only.
- `requirements.txt` and current codebase are strictly Python analytics-oriented.

Implication: M004 includes **new tech introduction risk** (Node/Next/Motion toolchain + frontend architecture) with no brownfield scaffold to extend.

### 3) Existing patterns strongly favor config-driven, artifact-driven contracts

Reusable patterns already present:

- Stable file-contract style in `scripts/pipeline_dispatcher.py` (`required_outputs` per stage).
- Config loading via `src/common/config.py` (deep-merge inheritance, no hardcoded paths).
- Aggregate-safe, no-raw-text constraints repeated across root and EDA contexts.
- Contract/regression culture via pytest in current pipeline code.

Implication: M004 should reuse this style with a **formal showcase input manifest + required files list**, not ad hoc page-level data loading.

### 4) Governance and boundary constraints are explicit and should be treated as non-negotiable

From requirements and prior milestone summaries:

- Internal only, aggregate-safe (`R013`, `R031`).
- No cloud dependency (`R030`).
- No live analytics backend/querying parquet/duckdb at request time (`R032`).
- Story coherence across five trust functions is a launch requirement (`R012`).

Implication: avoid accidental drift into server API/data-proxy patterns. M004 should be **build-time/static-data consumption only** for website content.

### 5) M004 narrative prior-art contract exists in milestone history, but source docs are missing locally

Milestone histories (M001 S03/S04 summaries) reference canonical showcase docs:

- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`

Those paths are absent in this worktree.

Implication: M004 should include a **narrative-source recovery step** or explicitly replace it with one canonical story source to prevent fragmented site/report/deck messaging.

---

## Technology Research (for New M004 Stack)

### Next.js (App Router + static/local showcase)

From `/vercel/next.js` docs:

- `output: 'export'` is the direct way to produce static output (`out/`) for local hosting.
- App Router server components can fetch data at build time in `next build`.
- Static export supports build-time route handler generation for GET JSON outputs.

M004 relevance:

- Fits local-hosted/non-cloud constraints.
- Encourages artifact-at-build consumption rather than runtime database calls.
- Important limitation: avoid features that require always-on server runtime.

### Motion for React / Framer Motion

From `motion.dev` docs:

- `LazyMotion` + `m` components can significantly reduce initial animation bundle size.
- `useReducedMotion` is built-in for accessibility-sensitive fallback behaviors.

M004 relevance:

- Supports polished narrative transitions without overloading local demo runtime.
- Should include reduced-motion behavior by default to keep demo accessibility and reliability high.

---

## What Should Be Proven First

1. **Input contract integrity for M004**
   - Confirm authoritative local sources for:
     - EDA export bundle (JSON/CSV/PNG/MD)
     - M002 modeling outputs
     - M003 closeout outputs
     - narrative contract docs
2. **One minimal end-to-end local showcase flow**
   - Start app locally.
   - Render one executive page from real exported artifacts.
   - Verify no live parquet/duckdb/database access path exists.
3. **Single-source story continuity mechanism**
   - Ensure site/report/deck all consume the same narrative structure + evidence anchors.

---

## Existing Patterns to Reuse

- **Contract-first file surfaces:** emulate dispatcher-style required artifacts for showcase intake.
- **Config-driven paths:** keep artifact roots configurable instead of hardcoded imports.
- **Fail-closed readiness truth:** treat missing required evidence as explicit blocked state, not silent fallback.
- **Aggregate-safe discipline:** propagate no-raw-text/no-row-level policy into all presentation surfaces.

---

## Boundary Contracts That Matter for M004

### A) Showcase Input Contract (must be explicit)

A single machine-readable intake manifest for website/report/deck build, including:

- required paths
- optional paths
- version/timestamp provenance
- governance markers (`internal`, `aggregate-safe`)
- missing/blocked diagnostics

### B) Website Data Access Contract

- Local static/build-time artifact reads only.
- No runtime reads from parquet, duckdb, or external services.
- Deterministic fallback states for missing artifacts.

### C) Narrative Continuity Contract

- One canonical story schema (prediction/surfacing/onboarding/monitoring/accountability).
- Per-claim evidence pointers (file + section/table/figure).
- Shared section ordering across site/report/deck.

### D) Demo-Readiness Contract

- Local run command(s) for app and optional static serve.
- Smoke assertions (page loads, key sections visible, no failed data loads).
- Explicit failure visibility when evidence inputs are absent.

---

## Known Failure Modes That Should Drive Slice Ordering

1. **Doc-state vs file-state drift** (already visible in this worktree).
2. **Narrative fragmentation** between website/report/deck if no shared source contract.
3. **Overbuilt frontend before evidence wiring** (high polish on unstable/placeholder data).
4. **Accidental live-backend creep** violating R030/R032.
5. **Demo fragility** from missing local runbook and readiness checks.

---

## Requirement Analysis (M004 Focus)

### Table stakes (must land)

- **R011:** local-hosted Next.js + Motion site using exported artifacts.
- **R012:** coherent business-oriented trust story across all final surfaces.
- **R013:** aggregate-safe/internal governance boundary remains intact.

### Continuity expectations from prior milestones

- Consume M003 closeout evidence as authoritative accountability input (when present).
- Preserve Track framing and handoff semantics from M001–M003 artifacts.

### Likely omissions (candidate requirements, not auto-binding)

1. **Candidate requirement:** M004 showcase-input manifest contract.
   - Why: current drift risk is primarily missing/misaligned upstream surfaces.
2. **Candidate requirement:** website/report/deck narrative parity checks.
   - Why: R012 can fail even when individual artifacts look good.
3. **Candidate requirement:** local demo smoke-test command and checklist.
   - Why: launchability should be executable, not implied.
4. **Candidate requirement:** explicit no-live-query verification for web app.
   - Why: protects R032 boundary during future edits.

### Optional/overbuild risks

- Heavy animation systems before data contract stability.
- Inventing CMS/backend for content management.
- Public deployment workflows (explicitly out of scope).

---

## Suggested Slice Boundaries for Roadmap Planner

1. **S1 — M004 intake reconciliation + contract lock** (highest risk)
   - Reconcile missing M001–M003 handoff surfaces in this worktree.
   - Define/show required input manifest and blocked semantics.

2. **S2 — Minimal Next.js local scaffold + static data loader**
   - Bootstrap app with static-export-compatible architecture.
   - Implement one executive narrative page backed by real artifacts.

3. **S3 — Trust-story IA + track drill-down templates**
   - Encode hybrid executive-first/drill-down-second navigation.
   - Attach evidence pointers per section.

4. **S4 — Report + deck continuity pipeline**
   - Build report/deck from the same narrative/evidence source contract.
   - Add parity checks against website claims.

5. **S5 — Demo hardening + governance verification**
   - Local runbook, smoke checks, and no-live-query assertions.
   - Final governance-safe audit of all showcase outputs.

---

## Skill Discovery (suggest)

### Already installed and directly relevant

- `frontend-design`
- `react-best-practices`
- `frontend-patterns`
- `frontend-slides`
- `article-writing`

### External skills discovered (not installed)

For Motion/Framer-specific implementation depth:

- `npx skills add patricio0312rev/skills@framer-motion-animator` (highest installs from search)
- `npx skills add mindrally/skills@framer-motion`
- `npx skills add pproenca/dot-skills@framer-motion`

Recommendation: if M004 heavily depends on animation choreography, the first option is the most promising by adoption count.

---

## Direct Answers to Strategic Questions

- **What should be proven first?**
  - That M004 has authoritative local input artifacts and a locked intake contract in this worktree.

- **What existing patterns should be reused?**
  - Config/contract-driven artifact handling, fail-closed readiness, and aggregate-safe output discipline.

- **What boundary contracts matter?**
  - Showcase input manifest, static-only website data access, narrative continuity schema, and demo-readiness checks.

- **What constraints does the existing codebase impose?**
  - Python-first artifact pipeline, no existing web scaffold, strict governance boundary, and local-only/non-cloud delivery.

- **Known failure modes shaping slice order?**
  - Start with state reconciliation, then data wiring, then storytelling parity, then polish/hardening.

- **Missing/optional/out-of-scope from requirements?**
  - Missing: explicit M004 intake manifest + parity checks + smoke verification.
  - Optional: advanced animation polish.
  - Out-of-scope: cloud hosting, live analytics backend, public release.
