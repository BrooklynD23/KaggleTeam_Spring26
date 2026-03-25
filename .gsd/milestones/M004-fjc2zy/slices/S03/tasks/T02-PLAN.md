---
estimated_steps: 12
estimated_files: 8
skills_used:
  - react-best-practices
  - frontend-patterns
  - accessibility
---

# T02: Implement typed track loader and `/tracks` drill-down routes

## Description
Expose the hybrid IA promised by the roadmap by adding track index/detail routes that render from canonical track artifacts and preserve governance + blocked diagnostics in runtime UI.

## Steps
1. Add `showcase/lib/load-tracks.ts` mirroring `load-story.ts` fallback semantics (`tracks_available` / `tracks_unavailable`) with deterministic blocked payloads.
2. Add `showcase/app/tracks/page.tsx` and `showcase/app/tracks/[trackKey]/page.tsx` to render canonical tracks and per-track evidence sections from `tracks.json`.
3. Add/adjust `showcase/components/track-flow.tsx` (and shared composition with `EvidenceList`) so track pages surface `surface_key`, `path`, `reason`, and `requirement_key` exactly as generated.
4. Update `showcase/app/page.tsx` and `showcase/app/executive/page.tsx` with drill-down navigation links while preserving current executive flow behavior.
5. Add `showcase/tests/load-tracks.test.ts` and `showcase/tests/track-flow.test.tsx` coverage for canonical ordering, fallback behavior, governance markers, and blocked evidence rendering.

## Must-Haves
- [ ] `/tracks` and `/tracks/<trackKey>` render from generated artifacts (or deterministic fallback), never live analytics queries.
- [ ] Track pages keep governance markers visible and preserve blocked diagnostics for R009/R010/R022 continuity surfaces.
- [ ] Tests enforce canonical ordering and fail when evidence pointer fields disappear or drift.

## Inputs

- `outputs/showcase/story/tracks.json`
- `showcase/lib/load-story.ts`
- `showcase/components/evidence-list.tsx`
- `showcase/app/page.tsx`
- `showcase/app/executive/page.tsx`

## Expected Output

- `showcase/lib/load-tracks.ts`
- `showcase/app/page.tsx`
- `showcase/app/executive/page.tsx`
- `showcase/app/tracks/page.tsx`
- `showcase/app/tracks/[trackKey]/page.tsx`
- `showcase/components/track-flow.tsx`
- `showcase/tests/load-tracks.test.ts`
- `showcase/tests/track-flow.test.tsx`

## Verification

npm --prefix showcase run test -- --run && npm --prefix showcase run build

## Observability Impact

Signals added/changed: UI-level track status chips and evidence diagnostic rows tied to generated artifact fields.
How a future agent inspects this: open `/tracks` and `/tracks/<trackKey>` plus run `npm --prefix showcase run test -- --run` for parity assertions.
Failure state exposed: fallback shell-state and blocked-evidence diagnostics become visible when track artifact load fails.
