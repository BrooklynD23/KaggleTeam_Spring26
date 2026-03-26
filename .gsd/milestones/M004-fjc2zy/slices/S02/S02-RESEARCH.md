# S02 Research — Executive trust-story flow from real exported artifacts

**Date:** 2026-03-24
**Slice:** M004-fjc2zy / S02

## Summary

S02 is a **targeted-to-deep integration slice**: the Next.js shell exists (from S01), but there is no executive narrative surface yet, no Motion dependency, and no static story artifact contract beyond intake diagnostics.

The fastest safe path is to keep S01’s contract-first pattern and add a second generated artifact layer for executive sections:

1. Generate a canonical executive-story payload from static files (primarily `outputs/showcase/intake/*.json` plus any available upstream exported surfaces).
2. Render an executive-first page flow from that payload with deterministic blocked states per section.
3. Add Motion transitions with a reduced-motion fallback baked in.
4. Keep all claims evidence-addressable (`surface_key`, `path`, `requirement_key`) so S03/S04 can reuse them.

This lets S02 advance the narrative now even while upstream evidence is missing in this worktree.

---

## Requirement targeting (active requirements relevant to S02)

- **Primary owner:** **R011** (local-hosted Next.js + Motion showcase runtime)
- **Direct support:** **R012** (coherent trust-marketplace narrative continuity)
- **Continuity support:** **R009**, **R010** (consume fairness/comparator evidence surfaces, even if blocked)
- **Governance continuity support:** **R013** (internal-only, aggregate-safe markers remain visible)
- **Blocked-surface continuity from S01:** **R022** (closeout surfaces remain visible when missing)

Implication: S02 should not hide missing evidence. It should render sections with explicit readiness/blocked evidence cards.

---

## Implementation landscape (what exists now)

### Existing S01 runtime surfaces

- `showcase/app/page.tsx`
  - Single homepage currently rendering S01 shell copy + `<ReadinessPanel />`
- `showcase/lib/load-intake.ts`
  - Typed intake loader, deterministic fallback (`intake_unavailable`, `INTAKE_MANIFEST_UNAVAILABLE`)
- `showcase/components/readiness-panel.tsx`
  - Renders status counts and blocked rows with machine-parseable fields
- `outputs/showcase/intake/manifest.json`
- `outputs/showcase/intake/validation_report.json`

### Existing verification surfaces

- Frontend tests: `showcase/tests/*.test.ts(x)`
- Runtime smoke: `scripts/showcase_smoke_check.py`
- Runbook: `docs/showcase_local_runbook.md`

### Gaps blocking S02 goals

- No executive-story schema/artifact contract yet
- No per-section evidence mapping contract
- No Motion package/dependency
- No reduced-motion behavior implementation
- No executive route structure (prediction/surfacing/onboarding/monitoring/accountability)
- `showcase/next.config.mjs` is `output: 'standalone'` (works for local server runtime but does not prove static-export path)

---

## Key findings that shape task order

1. **Only intake artifacts are present under `outputs/` in this worktree.**
   - `find outputs -maxdepth 4 -type f` returns only intake JSON files.
   - S02 must be resilient to absent upstream exports and still prove executive-flow behavior.

2. **The current homepage is S01-specific and not reusable as executive IA yet.**
   - Hardcoded "M004 · S01" and shell copy in `showcase/app/page.tsx`.

3. **S01 already established the right contract pattern.**
   - Python generator + deterministic JSON + typed TS loader + runtime fallback + smoke checker.
   - Reusing this pattern for executive narrative minimizes risk and keeps continuity with S03/S04.

4. **Governance markers already exist in manifest and should be surfaced in story UI.**
   - `manifest.governance` includes `internal_only`, `aggregate_safe`, `raw_review_text_allowed`.

5. **Project-state drift exists between docs and local files.**
   - `.gsd/PROJECT.md` claims many exported/modeling outputs exist, but they are absent in this worktree snapshot.
   - S02 must treat local filesystem truth as authoritative and visibly blocked where inputs are missing.

---

## Skill-informed guidance (explicit rules referenced)

### Installed skills to apply

- **react-best-practices**
  - Use `async-parallel` for independent file reads in server components/loaders.
  - Keep payloads small per `server-serialization` (don’t pass full manifests to client components).
  - Consider `bundle-dynamic-imports` if Motion-heavy section components grow large.
- **accessibility**
  - Respect reduced motion (WCAG motion guidance) and provide meaningful non-motion state changes.
  - Preserve semantic headings/landmarks and visible focus styles.

### Non-installed but relevant skill discovered

- Framer/Motion depth skill candidates (from `npx skills find "framer motion"`):
  - `npx skills add patricio0312rev/skills@framer-motion-animator` (highest installs)
  - `npx skills add mindrally/skills@framer-motion`
  - `npx skills add pproenca/dot-skills@framer-motion`

(Do not install during planning; user decides.)

---

## Library docs notes (Context7)

### Motion

- `useReducedMotion` allows per-user reduced motion fallback.
- `MotionConfig reducedMotion="user"` can enforce reduced-motion behavior globally.

### Next.js

- App Router server components can fetch/build static data at build time.
- `output: 'export'` is the static-export mode (no server runtime features).

Practical S02 implication: build narrative from static artifact reads and avoid runtime analytics/data services.

---

## Natural seams for planner decomposition

### Seam A — Executive narrative contract + data build

**Purpose:** introduce canonical section/evidence payload for website consumption.

Likely files:
- `configs/showcase.yaml` (optional: add executive section mapping)
- `scripts/build_showcase_story.py` (new)
- `src/showcase/story_contract.py` (new)
- `outputs/showcase/story/sections.json` (generated)
- `tests/test_showcase_story_contract.py` (new)

Notes:
- Keep section keys fixed: `prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`.
- Each section should include `status`, `headline`, `summary`, and `evidence[]` rows with `surface_key/path/requirement_key/reason`.

### Seam B — Next.js executive IA + loaders

**Purpose:** render executive-first flow from generated/static artifacts.

Likely files:
- `showcase/app/page.tsx` (convert to executive landing entry)
- `showcase/app/executive/page.tsx` (new, optional)
- `showcase/components/executive-flow.tsx` (new)
- `showcase/components/evidence-list.tsx` (new)
- `showcase/lib/load-story.ts` (new)

Notes:
- Keep server-side loader fallback behavior deterministic (mirror `load-intake.ts` design).
- Retain direct links/pointers to intake diagnostics so blocked claims stay inspectable.

### Seam C — Motion + reduced-motion accessibility

**Purpose:** add transitions without violating accessibility/usability.

Likely files:
- `showcase/package.json` (Motion dependency)
- `showcase/components/executive-flow.tsx`
- `showcase/app/layout.tsx` (optional global MotionConfig wrapper)
- `showcase/app/globals.css` (fallback visual states/focus)

Notes:
- Default to subtle transitions and preserve content parity when motion is reduced.
- Reduced-motion mode should still communicate section progression.

### Seam D — Verification and smoke extension

**Purpose:** prove S02 behavior from real artifacts with blocked-state visibility.

Likely files:
- `showcase/tests/executive-flow.test.tsx` (new)
- `showcase/tests/homepage-shell.test.tsx` (update)
- `scripts/showcase_smoke_check.py` (extend to executive headings/section evidence checks)
- `docs/showcase_local_runbook.md` (add S02 verification steps)

Notes:
- Assertions should verify section headings + at least one evidence pointer field per section.

---

## What to prove first (risk retirement order)

1. **Story contract determinism** (JSON shape and blocked semantics stable)
2. **Executive UI rendering from real generated artifacts** (not mock literals)
3. **Reduced-motion behavior** (no inaccessible transition-only meaning)
4. **Smoke parity checks against artifacts** (UI truth matches JSON truth)

---

## Verification contract for S02 (recommended commands)

- `python -m pytest tests/test_showcase_story_contract.py -q`
- `python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story`
- `npm --prefix showcase run test -- --run`
- `npm --prefix showcase run build`
- `npm --prefix showcase run dev` (separate terminal)
- `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000` (extended for executive checks)

Optional static-boundary proof (recommended for S02/S05 continuity):
- Build and serve static export path once `next.config` strategy is finalized.

---

## Risks / watchouts for executor

- **Config drift risk:** duplicating section mapping in TS and Python; keep one canonical source.
- **Narrative drift risk:** hand-written section copy can diverge from evidence pointers.
- **A11y regression risk:** motion-only transitions without reduced-motion fallback.
- **Boundary regression risk:** introducing route handlers/API calls that look like live analytics runtime.

---

## Recommendation

Plan S02 around a **new generated story contract** consumed by a **server-rendered executive flow** with **Motion + reduced-motion fallback** and **artifact-parity smoke checks**.

This is the shortest path to advancing R011 now while building the continuity scaffolding S03/S04 need.

---

## Sources

- Local code surfaces:
  - `showcase/app/page.tsx`
  - `showcase/lib/load-intake.ts`
  - `showcase/components/readiness-panel.tsx`
  - `showcase/next.config.mjs`
  - `scripts/showcase_smoke_check.py`
  - `outputs/showcase/intake/manifest.json`
- Context7 docs:
  - Motion (`/websites/motion_dev`) — `useReducedMotion`, `MotionConfig reducedMotion="user"`
  - Next.js (`/vercel/next.js`) — static export and App Router build-time data behavior
- Skills:
  - Installed: `react-best-practices`, `accessibility`
  - Discovery: `npx skills find "framer motion"`
