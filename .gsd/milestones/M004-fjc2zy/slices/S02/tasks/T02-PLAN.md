---
estimated_steps: 6
estimated_files: 10
skills_used:
  - react-best-practices
  - accessibility
  - frontend-patterns
---

# T02: Build executive-first Next.js flow with Motion and reduced-motion-safe behavior

Implement the executive narrative runtime surface in Next.js using generated story artifacts (not hardcoded text), with Motion transitions that preserve comprehension under reduced motion.

1. Add Motion dependency in `showcase/package.json` and create typed loader `showcase/lib/load-story.ts` with deterministic fallback semantics.
2. Evolve `showcase/app/page.tsx` and add `showcase/app/executive/page.tsx` to establish executive-first routing while retaining readiness entrypoints.
3. Implement `showcase/components/executive-flow.tsx` and `showcase/components/evidence-list.tsx` for canonical section/evidence rendering.
4. Apply reduced-motion-safe behavior and styling updates in `showcase/app/layout.tsx` and `showcase/app/globals.css`.
5. Add/update tests in `showcase/tests/executive-flow.test.tsx` and `showcase/tests/homepage-shell.test.tsx` for section order, blocked diagnostics, governance visibility, and reduced-motion behavior.

## Inputs

- `outputs/showcase/story/sections.json`
- `outputs/showcase/intake/manifest.json`
- `showcase/lib/load-intake.ts`
- `showcase/components/readiness-panel.tsx`
- `showcase/app/page.tsx`

## Expected Output

- `showcase/package.json`
- `showcase/lib/load-story.ts`
- `showcase/app/page.tsx`
- `showcase/app/executive/page.tsx`
- `showcase/components/executive-flow.tsx`
- `showcase/components/evidence-list.tsx`
- `showcase/app/layout.tsx`
- `showcase/app/globals.css`
- `showcase/tests/executive-flow.test.tsx`
- `showcase/tests/homepage-shell.test.tsx`

## Verification

npm --prefix showcase run test -- --run && npm --prefix showcase run build

## Observability Impact

Adds UI-visible section/evidence diagnostics and reduced-motion-safe executive transitions for runtime inspection.
