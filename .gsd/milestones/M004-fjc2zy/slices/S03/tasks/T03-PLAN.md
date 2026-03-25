---
estimated_steps: 12
estimated_files: 3
skills_used:
  - verification-loop
  - coding-standards
  - accessibility
---

# T03: Extend smoke parity and runbook coverage for track drill-downs

## Description
Close the slice with local runtime verification that compares rendered track routes against generated track artifacts and makes drift immediately diagnosable.

## Steps
1. Extend `scripts/showcase_smoke_check.py` CLI and checks with `--tracks` support plus route assertions for `/tracks` and representative per-track pages.
2. Add parity checks that validate governance markers and evidence diagnostic fields (`surface_key`, `path`, `reason`, `requirement_key`) against `tracks.json`.
3. Tighten `showcase/tests/track-flow.test.tsx` integration assertions so smoke and unit-level checks align on the same field contract.
4. Update `docs/showcase_local_runbook.md` command order to generate intake/story/tracks artifacts before starting the local app and executing smoke checks.
5. Ensure smoke output prints clear PASS/FAIL labels for each track parity assertion to localize artifact-vs-UI drift quickly.

## Must-Haves
- [ ] Smoke checker fails when track-route evidence fields differ from generated artifact rows.
- [ ] Runbook contains the full S03 local verification sequence including `build_showcase_tracks.py` and `--tracks` smoke input.
- [ ] Runtime parity checks explicitly cover blocked diagnostic visibility for missing M003 surfaces.

## Inputs

- `scripts/showcase_smoke_check.py`
- `docs/showcase_local_runbook.md`
- `outputs/showcase/story/tracks.json`
- `showcase/app/tracks/page.tsx`
- `showcase/app/tracks/[trackKey]/page.tsx`

## Expected Output

- `scripts/showcase_smoke_check.py`
- `docs/showcase_local_runbook.md`
- `showcase/tests/track-flow.test.tsx`
- `.gsd/milestones/M004-fjc2zy/slices/S03/S03-PLAN.md`

## Verification

python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && npm --prefix showcase run test -- --run && python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000

## Observability Impact

Signals added/changed: smoke parity labels for track index/detail checks.
How a future agent inspects this: run `python scripts/showcase_smoke_check.py ... --tracks outputs/showcase/story/tracks.json` and inspect PASS/FAIL output lines.
Failure state exposed: mismatch between artifact data and rendered drill-down rows is surfaced with check-specific failure labels.
