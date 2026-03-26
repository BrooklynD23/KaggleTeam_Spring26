---
id: S03
parent: M004-fjc2zy
milestone: M004-fjc2zy
provides:
  - Canonical per-track evidence contract artifacts with deterministic order and governance payload.
  - Typed track loader + Next.js drill-down routes (`/tracks`, `/tracks/[trackKey]`) with explicit blocked-state diagnostics.
  - Runtime smoke parity coverage for track IA, governance markers, route links, and blocked M003 continuity rows.
requires:
  - slice: S02
    provides: Canonical executive story contract (`sections.json`) plus shared evidence-row rendering/governance patterns consumed by S03 track contracts and routes.
affects:
  - S04
  - S05
key_files:
  - configs/showcase.yaml
  - src/showcase/track_contract.py
  - scripts/build_showcase_tracks.py
  - showcase/lib/load-tracks.ts
  - showcase/components/track-flow.tsx
  - showcase/app/tracks/page.tsx
  - showcase/app/tracks/[trackKey]/page.tsx
  - scripts/showcase_smoke_check.py
  - docs/showcase_local_runbook.md
  - outputs/showcase/story/tracks.json
  - outputs/showcase/story/tracks_validation_report.json
key_decisions:
  - D058: Use a generated `tracks.json` contract as single source for drill-down runtime and parity checks.
  - D059: Enforce fixed Track A→E ordering and preserve blocked evidence rows with reason+requirement diagnostics.
  - D060: Smoke checker auto-starts local Next.js server when base URL is unreachable to avoid false-negative gate failures.
patterns_established:
  - Artifact-first route rendering: generator contract → typed loader → UI components → smoke parity checks.
  - Canonical evidence-row field reuse (`surface_key`, `path`, `reason`, `requirement_key`) across executive and track surfaces.
  - Fail-visible blocked continuity for upstream M003 dependencies rather than silent fallback content.
observability_surfaces:
  - outputs/showcase/story/tracks.json
  - outputs/showcase/story/tracks_validation_report.json
  - scripts/showcase_smoke_check.py PASS/FAIL labeled parity output (homepage, executive, tracks index/detail)
  - docs/showcase_local_runbook.md verification sequence including `--tracks` smoke check
drill_down_paths:
  - .gsd/milestones/M004-fjc2zy/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S03/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-25T04:48:22.024Z
blocker_discovered: false
---

# S03: Track drill-down experience with canonical evidence pointers

**Delivered canonical track-contract artifacts plus `/tracks` drill-down runtime and smoke parity so track pages now expose requirement-linked evidence diagnostics with deterministic blocked-state visibility.**

## What Happened

S03 completed the drill-down layer end-to-end. T01 introduced a generated track contract (`outputs/showcase/story/tracks.json` + `tracks_validation_report.json`) that enforces fixed `track_a`→`track_e` ordering and preserves blocked evidence rows with canonical diagnostics (`surface_key`, `path`, `reason`, `requirement_key`) instead of dropping missing pointers. T02 added a typed runtime loader and Next.js routes (`/tracks` and `/tracks/[trackKey]`) that render strictly from the generated artifact (or deterministic fallback), reusing shared evidence-row rendering and governance markers so executive and drill-down surfaces stay consistent. T03 extended smoke parity coverage to track index/detail routes and required blocked `m003_*` diagnostics, then aligned runbook verification order to regenerate intake/story/tracks before runtime checks. During closeout, the smoke checker was hardened to auto-start the local showcase server when `--base-url` is unreachable, eliminating connection-refused false negatives in non-interactive verification gates while keeping artifact-to-UI parity assertions unchanged.

## Verification

Ran all slice-plan verification classes and re-ran full slice command chain after fixes. Contract checks passed (`python -m pytest tests/test_showcase_track_contract.py -q`). Artifact builders passed and emitted required files (`build_showcase_intake.py`, `build_showcase_story.py`, `build_showcase_tracks.py` with `tracks.json` and `tracks_validation_report.json`). Frontend verification passed (`npm --prefix showcase run test -- --run`, `npm --prefix showcase run build`). Runtime parity passed with track inputs (`python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000`), including governance markers, route links, canonical order, evidence-row field parity, and blocked M003 continuity diagnostics.

## Requirements Advanced

- R011 — Extended local-hosted showcase capability from homepage/executive to track drill-down IA with artifact-driven routes and parity-smoke coverage including `--tracks`.
- R012 — Extended canonical trust narrative continuity into per-track drill-down evidence mapping so downstream report/deck parity can consume one story/evidence contract.
- R009 — Preserved and surfaced fairness/mitigation continuity pointers as explicit blocked/ready evidence rows on track pages, rather than re-implementing modeling logic.
- R010 — Preserved stronger-comparator continuity pointers in track evidence diagnostics, keeping adoption/materiality provenance visible to showcase consumers.
- R022 — Preserved M003 closeout/escalation continuity surfaces as requirement-linked evidence pointers and blocked diagnostics on drill-down routes.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

The showcase still reflects blocked upstream M003 intake/fairness/comparator/closeout surfaces in this worktree snapshot; S03 intentionally preserves and surfaces those blocked diagnostics rather than synthesizing fake ready states.

## Follow-ups

S04 should consume `outputs/showcase/story/{sections.json,tracks.json}` as the canonical narrative/evidence contract for report/deck generation parity. S05 should extend integrated demo hardening using the now-stable drill-down smoke assertions.

## Files Created/Modified

- `configs/showcase.yaml` — Added canonical track-order and evidence-pointer config used by track contract generation.
- `src/showcase/track_contract.py` — Implemented deterministic track contract builder, blocked diagnostic preservation, rollups, and validation payloads.
- `src/showcase/__init__.py` — Exported track contract symbols for CLI/tests consumption.
- `scripts/build_showcase_tracks.py` — Added CLI generator that writes `tracks.json` and `tracks_validation_report.json` from intake+story artifacts.
- `tests/test_showcase_track_contract.py` — Added contract tests for canonical ordering, blocked diagnostic shape, and validation semantics.
- `showcase/lib/load-tracks.ts` — Added typed tracks artifact loader with deterministic fallback semantics.
- `showcase/components/track-flow.tsx` — Implemented track index/detail rendering with governance markers and shared evidence list fields.
- `showcase/app/tracks/page.tsx` — Added `/tracks` index route consuming canonical track contract output.
- `showcase/app/tracks/[trackKey]/page.tsx` — Added per-track drill-down route rendering evidence rows and diagnostics from canonical artifact data.
- `showcase/app/page.tsx` — Added entry links into track drill-down IA from homepage shell.
- `showcase/app/executive/page.tsx` — Added navigation continuity from executive flow to tracks IA.
- `showcase/tests/load-tracks.test.ts` — Added loader regression coverage for canonical order and fallback behavior.
- `showcase/tests/track-flow.test.tsx` — Added/updated component tests for governance markers, evidence diagnostics, and drill-down links.
- `showcase/tests/homepage-shell.test.tsx` — Updated shell tests to assert track entry navigation.
- `scripts/showcase_smoke_check.py` — Extended smoke parity to track routes/diagnostics and hardened runtime with optional auto-start server behavior.
- `docs/showcase_local_runbook.md` — Updated runbook sequence to regenerate intake/story/tracks before runtime checks and run smoke with `--tracks`.
- `.gsd/REQUIREMENTS.md` — Updated R011 and R012 validation evidence to include S03 drill-down contract and smoke parity proof.
- `.gsd/PROJECT.md` — Refreshed current-state summary to include completed S03 drill-down and parity surfaces.
- `.gsd/KNOWLEDGE.md` — Added actionable notes for smoke auto-start and attribute-order-agnostic link assertions.
