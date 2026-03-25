---
id: T01
parent: S03
milestone: M004-fjc2zy
key_files:
  - configs/showcase.yaml
  - src/showcase/track_contract.py
  - src/showcase/__init__.py
  - scripts/build_showcase_tracks.py
  - tests/test_showcase_track_contract.py
  - outputs/showcase/story/tracks.json
  - outputs/showcase/story/tracks_validation_report.json
key_decisions:
  - D059: enforce fixed track_a→track_e ordering and preserve blocked evidence rows with reason + requirement diagnostics instead of dropping missing pointers.
  - Reused intake/story reason-code semantics in track validation output so downstream UI/smoke checks can treat status fields consistently across artifact layers.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T04:30:46.919Z
blocker_discovered: false
---

# T01: Add canonical showcase track contract generation with deterministic order and blocked evidence diagnostics

**Add canonical showcase track contract generation with deterministic order and blocked evidence diagnostics**

## What Happened

Implemented T01 end-to-end by adding a canonical track contract layer that merges showcase config, intake manifest, and story sections into deterministic track drill-down artifacts. Updated configs/showcase.yaml with showcase.tracks.order + entries for track_a through track_e, including required evidence pointers and story-section bindings. Added src/showcase/track_contract.py with strict parsing/validation (canonical order enforcement), governance payload merge, per-track evidence synthesis, blocked-row preservation, section reference linkage, rollups, and validation reason-code reporting. Exported new track contract symbols from src/showcase/__init__.py. Added scripts/build_showcase_tracks.py to emit outputs/showcase/story/tracks.json and outputs/showcase/story/tracks_validation_report.json in deterministic JSON form. Added tests/test_showcase_track_contract.py covering canonical ordering, blocked-diagnostic shape (surface_key/path/reason/requirement_key), missing-surface reason handling via SURFACE_NOT_IN_INTAKE_MANIFEST, and CLI output shape. Verified observability impact directly in generated artifacts: track_status_rollup and required_blocked_evidence counters are present, and blocked diagnostics carry explicit reason codes and requirement keys for R009/R010/R022 continuity surfaces.

## Verification

Task-level verification passed exactly as planned: python -m pytest tests/test_showcase_track_contract.py -q and track artifact build command succeeded, and both tracks.json + tracks_validation_report.json were generated. Slice-level checks were also executed for visibility: showcase frontend test/build commands passed; smoke check with --tracks failed because scripts/showcase_smoke_check.py does not yet support the --tracks flag (work planned for T03). This is expected at T01 and was recorded rather than treated as a blocker.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_track_contract.py -q` | 0 | ✅ pass | 240ms |
| 2 | `python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && test -f outputs/showcase/story/tracks.json && test -f outputs/showcase/story/tracks_validation_report.json` | 0 | ✅ pass | 66ms |
| 3 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 2109ms |
| 4 | `npm --prefix showcase run build` | 0 | ✅ pass | 15958ms |
| 5 | `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000` | 2 | ❌ fail | 59ms |


## Deviations

None.

## Known Issues

Slice-level smoke command currently fails with exit code 2: scripts/showcase_smoke_check.py does not yet accept --tracks. This is expected for T01 and is scheduled in T03.

## Files Created/Modified

- `configs/showcase.yaml`
- `src/showcase/track_contract.py`
- `src/showcase/__init__.py`
- `scripts/build_showcase_tracks.py`
- `tests/test_showcase_track_contract.py`
- `outputs/showcase/story/tracks.json`
- `outputs/showcase/story/tracks_validation_report.json`
