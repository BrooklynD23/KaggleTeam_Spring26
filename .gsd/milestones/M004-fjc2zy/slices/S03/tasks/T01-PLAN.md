---
estimated_steps: 12
estimated_files: 5
skills_used:
  - react-best-practices
  - backend-patterns
  - verification-loop
---

# T01: Generate canonical track drill-down contract artifacts

## Description
Define one canonical track-drill-down artifact contract so all runtime pages and parity checks consume the same machine-readable track evidence pointers.

## Steps
1. Extend `configs/showcase.yaml` with a `showcase.tracks` mapping that locks canonical track order and required evidence surface keys for Track A–E.
2. Implement `src/showcase/track_contract.py` to merge showcase config + intake manifest + story sections into deterministic track entries with governance payload and per-evidence status rows.
3. Export track contract symbols in `src/showcase/__init__.py` and add `scripts/build_showcase_tracks.py` to emit `tracks.json` and `tracks_validation_report.json`.
4. Add `tests/test_showcase_track_contract.py` assertions for canonical order, blocked-diagnostic field shape (`surface_key`, `path`, `reason`, `requirement_key`), and missing-surface reason handling.
5. Keep blocked visibility strict for R009/R010/R022 surfaces so missing fairness/comparator/closeout evidence appears in generated artifacts instead of being dropped.

## Must-Haves
- [ ] Generated artifacts include deterministic Track A→E ordering and reusable track-level evidence rows.
- [ ] Blocked evidence rows preserve `surface_key`, `path`, `reason`, and `requirement_key` fields for downstream UI/smoke parity.
- [ ] Contract tests fail when required tracks or required evidence pointers are absent from generated outputs.

## Inputs

- `configs/showcase.yaml`
- `src/showcase/intake_contract.py`
- `src/showcase/story_contract.py`
- `outputs/showcase/intake/manifest.json`
- `outputs/showcase/story/sections.json`

## Expected Output

- `configs/showcase.yaml`
- `src/showcase/track_contract.py`
- `src/showcase/__init__.py`
- `scripts/build_showcase_tracks.py`
- `tests/test_showcase_track_contract.py`
- `outputs/showcase/story/tracks.json`
- `outputs/showcase/story/tracks_validation_report.json`

## Verification

python -m pytest tests/test_showcase_track_contract.py -q && python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story && test -f outputs/showcase/story/tracks.json && test -f outputs/showcase/story/tracks_validation_report.json

## Observability Impact

Signals added/changed: track-level readiness rollups and blocked reason-code diagnostics in generated validation output.
How a future agent inspects this: inspect `outputs/showcase/story/tracks.json` and `outputs/showcase/story/tracks_validation_report.json` after running the generator.
Failure state exposed: missing required track evidence is visible as blocked rows with explicit reason codes and requirement keys.
