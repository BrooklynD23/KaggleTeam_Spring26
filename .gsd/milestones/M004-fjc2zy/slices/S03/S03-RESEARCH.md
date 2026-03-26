# S03 Research — Track drill-down experience with canonical evidence pointers

## Summary
S03 is a **targeted extension** of the S02 contract-first pattern, not a new architecture. The repo already has:
- canonical intake + story artifact generation (`outputs/showcase/intake`, `outputs/showcase/story`),
- a typed runtime loader with deterministic fallback (`showcase/lib/load-story.ts`),
- executive route rendering + evidence diagnostics components,
- smoke parity checks (`scripts/showcase_smoke_check.py`).

What is missing for S03 is the **track-level contract and routes**: there is no `track` story artifact, no `/tracks/*` pages, and no smoke/test coverage for drill-down parity.

## Requirement Focus (Active requirements this slice owns/supports)
- **Primary ownership:**
  - **R009** fairness/mitigation continuity must stay visible in accountability flow and Track E drill-down readiness/blocked states.
  - **R010** stronger-model/comparator continuity must stay visible in drill-down diagnostics (especially Track A + comparator evidence surfaces).
- **Supports:**
  - **R011** by extending local-hosted runtime with real drill-down routes backed by generated artifacts.
  - **R012** by keeping canonical evidence pointers and narrative ordering aligned between executive + track views.
  - **R013** by preserving governance markers (internal-only, aggregate-safe, raw-review-text disallow) in drill-down surfaces.
  - **R022** by preserving explicit blocked diagnostics for missing M003 closeout surfaces in drill-down evidence rows.

## Skill Notes Applied
- **react-best-practices**
  - `async-parallel`: keep page-level data loading parallelized (`Promise.all`) as already done on homepage; follow same pattern if track pages load multiple artifacts.
  - `server-serialization`: keep drill-down payloads compact and typed in server components; avoid shipping unnecessary large blobs to client components.
- **accessibility**
  - Motion/reduced-motion handling is already in place (`useReducedMotion`, `@media (prefers-reduced-motion: reduce)`); drill-down interactions should preserve this pattern.
  - Keep skip-link + semantic structure (`<main>`, headings) consistent for new routes.

## Skill Discovery (suggest)
Installed and directly relevant:
- `react-best-practices`
- `frontend-patterns`
- `accessibility`

Not installed but relevant for heavier motion choreography (optional):
- `npx skills add patricio0312rev/skills@framer-motion-animator` (highest install count)
- `npx skills add mindrally/skills@framer-motion`

## Implementation Landscape

### Existing contract/generator surfaces (reusable)
- `configs/showcase.yaml`
  - Already defines governance markers and executive story mapping/evidence surface keys.
  - No track drill-down schema yet.
- `src/showcase/intake_contract.py`
  - Canonical surface readiness computation and blocked reason codes.
- `src/showcase/story_contract.py`
  - Executive section builder with strict canonical order and evidence pointer rows.
- `scripts/build_showcase_story.py`
  - Writes `outputs/showcase/story/sections.json` + `validation_report.json`.

### Existing runtime seams (reuse, do not duplicate)
- `showcase/lib/load-story.ts`
  - Typed artifact loader + deterministic fallback behavior.
- `showcase/components/evidence-list.tsx`
  - Already renders machine-parseable evidence pointer rows (`surface_key`, `path`, `reason`, `requirement_key`).
- `showcase/components/executive-flow.tsx`
  - Already handles ordering, status chips, governance strip, reduced-motion transitions.
- `showcase/app/page.tsx` + `showcase/app/executive/page.tsx`
  - Only homepage + executive route currently exist; no track drill-down route tree exists.

### Existing verification seams
- Python contract tests:
  - `tests/test_showcase_intake_contract.py`
  - `tests/test_showcase_story_contract.py`
- Showcase Vitest coverage:
  - `showcase/tests/load-story.test.ts`
  - `showcase/tests/executive-flow.test.tsx`
  - `showcase/tests/homepage-shell.test.tsx`
- Runtime parity checker:
  - `scripts/showcase_smoke_check.py` currently validates homepage + `/executive` only.

### Observed current runtime state
- Only showcase artifacts present under `outputs/` are intake/story JSON outputs.
- Upstream M001–M003 surfaces are still mostly missing, so blocked-state rendering is the normal path right now.
- This makes blocked diagnostics a first-class behavior for S03 verification (not an edge case).

## Natural Seams for Planner Decomposition
1. **Contract extension seam (Python):**
   - Extend `configs/showcase.yaml` with track drill-down definitions + canonical evidence pointers.
   - Add `src/showcase/track_contract.py` (or expand `story_contract.py` carefully) + CLI script to generate `outputs/showcase/story/tracks.json` (+ validation report).
2. **Runtime loader seam (TS):**
   - Add typed loader (`showcase/lib/load-tracks.ts`) mirroring `load-story.ts` fallback semantics.
3. **UI route/component seam (Next):**
   - Add `/tracks` index + per-track route(s) (`/tracks/track-a` … `/tracks/track-e`) with reusable evidence-list rendering and governance markers.
   - Add navigation links from home/executive into drill-down IA.
4. **Verification seam:**
   - Add Python tests for new track contract generator.
   - Add Vitest coverage for loader + drill-down components/routes.
   - Extend `scripts/showcase_smoke_check.py` to assert drill-down parity fields and explicit blocked diagnostics for missing M003 closeout/comparator/fairness surfaces.

## Build/Proof Order (what to prove first)
1. **Contract first:** generate deterministic track artifact with canonical ordering and evidence-pointer rows before touching UI.
2. **Loader second:** ensure typed fallback for missing/invalid track artifact is deterministic.
3. **UI third:** render drill-down routes from generated artifact only (no ad hoc file probing in components).
4. **Smoke last:** verify route-level parity against generated artifacts (same pattern as executive).

## Key Risks / Constraints
- **Most likely failure:** bypassing contract artifacts and directly hardcoding track content in React pages (breaks R012 continuity).
- **Continuity risk:** duplicating evidence row markup instead of reusing `evidence-list.tsx` shape causes parity drift between executive and drill-down surfaces.
- **Governance drift risk:** forgetting governance strip/markers on track pages weakens R013 continuity.
- **S03-specific continuity risk:** missing explicit blocked rows for M003 closeout/comparator/fairness surfaces would regress R022/R009/R010 semantics.

## Verification Plan
Run after S03 implementation:

```bash
# Python contract tests
python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py -q

# Build artifacts
python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake
python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story
python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story

# Frontend tests + build
npm --prefix showcase run test -- --run
npm --prefix showcase run build

# Runtime smoke (extended for drill-down routes)
python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000
```

## Recommendation
Treat S03 as a **contract-extension slice**:
- introduce a canonical track artifact and consume it everywhere,
- keep evidence-pointer field shape identical to S02,
- enforce explicit blocked-state visibility for R009/R010/R022 surfaces in both artifacts and UI,
- then extend smoke parity checks so failures are caught at runtime, not in demo.
