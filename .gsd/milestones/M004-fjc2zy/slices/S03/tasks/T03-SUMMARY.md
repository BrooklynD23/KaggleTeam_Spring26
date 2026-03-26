---
id: T03
parent: S03
milestone: M004-fjc2zy
key_files:
  - scripts/showcase_smoke_check.py
  - showcase/tests/track-flow.test.tsx
  - docs/showcase_local_runbook.md
key_decisions:
  - Added artifact-driven track parity checks in smoke rather than UI-only heuristics so route drift is diagnosed against canonical contract fields.
  - Enforced explicit blocked `m003_*` required-evidence assertions in smoke output to guarantee missing closeout/continuity surfaces remain visible and testable in runtime routes.
duration: ""
verification_result: passed
completed_at: 2026-03-25T04:43:18.049Z
blocker_discovered: false
---

# T03: Extended showcase smoke parity to cover track index/detail routes, synchronized track-flow contract assertions, and updated the S03 runbook verification sequence.

**Extended showcase smoke parity to cover track index/detail routes, synchronized track-flow contract assertions, and updated the S03 runbook verification sequence.**

## What Happened

Executed T03 by extending `scripts/showcase_smoke_check.py` with optional `--tracks` artifact input and route-level parity checks for `/tracks` and `/tracks/{trackKey}` pages. The smoke checker now validates track governance markers, track summary rollups, route link integrity, canonical order, and per-evidence diagnostics (`surface_key`, `path`, `reason`, `requirement_key`) against generated `tracks.json`, with explicit checks for blocked `m003_*` required-surface visibility to catch continuity drift. While validating smoke output, initial link checks failed due an href/testid attribute-order assumption; verified rendered HTML, updated matcher logic to be attribute-order agnostic, and re-ran the gate to full PASS. Tightened `showcase/tests/track-flow.test.tsx` so unit-level assertions mirror smoke parity expectations (scope governance marker, evidence status chips/fields, route links in index and detail modes). Updated `docs/showcase_local_runbook.md` from S02 to S03 and reordered/expanded commands to include intake → story → tracks generation before app runtime checks, then smoke execution with `--tracks` input.

## Verification

Ran contract and runtime verification end-to-end: pytest contract tests, intake/story/tracks builders, showcase vitest suite, Next production build, and smoke parity against a live dev server at `http://127.0.0.1:3000` using `--tracks`. Smoke now emits explicit PASS/FAIL labels across homepage, executive, tracks index, per-track detail evidence parity, and blocked M003 continuity diagnostics.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_track_contract.py -q` | 0 | ✅ pass | 247ms |
| 2 | `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake` | 0 | ✅ pass | 60ms |
| 3 | `python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story` | 0 | ✅ pass | 70ms |
| 4 | `python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && test -f outputs/showcase/story/tracks.json && test -f outputs/showcase/story/tracks_validation_report.json` | 0 | ✅ pass | 59ms |
| 5 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1802ms |
| 6 | `npm --prefix showcase run build` | 0 | ✅ pass | 18017ms |
| 7 | `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000` | 0 | ✅ pass | 221ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scripts/showcase_smoke_check.py`
- `showcase/tests/track-flow.test.tsx`
- `docs/showcase_local_runbook.md`
