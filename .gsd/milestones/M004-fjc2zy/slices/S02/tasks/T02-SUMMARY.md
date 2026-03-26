---
id: T02
parent: S02
milestone: M004-fjc2zy
key_files:
  - showcase/package.json
  - showcase/package-lock.json
  - showcase/lib/load-story.ts
  - showcase/app/page.tsx
  - showcase/app/executive/page.tsx
  - showcase/components/executive-flow.tsx
  - showcase/components/evidence-list.tsx
  - showcase/app/layout.tsx
  - showcase/app/globals.css
  - showcase/tests/executive-flow.test.tsx
  - showcase/tests/homepage-shell.test.tsx
key_decisions:
  - Added `framer-motion` and implemented reduced-motion-aware transitions in the executive flow, with a stable no-motion path when user preference requests reduced motion.
  - Implemented a deterministic `load-story` fallback that preserves canonical executive section ordering and explicit blocked evidence diagnostics when story artifacts are unavailable.
  - Exposed governance and evidence diagnostics directly in UI components to satisfy runtime observability expectations without relying on synthesized mock content.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T04:10:50.363Z
blocker_discovered: false
---

# T02: Implement executive-first Next.js story flow with motion-safe transitions, deterministic story fallback loading, and runtime diagnostics tests.

**Implement executive-first Next.js story flow with motion-safe transitions, deterministic story fallback loading, and runtime diagnostics tests.**

## What Happened

Implemented the S02/T02 executive runtime in `showcase` end-to-end using generated story artifacts rather than hardcoded narrative content. I added `framer-motion` to the app dependencies and introduced `showcase/lib/load-story.ts`, a typed loader that reads `outputs/showcase/story/sections.json` with deterministic fallback semantics: canonical section order is preserved and blocked evidence diagnostics remain explicit if the story artifact is missing. I evolved routing by updating `showcase/app/page.tsx` to be an executive-first entrypoint while retaining readiness diagnostics, and added `showcase/app/executive/page.tsx` as the dedicated narrative route. I implemented `showcase/components/executive-flow.tsx` to render canonical sections, status rollups, governance markers, and evidence diagnostics from the story contract, and added `showcase/components/evidence-list.tsx` for per-evidence blocked/required surfaces (`surface_key`, `path`, `reason`, `requirement_key`) visibility. I updated `showcase/app/layout.tsx` and `showcase/app/globals.css` for accessibility and reduced-motion-safe behavior (skip link, focus-visible styling, and `prefers-reduced-motion` handling), while the runtime flow also uses Motion’s reduced-motion preference to suppress transitions when requested. I added/updated tests in `showcase/tests/executive-flow.test.tsx` and `showcase/tests/homepage-shell.test.tsx` to verify canonical section rendering, blocked diagnostics exposure, governance visibility, executive-first navigation, and reduced-motion mode behavior.

## Verification

Task-level verification passed: `npm --prefix showcase run test -- --run && npm --prefix showcase run build` completed successfully with all showcase tests passing and Next.js build succeeding. Slice-level checks were run as required in this intermediate task: story contract pytest and story artifact build commands passed, and showcase test/build commands passed. The smoke-check command remains failing for the already-known CLI mismatch (`showcase_smoke_check.py` does not accept `--story` yet), consistent with prior task findings and expected to be addressed downstream.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `.venv-local/bin/python -m pytest tests/test_showcase_story_contract.py -q` | 0 | ✅ pass | 241ms |
| 2 | `.venv-local/bin/python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && test -f outputs/showcase/story/sections.json && test -f outputs/showcase/story/validation_report.json` | 0 | ✅ pass | 65ms |
| 3 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1657ms |
| 4 | `npm --prefix showcase run build` | 0 | ✅ pass | 24919ms |
| 5 | `.venv-local/bin/python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000` | 2 | ❌ fail | 52ms |
| 6 | `npm --prefix showcase run test -- --run && npm --prefix showcase run build` | 0 | ✅ pass | 17419ms |


## Deviations

Used `.venv-local/bin/python` for Python verification commands to match the project virtualenv/tooling availability in this environment.

## Known Issues

`scripts/showcase_smoke_check.py` still rejects the `--story` argument from the slice verification command (`error: unrecognized arguments: --story ...`).

## Files Created/Modified

- `showcase/package.json`
- `showcase/package-lock.json`
- `showcase/lib/load-story.ts`
- `showcase/app/page.tsx`
- `showcase/app/executive/page.tsx`
- `showcase/components/executive-flow.tsx`
- `showcase/components/evidence-list.tsx`
- `showcase/app/layout.tsx`
- `showcase/app/globals.css`
- `showcase/tests/executive-flow.test.tsx`
- `showcase/tests/homepage-shell.test.tsx`
