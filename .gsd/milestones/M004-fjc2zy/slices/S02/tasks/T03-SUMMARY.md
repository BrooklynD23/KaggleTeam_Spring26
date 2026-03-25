---
id: T03
parent: S02
milestone: M004-fjc2zy
key_files:
  - scripts/showcase_smoke_check.py
  - showcase/tests/load-story.test.ts
  - docs/showcase_local_runbook.md
key_decisions:
  - Smoke parity assertions are keyed by `data-testid` and field-level labels to stay resilient to SSR markup wrappers while preserving strict artifact-to-UI parity checks.
  - `load-story` behavior is locked by dedicated tests for both normalization and deterministic fallback (missing file and invalid JSON), ensuring executive flow remains explicit and stable under artifact failure modes.
duration: ""
verification_result: passed
completed_at: 2026-03-25T04:16:27.694Z
blocker_discovered: false
---

# T03: Extended showcase smoke parity checks, load-story normalization tests, and S02 runbook sequencing for executive artifact verification.

**Extended showcase smoke parity checks, load-story normalization tests, and S02 runbook sequencing for executive artifact verification.**

## What Happened

Implemented T03 across smoke diagnostics, loader testing, and runbook execution flow. In `scripts/showcase_smoke_check.py`, I extended the checker to require both intake manifest and story artifact inputs, fetch both `/` and `/executive`, and validate executive-first parity signals: canonical section rendering presence/order, section status chips, governance markers, summary counters, and evidence pointer fields (`surface_key`, `path`, `reason`, `requirement_key`) for each evidence row. The output now emits actionable PASS/FAIL labels tied to specific section/evidence keys for triage. During verification, governance checks initially failed because Next.js SSR inserted comment nodes between labels and values; I adjusted matching to use `data-testid`-scoped regex extraction so checks are resilient while still field-specific. Added `showcase/tests/load-story.test.ts` to cover normal load + normalization behavior, missing-file deterministic fallback, and invalid-JSON fallback (`STORY_READ_FAILURE`) so fallback/normalization behavior is explicitly regression-tested. Updated `docs/showcase_local_runbook.md` to S02 command order: build intake, build story, run showcase tests/build, start dev server, run smoke parity check with `--story` input.

## Verification

Ran full task and slice checks. `pytest` contract tests passed for story contract behavior. Story artifact build command succeeded and produced both expected outputs (`sections.json`, `validation_report.json`). Showcase Vitest suite passed including the new `load-story` coverage. Next.js production build passed. Live smoke parity check against `http://127.0.0.1:3000` passed and emitted labeled PASS rows for homepage diagnostics and executive section/evidence parity checks.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_story_contract.py -q` | 0 | ✅ pass | 244ms |
| 2 | `python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && test -f outputs/showcase/story/sections.json && test -f outputs/showcase/story/validation_report.json` | 0 | ✅ pass | 62ms |
| 3 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1723ms |
| 4 | `npm --prefix showcase run build` | 0 | ✅ pass | 16151ms |
| 5 | `npm --prefix showcase run test -- --run && python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000` | 0 | ✅ pass | 1922ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scripts/showcase_smoke_check.py`
- `showcase/tests/load-story.test.ts`
- `docs/showcase_local_runbook.md`
