---
estimated_steps: 5
estimated_files: 7
skills_used:
  - frontend-patterns
  - react-best-practices
  - frontend-design
---

# T02: Scaffold the local Next.js showcase shell and intake loader boundary

**Slice:** S01 — Intake-locked showcase shell with visible readiness and blocked states
**Milestone:** M004-fjc2zy

## Description

Create the first runnable Next.js showcase shell under `showcase/` and wire a typed intake loader boundary so homepage rendering is driven by generated intake diagnostics rather than mock placeholders.

## Steps

1. Scaffold a minimal Next.js App Router project in `showcase/` with scripts/dependencies suitable for local development and static-friendly builds.
2. Add base app shell files (`layout.tsx`, `page.tsx`) that establish the homepage frame for readiness-first rendering.
3. Implement `showcase/lib/load-intake.ts` to read and parse `outputs/showcase/intake/manifest.json`, returning a typed fallback payload when the file is missing/unreadable.
4. Add `showcase/components/shell-status.tsx` and wire homepage composition so startup state clearly distinguishes intake-available vs intake-unavailable paths.
5. Add baseline frontend tests that assert shell rendering behavior for both present and missing intake payloads.

## Must-Haves

- [ ] `npm --prefix showcase run dev` launches a local homepage shell.
- [ ] Homepage data flow reads intake state through `showcase/lib/load-intake.ts` (no hardcoded readiness strings).
- [ ] Missing-intake branch renders deterministic fallback status instead of blank/throwing UI.
- [ ] Frontend tests cover both intake-present and intake-missing shell states.

## Verification

- `npm --prefix showcase run test -- --run`
- `npm --prefix showcase run build`

## Observability Impact

- Signals added/changed: explicit shell state labels for `intake_available` vs `intake_unavailable` in rendered UI.
- How a future agent inspects this: run `npm --prefix showcase run dev` and inspect the homepage shell state, plus test output from `npm --prefix showcase run test -- --run`.
- Failure state exposed: loader parse/read failures resolve to a visible fallback branch instead of crashing the homepage render path.

## Inputs

- `.gsd/milestones/M004-fjc2zy/slices/S01/tasks/T01-PLAN.md` — canonical intake contract/output expectations
- `configs/showcase.yaml` — source of required/optional surface keys that loader-rendered UI will display
- `scripts/build_showcase_intake.py` — generator contract for `manifest.json` shape consumed by loader
- `outputs/showcase/intake/manifest.json` — intake payload source for homepage shell state

## Expected Output

- `showcase/package.json` — Next.js showcase scripts and dependencies
- `showcase/next.config.mjs` — local/static-friendly showcase build configuration
- `showcase/tsconfig.json` — TypeScript config for showcase app
- `showcase/app/layout.tsx` — app-wide shell layout
- `showcase/app/page.tsx` — homepage shell entrypoint
- `showcase/lib/load-intake.ts` — typed intake manifest loader with fallback
- `showcase/components/shell-status.tsx` — shell status component reflecting intake availability
