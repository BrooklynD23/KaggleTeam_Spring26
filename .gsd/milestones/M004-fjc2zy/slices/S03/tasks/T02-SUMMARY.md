---
id: T02
parent: S03
milestone: M004-fjc2zy
key_files:
  - showcase/lib/load-tracks.ts
  - showcase/components/track-flow.tsx
  - showcase/app/tracks/page.tsx
  - showcase/app/tracks/[trackKey]/page.tsx
  - showcase/app/page.tsx
  - showcase/app/executive/page.tsx
  - showcase/tests/load-tracks.test.ts
  - showcase/tests/track-flow.test.tsx
  - showcase/tests/homepage-shell.test.tsx
key_decisions:
  - Mirrored `load-story.ts` fallback semantics in a dedicated typed `load-tracks.ts` loader to keep deterministic blocked diagnostics when `tracks.json` is unavailable.
  - Reused `EvidenceList` for track evidence rendering so canonical evidence pointer fields (`surface_key`, `path`, `reason`, `requirement_key`) remain consistent across executive and track drill-down views.
  - Kept track detail routes strictly artifact-driven (`loadTracks` + route params) and explicitly avoided introducing live query/data-fetch paths.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T04:36:02.640Z
blocker_discovered: false
---

# T02: Implement typed tracks artifact loader and wire `/tracks` drill-down routes with canonical evidence diagnostics.

**Implement typed tracks artifact loader and wire `/tracks` drill-down routes with canonical evidence diagnostics.**

## What Happened

Implemented the full track drill-down runtime path from generated artifacts. Added `showcase/lib/load-tracks.ts` with typed contracts and deterministic fallback semantics (`tracks_available` / `tracks_unavailable`), including canonical `track_a`→`track_e` ordering, governance defaults, blocked evidence rows, and normalized machine-readable fields. Added route surfaces `showcase/app/tracks/page.tsx` and `showcase/app/tracks/[trackKey]/page.tsx`, both rendering exclusively from `loadTracks()` output (no live analytics queries). Added `showcase/components/track-flow.tsx` to render governance markers, status chips, per-track summaries, and evidence diagnostics via shared `EvidenceList` composition so `surface_key`, `path`, `reason`, and `requirement_key` stay visible exactly from generated payloads. Updated `showcase/app/page.tsx` and `showcase/app/executive/page.tsx` with drill-down navigation links while preserving existing executive flow rendering. Added `showcase/tests/load-tracks.test.ts` and `showcase/tests/track-flow.test.tsx` to enforce canonical ordering, fallback behavior, governance markers, and blocked evidence field visibility; updated homepage shell tests to assert new tracks navigation entry points.

## Verification

Ran slice-level verification commands plus task-level frontend verification. Contract tests passed; track artifact generation command passed and produced `tracks.json` + `tracks_validation_report.json`; showcase frontend tests passed (including new loader/track-flow tests); showcase production build passed and includes `/tracks` and `/tracks/[trackKey]` routes. Smoke check with `--tracks` still fails because that CLI flag is not yet implemented (planned for T03). UI observability signals (track status chips and evidence diagnostic rows) were verified through component/integration tests. Attempted runtime browser verification, but local Playwright browser launch failed in this environment due missing system library `libnspr4.so`, so browser assertions were not executable here.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_track_contract.py -q` | 0 | ✅ pass | 246ms |
| 2 | `python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && test -f outputs/showcase/story/tracks.json && test -f outputs/showcase/story/tracks_validation_report.json` | 0 | ✅ pass | 64ms |
| 3 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1810ms |
| 4 | `npm --prefix showcase run build` | 0 | ✅ pass | 17905ms |
| 5 | `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000` | 2 | ❌ fail | 54ms |


## Deviations

Direct browser-based UI verification could not be completed because Playwright Chromium failed to launch (`libnspr4.so` missing). Validation relied on passing Vitest route/component assertions and Next build output.

## Known Issues

`python scripts/showcase_smoke_check.py ... --tracks ...` still returns `unrecognized arguments: --tracks` (expected until T03). Browser automation tooling in this environment currently cannot launch Chromium due missing shared library `libnspr4.so`.

## Files Created/Modified

- `showcase/lib/load-tracks.ts`
- `showcase/components/track-flow.tsx`
- `showcase/app/tracks/page.tsx`
- `showcase/app/tracks/[trackKey]/page.tsx`
- `showcase/app/page.tsx`
- `showcase/app/executive/page.tsx`
- `showcase/tests/load-tracks.test.ts`
- `showcase/tests/track-flow.test.tsx`
- `showcase/tests/homepage-shell.test.tsx`
