---
id: T03
parent: S01
milestone: M004-fjc2zy
key_files:
  - showcase/components/readiness-panel.tsx
  - showcase/app/page.tsx
  - showcase/tests/readiness-panel.test.tsx
  - showcase/tests/homepage-shell.test.tsx
  - showcase/tests/setup.ts
  - scripts/showcase_smoke_check.py
  - docs/showcase_local_runbook.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Expose blocked diagnostics in a structured row layout with explicit machine-parseable fields (`surface_key`, `path`, `reason`, `requirement_key`) directly from manifest data.
  - Implement a manifest-driven smoke checker that validates rendered diagnostics against the same manifest used by runtime, so demo regressions fail fast with explicit missing-text reasons.
  - Centralize Testing Library DOM cleanup in `showcase/tests/setup.ts` to prevent cross-test leakage in Vitest integration/component suites.
duration: ""
verification_result: passed
completed_at: 2026-03-25T03:46:01.181Z
blocker_discovered: false
---

# T03: Render manifest-driven readiness diagnostics in the showcase homepage with automated smoke verification and runbook docs.

**Render manifest-driven readiness diagnostics in the showcase homepage with automated smoke verification and runbook docs.**

## What Happened

Implemented a new `ReadinessPanel` server-rendered component that exposes intake readiness metrics and explicit blocked required-surface diagnostics sourced directly from manifest payload fields. The homepage integration was switched from the prior shell status card to this readiness-focused panel. Blocked rows now render machine-parseable context columns (`surface_key`, `path`, `reason`, `requirement_key`) and preserve deterministic fallback visibility (`intake-fallback-note`) when intake loading fails. Added component-level tests for blocked and ready-empty states and refreshed homepage integration tests for both blocked diagnostics and fallback diagnostics. Added `scripts/showcase_smoke_check.py` to fetch the running homepage and validate required readiness/blocked diagnostics against the manifest, failing with non-zero exit when expected status text or blocked context is absent. Added `docs/showcase_local_runbook.md` documenting intake build, local startup, smoke verification, and quick verification loop. During verification, test isolation failures were diagnosed as DOM cleanup accumulation; fixed by adding `afterEach(cleanup)` in `showcase/tests/setup.ts` and reran tests successfully.

## Verification

Executed full slice verification gates relevant to S01 runtime + shell behavior. Intake contract pytest checks passed (full + missing subset) using `uv run --with pytest` due missing `pytest` in the base interpreter. Intake artifact build command passed and confirmed manifest/validation files exist. Frontend Vitest suite passed after adding global cleanup. Smoke check passed against a live Next.js dev server on `http://127.0.0.1:3000`, verifying readiness heading, status text, summary counts, blocked section heading, and per-blocked-surface path/reason visibility. Production build succeeded (`next build`). Observability signals were verified in both generated intake JSON artifacts and rendered homepage output.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run --with pytest python -m pytest tests/test_showcase_intake_contract.py -q` | 0 | ✅ pass | 1884ms |
| 2 | `uv run --with pytest python -m pytest tests/test_showcase_intake_contract.py -q -k missing` | 0 | ✅ pass | 274ms |
| 3 | `uv run --with pyyaml python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && test -f outputs/showcase/intake/manifest.json && test -f outputs/showcase/intake/validation_report.json` | 0 | ✅ pass | 268ms |
| 4 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1555ms |
| 5 | `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000` | 0 | ✅ pass | 2309ms |
| 6 | `npm --prefix showcase run build` | 0 | ✅ pass | 16642ms |


## Deviations

Used `uv run --with pytest ...` and `uv run --with pyyaml ...` wrappers for Python verification commands because the base `python` runtime in this worktree lacked `pytest`/`pip`. This is an environment adaptation only; command semantics and assertions remained unchanged.

## Known Issues

None.

## Files Created/Modified

- `showcase/components/readiness-panel.tsx`
- `showcase/app/page.tsx`
- `showcase/tests/readiness-panel.test.tsx`
- `showcase/tests/homepage-shell.test.tsx`
- `showcase/tests/setup.ts`
- `scripts/showcase_smoke_check.py`
- `docs/showcase_local_runbook.md`
- `.gsd/KNOWLEDGE.md`
