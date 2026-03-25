---
estimated_steps: 5
estimated_files: 5
skills_used:
  - frontend-patterns
  - test
  - verification-loop
---

# T03: Render visible readiness and blocked states with smoke verification

**Slice:** S01 — Intake-locked showcase shell with visible readiness and blocked states
**Milestone:** M004-fjc2zy

## Description

Complete the S01 user-facing promise by rendering explicit ready/missing diagnostics on the homepage and adding an executable smoke path that confirms stakeholders can detect blocked intake state quickly during local demos.

## Steps

1. Implement `showcase/components/readiness-panel.tsx` to render ready counts, missing counts, and blocked required surfaces with artifact paths and reason codes.
2. Integrate `readiness-panel` into `showcase/app/page.tsx` so homepage status reflects live intake manifest content.
3. Add frontend tests in `showcase/tests/readiness-panel.test.tsx` and `showcase/tests/homepage-shell.test.tsx` that assert blocked-state visibility and fallback-state visibility.
4. Add `scripts/showcase_smoke_check.py` to validate that the running homepage exposes readiness diagnostics for local verification.
5. Document run + smoke steps in `docs/showcase_local_runbook.md` so S02+ slices inherit one stable startup/verification path.

## Must-Haves

- [ ] Homepage displays an explicit blocked section when required artifacts are missing.
- [ ] Blocked rows include machine-parseable context (surface key/path/reason) sourced from intake manifest data.
- [ ] Frontend tests assert readiness-panel behavior for both blocked and ready surfaces.
- [ ] Smoke script verifies local page content for readiness diagnostics and returns non-zero when expected status text is absent.

## Verification

- `npm --prefix showcase run test -- --run`
- `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000`

## Observability Impact

- Signals added/changed: homepage readiness panel exposes blocked required-surface diagnostics from manifest data.
- How a future agent inspects this: view homepage panel in local app and run `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000`.
- Failure state exposed: missing intake surfaces and missing UI diagnostics both produce explicit smoke-check failures.

## Inputs

- `showcase/app/page.tsx` — homepage shell that will host readiness diagnostics
- `showcase/lib/load-intake.ts` — intake manifest loader used by readiness panel
- `outputs/showcase/intake/manifest.json` — readiness/blocked source data for UI rendering
- `outputs/showcase/intake/validation_report.json` — blocked reason details used by panel rows

## Expected Output

- `showcase/components/readiness-panel.tsx` — visible readiness/blocked diagnostics component
- `showcase/tests/readiness-panel.test.tsx` — component-level blocked/ready behavior assertions
- `showcase/tests/homepage-shell.test.tsx` — homepage integration assertions for blocked/fallback states
- `scripts/showcase_smoke_check.py` — executable local smoke verification for readiness diagnostics
- `docs/showcase_local_runbook.md` — local run and smoke-check instructions for S01 demo path
