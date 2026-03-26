---
id: T02
parent: S01
milestone: M004-fjc2zy
provides:
  - A runnable Next.js App Router showcase shell under `showcase/` with a homepage frame wired to real intake diagnostics.
  - A typed intake loader boundary that reads `outputs/showcase/intake/manifest.json` and returns a deterministic fallback on read/parse failure.
  - Baseline frontend regression coverage for intake-present and intake-missing shell states, including explicit `intake_unavailable` verification filtering.
key_files:
  - showcase/package.json
  - showcase/app/page.tsx
  - showcase/lib/load-intake.ts
  - showcase/components/shell-status.tsx
  - showcase/tests/load-intake.test.ts
  - showcase/tests/homepage-shell.test.tsx
  - .gsd/milestones/M004-fjc2zy/slices/S01/S01-PLAN.md
key_decisions:
  - Runtime intake load failures are surfaced via deterministic fallback payload (`shellState=intake_unavailable`, reason `INTAKE_MANIFEST_UNAVAILABLE`) instead of throwing.
patterns_established:
  - Server-component boundary pattern: async homepage reads intake once via `loadIntake()` and passes typed state to a pure presentational status component.
observability_surfaces:
  - Homepage shell state chip (`intake_available` / `intake_unavailable`) and fallback note in `showcase/components/shell-status.tsx`
  - `npm --prefix showcase run test -- --run -t intake-unavailable`
  - `curl http://127.0.0.1:3000` rendered HTML showing shell state label and intake path
  - `.gsd/DECISIONS.md` entry D051
duration: 1h 35m
verification_result: partial
completed_at: 2026-03-24
blocker_discovered: false
---

# T02: Scaffold the local Next.js showcase shell and intake loader boundary

**Shipped a runnable Next.js showcase shell that reads canonical intake manifest data at runtime and renders deterministic `intake_unavailable` fallback diagnostics when the manifest cannot be loaded.**

## What Happened

I first applied the pre-flight observability fix by extending `S01-PLAN.md` verification with an explicit failure-path frontend check: `npm --prefix showcase run test -- --run -t intake-unavailable`.

I then scaffolded `showcase/` as a minimal Next.js App Router app (`package.json`, `next.config.mjs`, `tsconfig.json`, `next-env.d.ts`, `app/layout.tsx`, `app/page.tsx`, `app/globals.css`) and wired the homepage to `await loadIntake()`.

I implemented `showcase/lib/load-intake.ts` as the typed intake boundary:
- reads `../outputs/showcase/intake/manifest.json`
- normalizes manifest shape for safe rendering
- returns deterministic fallback payload with `shellState: intake_unavailable`, reason `INTAKE_MANIFEST_UNAVAILABLE`, and stable timestamp when read/parse fails.

I added `showcase/components/shell-status.tsx` to render explicit shell state labels, readiness counters, intake path, and a fallback note when unavailable.

I added baseline frontend tests:
- `showcase/tests/load-intake.test.ts` (present + missing manifest behavior)
- `showcase/tests/homepage-shell.test.tsx` (homepage renders `intake_available` and fallback branch for `intake_unavailable`)

Finally, I verified runtime startup via `npm run dev` (bg shell) and confirmed rendered output includes `intake_available` state + intake path from canonical manifest.

## Verification

I ran both task-level checks (`npm test`, `npm build`) and the slice-level verification list. For this intermediate task, all currently implementable checks pass; the slice smoke command still fails because `scripts/showcase_smoke_check.py` is a T03 deliverable and does not exist yet.

I also verified observability impact directly by starting `next dev` and confirming the homepage output contains explicit shell state labels.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q` | 0 | ✅ pass | 1.05s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q -k missing` | 0 | ✅ pass | 0.93s |
| 3 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && test -f outputs/showcase/intake/manifest.json && test -f outputs/showcase/intake/validation_report.json` | 0 | ✅ pass | 0.43s |
| 4 | `cd showcase && npm run test -- --run` | 0 | ✅ pass | 2.22s |
| 5 | `cd showcase && npm run test -- --run -t intake-unavailable` | 0 | ✅ pass | 2.17s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000` | 2 | ❌ fail | 0.06s |
| 7 | `cd showcase && npm run build` | 0 | ✅ pass | 16.81s |
| 8 | `curl -sS http://127.0.0.1:3000 | rg -n 'intake_available|Shell startup state|Intake-locked showcase shell'` | 0 | ✅ pass | 2.20s |

## Diagnostics

- Build intake bundle:  
  `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake`
- Start shell locally:  
  `npm --prefix showcase run dev`
- Verify shell-state rendering in tests:  
  `npm --prefix showcase run test -- --run`  
  `npm --prefix showcase run test -- --run -t intake-unavailable`
- Inspect runtime shell state quickly:  
  `curl http://127.0.0.1:3000 | rg 'intake_available|intake_unavailable|Intake manifest path'`

## Deviations

- Added `showcase/app/globals.css`, `showcase/vitest.config.ts`, `showcase/tests/setup.ts`, and `showcase/package-lock.json` beyond the plan’s minimum file list to make the shell/test runtime actually runnable.

## Known Issues

- Slice smoke verification still fails because `scripts/showcase_smoke_check.py` is not implemented yet (planned in T03).
- Browser tool-based verification could not run in this environment because Playwright Chromium failed to launch (`libnspr4.so` missing); runtime UI state was verified via live dev server + HTML assertion instead.

## Files Created/Modified

- `showcase/package.json` — Added Next.js/Vitest scripts and dependencies for runnable local shell + tests.
- `showcase/package-lock.json` — Captured installed dependency lock state.
- `showcase/next.config.mjs` — Added minimal Next.js config for local standalone-friendly builds.
- `showcase/tsconfig.json` — Added TS compiler config with `@/*` alias and Next plugin.
- `showcase/next-env.d.ts` — Added Next TypeScript environment declarations.
- `showcase/app/layout.tsx` — Added app-wide root layout and metadata.
- `showcase/app/page.tsx` — Added async homepage entrypoint that loads intake from boundary loader.
- `showcase/app/globals.css` — Added baseline shell styling and status/metric presentation styles.
- `showcase/lib/load-intake.ts` — Added typed manifest loader with deterministic unavailable fallback behavior.
- `showcase/components/shell-status.tsx` — Added shell status component rendering observable availability/fallback state.
- `showcase/tests/load-intake.test.ts` — Added loader contract tests for present/missing manifest cases.
- `showcase/tests/homepage-shell.test.tsx` — Added homepage rendering tests for intake available/unavailable branches.
- `showcase/tests/setup.ts` — Added Vitest testing-library matcher setup.
- `showcase/vitest.config.ts` — Added jsdom/react Vitest config with alias mapping.
- `.gsd/milestones/M004-fjc2zy/slices/S01/S01-PLAN.md` — Added explicit failure-path verification command and marked T02 complete.
- `.gsd/DECISIONS.md` — Appended decision D051 for deterministic intake-unavailable fallback semantics.
