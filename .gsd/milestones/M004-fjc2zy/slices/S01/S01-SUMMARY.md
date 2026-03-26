---
id: S01
parent: M004-fjc2zy
milestone: M004-fjc2zy
provides:
  - Canonical intake manifest + validation report surfaces for showcase readiness gating.
  - A runnable local Next.js shell with explicit intake-ready/intake-blocked/intake-unavailable state rendering.
  - A smoke-check/runbook verification path that proves homepage diagnostics are visible and contract-aligned.
requires:
  - slice: M001-4q3lxl/S02
    provides: Aggregate-safe export contract expectations and governance boundary markers consumed as required intake surfaces.
  - slice: M003-rdpeu4/S05
    provides: Closeout manifest/validation semantics consumed as required S01 readiness/blocked checks (R022 continuity).
  - slice: M003-rdpeu4/S07
    provides: Latest closeout readiness vocabulary continuity that S01 expects and diagnoses when artifacts are absent.
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - configs/showcase.yaml
  - src/showcase/intake_contract.py
  - scripts/build_showcase_intake.py
  - tests/test_showcase_intake_contract.py
  - showcase/app/page.tsx
  - showcase/components/readiness-panel.tsx
  - showcase/lib/load-intake.ts
  - showcase/tests/readiness-panel.test.tsx
  - showcase/tests/homepage-shell.test.tsx
  - scripts/showcase_smoke_check.py
  - docs/showcase_local_runbook.md
key_decisions:
  - Use config-driven intake declarations with deterministic required/optional missing reason codes as the canonical readiness truth source.
  - Render blocked diagnostics directly from manifest fields (including requirement and path context) rather than synthesized UI-only text.
  - Keep homepage available on intake read/parse failure by returning deterministic `intake_unavailable` fallback payloads.
  - Verify runtime diagnostics via a manifest-driven smoke checker that compares rendered homepage signals against intake artifact truth.
patterns_established:
  - Contract-first showcase intake pattern: YAML contract -> shared validator/generator -> persisted manifest/validation report -> UI loader -> runtime diagnostics.
  - Fail-visible shell pattern: always render readiness state, never hide missing upstream artifacts behind blank placeholders.
  - Deterministic diagnostics pattern: stable reason codes and field names support both UI rendering and automation assertions.
observability_surfaces:
  - `outputs/showcase/intake/manifest.json`
  - `outputs/showcase/intake/validation_report.json`
  - Homepage readiness panel (`status`, counts, blocked rows with `surface_key/path/reason/requirement_key`)
  - `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake`
  - `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000`
drill_down_paths:
  - .gsd/milestones/M004-fjc2zy/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S01/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-25T03:50:01.369Z
blocker_discovered: false
---

# S01: Intake-locked showcase shell with visible readiness and blocked states

**Delivered a runnable local Next.js showcase shell that is intake-locked to a canonical manifest and visibly reports ready/missing/blocked artifact diagnostics instead of silent placeholders.**

## What Happened

S01 shipped the foundational intake-to-UI contract for M004. T01 introduced a config-driven intake contract (`configs/showcase.yaml`) and generator (`scripts/build_showcase_intake.py`, `src/showcase/intake_contract.py`) that emits deterministic `manifest.json` and `validation_report.json` with required/optional surface semantics, stable reason codes, and governance markers. T02 scaffolded the local App Router shell under `showcase/`, added typed intake loading (`showcase/lib/load-intake.ts`), and established deterministic runtime fallback semantics (`intake_unavailable`, `INTAKE_MANIFEST_UNAVAILABLE`) so the homepage still renders an explicit blocked state when intake files are absent/unreadable. T03 added the readiness UI (`showcase/components/readiness-panel.tsx`) that renders summary counts and blocked rows with machine-parseable fields (`surface_key`, `path`, `reason`, `requirement_key`), updated component/integration tests, and shipped `scripts/showcase_smoke_check.py` plus `docs/showcase_local_runbook.md` to verify live local diagnostics against the manifest. The assembled slice now makes handoff drift explicit at the first user-facing surface and establishes the contract downstream slices consume.

## Verification

Executed all slice-plan verification gates successfully in this worktree: (1) `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q` (pass), (2) `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_showcase_intake_contract.py -q -k missing` (pass), (3) `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && test -f outputs/showcase/intake/manifest.json && test -f outputs/showcase/intake/validation_report.json` (pass), (4) `npm --prefix showcase run test -- --run` (pass), (5) started `npm --prefix showcase run dev` on port 3000 and ran `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000` (pass with per-surface blocked assertions), (6) `npm --prefix showcase run build` (pass). Observability surfaces confirmed: generated intake JSON artifacts include status/summary/blocked diagnostics, homepage displays readiness + blocked diagnostics, and smoke checker validates UI against manifest contract.

## Requirements Advanced

- R011 — Established the first working local-hosted Next.js showcase runtime and one-command verification path (tests, smoke check, production build).
- R013 — Made governance/internal-only intake markers and aggregate-safe diagnostics visible in generated intake artifacts and homepage status surfaces.
- R022 — Added explicit blocked diagnostics for required M003 closeout surfaces so compute-escalation continuity is visible when upstream artifacts are absent.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

Used the existing project virtualenv interpreter (`/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`) because the base interpreter lacked pytest; verification semantics remained the same.

## Known Limitations

Intake is currently blocked in this fresh worktree because required upstream M001/M003 artifact paths are missing, so the homepage correctly shows blocked diagnostics instead of a ready executive story. Executive narrative flow, track drill-down routes, and report/deck parity are not part of S01 and remain for S02-S05.

## Follow-ups

S02 should consume the same intake contract to gate executive-story sections by readiness; S03 should reuse blocked-row evidence pointer fields for track drill-down provenance; S05 should include smoke/parity/governance checks in one integrated demo gate.

## Files Created/Modified

- `configs/showcase.yaml` — Added canonical showcase intake surface contract (required/optional artifacts, requirement keys, governance markers).
- `src/showcase/intake_contract.py` — Implemented intake contract evaluation and deterministic blocked diagnostics model.
- `src/showcase/__init__.py` — Exported showcase intake contract interfaces/constants.
- `scripts/build_showcase_intake.py` — Added CLI to generate `manifest.json` and `validation_report.json` under output path.
- `tests/test_showcase_intake_contract.py` — Added intake contract regression coverage for ready/missing branches and output shape drift.
- `showcase/package.json` — Created Next.js shell package scripts/dependencies for dev, test, and build.
- `showcase/package-lock.json` — Captured lockfile for reproducible Node dependency installation.
- `showcase/next.config.mjs` — Added minimal Next.js config for local showcase shell.
- `showcase/tsconfig.json` — Added TypeScript configuration and path aliases for shell code/tests.
- `showcase/next-env.d.ts` — Added Next.js TypeScript environment declarations.
- `showcase/vitest.config.ts` — Configured Vitest/jsdom test runtime and path alias resolution.
- `showcase/tests/setup.ts` — Added shared test setup with matcher wiring and DOM cleanup isolation.
- `showcase/app/layout.tsx` — Added base layout and metadata for showcase app.
- `showcase/app/page.tsx` — Wired homepage to intake loader and readiness panel rendering.
- `showcase/app/globals.css` — Added shell/readiness panel styles for visible diagnostics presentation.
- `showcase/lib/load-intake.ts` — Implemented typed manifest loader with deterministic unavailable fallback.
- `showcase/components/shell-status.tsx` — Added initial shell-state component for intake availability diagnostics.
- `showcase/components/readiness-panel.tsx` — Implemented manifest-driven readiness summary and blocked diagnostics UI.
- `showcase/tests/load-intake.test.ts` — Added loader behavior tests for manifest present/missing cases.
- `showcase/tests/readiness-panel.test.tsx` — Added component tests for blocked and ready-empty diagnostics states.
- `showcase/tests/homepage-shell.test.tsx` — Added homepage tests validating blocked diagnostics and intake-unavailable fallback rendering.
- `scripts/showcase_smoke_check.py` — Added manifest-driven runtime smoke checker for homepage diagnostics visibility.
- `docs/showcase_local_runbook.md` — Documented local intake-build/startup/smoke-check verification workflow for stakeholders.
- `.gsd/milestones/M004-fjc2zy/slices/S01/S01-PLAN.md` — Updated task checklist/verification entries during task execution and completion.
- `.gsd/REQUIREMENTS.md` — Updated R011 with S01 partial-validation evidence and ownership/supporting-slice continuity notes.
- `.gsd/DECISIONS.md` — Appended S01 closeout decision capturing manifest-driven smoke verification contract (D052).
- `.gsd/KNOWLEDGE.md` — Added reusable lessons on Vitest DOM cleanup isolation and manifest-driven smoke-check triage.
- `.gsd/PROJECT.md` — Refreshed current-state summary to reflect completed M004 S01 showcase shell/intake diagnostics.
