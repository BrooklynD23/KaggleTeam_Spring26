# S03: Track drill-down experience with canonical evidence pointers

**Goal:** Add contract-driven track drill-down routes so stakeholders can inspect per-track evidence diagnostics from generated artifacts while preserving canonical claim-to-evidence pointers, governance markers, and explicit blocked-state visibility.
**Demo:** stakeholders can open per-track drill-down pages and inspect canonical metrics/figures plus explicit evidence pointers back to exported artifacts and M003 closeout surfaces.

## Must-Haves

- Canonical track artifact generation exists (`outputs/showcase/story/tracks.json`) with fixed track ordering (`track_a`→`track_e`), per-track evidence rows, governance payload, and blocked diagnostics carrying `surface_key`, `path`, `reason`, and `requirement_key`.
- Next.js exposes `/tracks` and per-track drill-down routes that render only from generated track artifacts (or deterministic fallback) and reuse canonical evidence-row field rendering.
- Track pages keep governance markers visible and preserve blocked semantics for M003 closeout/fairness/comparator surfaces (R022/R009/R010 continuity).
- Local smoke checks assert artifact-to-UI parity for drill-down routes, including explicit blocked diagnostics when upstream artifacts are missing.
- Observability surfaces are inspectable via generated track diagnostics artifacts and smoke-check labeled parity output for route drift triage.
- Verification passes: contract tests, artifact build commands, showcase frontend tests/build, and smoke checks with `--tracks` input.

## Proof Level

- This slice proves: integration

## Integration Closure

Consumes S02 intake/story contracts and evidence-list rendering; adds track contract generator, typed runtime loader, and `/tracks` route wiring. Leaves S04/S05 to consume these canonical track surfaces for report/deck parity and integrated milestone hardening.

## Verification

- `python -m pytest tests/test_showcase_track_contract.py -q`
- `python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && test -f outputs/showcase/story/tracks.json && test -f outputs/showcase/story/tracks_validation_report.json`
- `npm --prefix showcase run test -- --run`
- `npm --prefix showcase run build`
- `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000`

## Tasks

- [x] **T01: Generate canonical track drill-down contract artifacts** `est:1h 45m`
  Why: retire narrative/evidence drift by defining one generated track-level contract before UI changes.
Files: `configs/showcase.yaml`, `src/showcase/track_contract.py`, `src/showcase/__init__.py`, `scripts/build_showcase_tracks.py`, `tests/test_showcase_track_contract.py`
Do: extend showcase config with track definitions and required evidence keys; build a track contract module that reads intake + executive story artifacts and emits deterministic track rows with canonical ordering, governance metadata, and blocked diagnostics (`surface_key`, `path`, `reason`, `requirement_key`); add CLI generation and regression tests for ready/blocked paths.
Verify: `python -m pytest tests/test_showcase_track_contract.py -q && python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && test -f outputs/showcase/story/tracks.json && test -f outputs/showcase/story/tracks_validation_report.json`
Done when: track artifacts are generated deterministically with canonical order and explicit blocked rows that preserve R009/R010/R022 diagnostics semantics.
  - Files: `configs/showcase.yaml`, `src/showcase/track_contract.py`, `src/showcase/__init__.py`, `scripts/build_showcase_tracks.py`, `tests/test_showcase_track_contract.py`
  - Verify: python -m pytest tests/test_showcase_track_contract.py -q && python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && test -f outputs/showcase/story/tracks.json && test -f outputs/showcase/story/tracks_validation_report.json

- [x] **T02: Implement typed track loader and `/tracks` drill-down routes** `est:2h 15m`
  Why: make drill-down IA real in local runtime by rendering per-track pages from canonical artifacts instead of hardcoded content.
Files: `showcase/lib/load-tracks.ts`, `showcase/app/page.tsx`, `showcase/app/executive/page.tsx`, `showcase/app/tracks/page.tsx`, `showcase/app/tracks/[trackKey]/page.tsx`, `showcase/components/track-flow.tsx`, `showcase/tests/load-tracks.test.ts`, `showcase/tests/track-flow.test.tsx`
Do: add a typed track artifact loader with deterministic fallback semantics; wire homepage/executive entry links to tracks IA; add tracks index and per-track route that render canonical metrics/evidence using `EvidenceList` and governance markers; preserve reduced-motion-safe behavior and explicit blocked diagnostics for missing M003 fairness/comparator/closeout surfaces.
Verify: `npm --prefix showcase run test -- --run && npm --prefix showcase run build`
Done when: `/tracks` and `/tracks/<track-key>` routes render from `tracks.json` (or fallback), keep evidence pointer fields visible, and tests cover canonical ordering plus fallback/error behavior.
  - Files: `showcase/lib/load-tracks.ts`, `showcase/app/page.tsx`, `showcase/app/executive/page.tsx`, `showcase/app/tracks/page.tsx`, `showcase/app/tracks/[trackKey]/page.tsx`, `showcase/components/track-flow.tsx`, `showcase/tests/load-tracks.test.ts`, `showcase/tests/track-flow.test.tsx`
  - Verify: npm --prefix showcase run test -- --run && npm --prefix showcase run build

- [x] **T03: Extend smoke parity and runbook coverage for track drill-downs** `est:1h 15m`
  Why: close the slice with executable parity checks that catch drift between generated track artifacts and rendered drill-down routes.
Files: `scripts/showcase_smoke_check.py`, `docs/showcase_local_runbook.md`, `showcase/tests/track-flow.test.tsx`
Do: extend smoke checker CLI/schema to accept `--tracks` and validate `/tracks` + per-track page assertions against artifact fields; include checks for governance markers and required blocked diagnostics (`surface_key`, `path`, `reason`, `requirement_key`); update local runbook command order to generate tracks artifact before runtime checks.
Verify: `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && npm --prefix showcase run test -- --run && python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000`
Done when: smoke output includes explicit PASS/FAIL parity checks for track routes and fails deterministically when track artifact fields or blocked diagnostics drift from rendered UI.
  - Files: `scripts/showcase_smoke_check.py`, `docs/showcase_local_runbook.md`, `showcase/tests/track-flow.test.tsx`
  - Verify: python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && npm --prefix showcase run test -- --run && python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000

## Files Likely Touched

- configs/showcase.yaml
- src/showcase/track_contract.py
- src/showcase/__init__.py
- scripts/build_showcase_tracks.py
- tests/test_showcase_track_contract.py
- showcase/lib/load-tracks.ts
- showcase/app/page.tsx
- showcase/app/executive/page.tsx
- showcase/app/tracks/page.tsx
- showcase/app/tracks/[trackKey]/page.tsx
- showcase/components/track-flow.tsx
- showcase/tests/load-tracks.test.ts
- showcase/tests/track-flow.test.tsx
- scripts/showcase_smoke_check.py
- docs/showcase_local_runbook.md
