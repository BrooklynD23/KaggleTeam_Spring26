---
estimated_steps: 5
estimated_files: 8
skills_used:
  - article-writing
  - frontend-slides
  - backend-patterns
  - verification-loop
---

# T01: Generate report and deck artifacts from canonical story/track contracts

**Slice:** S04 — Report and deck generated from shared narrative/evidence source
**Milestone:** M004-fjc2zy

## Description

Build deterministic report/deck generation on top of existing `sections.json` and `tracks.json` so website/report/deck all consume one story/evidence contract.

## Steps

1. Add `src/showcase/deliverables_contract.py` with shared loaders/render helpers that read `outputs/showcase/story/sections.json` and `outputs/showcase/story/tracks.json` and normalize executive+track rows for markdown rendering.
2. Add `scripts/build_showcase_report.py` and `scripts/build_showcase_deck.py` CLIs (patterned after existing `build_showcase_*` scripts) to generate deterministic markdown outputs under `outputs/showcase/deliverables/`.
3. Ensure both generated artifacts carry governance markers and canonical evidence fields (`surface_key`, `path`, `reason`, `requirement_key`) including blocked diagnostics for missing M003 surfaces.
4. Export deliverable contract helpers via `src/showcase/__init__.py` and add regression coverage in `tests/test_showcase_report_contract.py` and `tests/test_showcase_deck_contract.py` for canonical ordering + continuity fields.
5. Run tests and generators to confirm artifacts are reproducible from story/track inputs with no hand-authored narrative branch.

## Must-Haves

- [ ] Report and deck are generated from canonical story/track artifacts, not manually curated duplicate narratives.
- [ ] Executive section ordering remains canonical (`prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`).
- [ ] Governance markers and blocked/ready evidence pointer fields are present in both report and deck outputs.

## Verification

- `python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py -q`
- `python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables`
- `python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables`
- `test -f outputs/showcase/deliverables/showcase_report.md && test -f outputs/showcase/deliverables/showcase_deck.md`

## Observability Impact

- Signals added/changed: generated deliverables include source artifact references and section/track rollup counts for continuity inspection.
- How a future agent inspects this: open `outputs/showcase/deliverables/showcase_report.md` and `outputs/showcase/deliverables/showcase_deck.md` and compare against story/track artifacts.
- Failure state exposed: missing or drifted section/evidence rows surface as absent/mismatched required fields in generated markdown plus failing regression tests.

## Inputs

- `configs/showcase.yaml` — canonical governance and ordering config.
- `src/showcase/story_contract.py` — executive section contract semantics.
- `src/showcase/track_contract.py` — track drill-down/evidence contract semantics.
- `outputs/showcase/story/sections.json` — canonical executive source artifact.
- `outputs/showcase/story/tracks.json` — canonical track source artifact.

## Expected Output

- `src/showcase/deliverables_contract.py` — shared report/deck rendering contract helpers.
- `src/showcase/__init__.py` — export wiring for new deliverables helpers.
- `scripts/build_showcase_report.py` — report generator CLI.
- `scripts/build_showcase_deck.py` — deck-source generator CLI.
- `tests/test_showcase_report_contract.py` — report contract regression tests.
- `tests/test_showcase_deck_contract.py` — deck contract regression tests.
- `outputs/showcase/deliverables/showcase_report.md` — generated report artifact.
- `outputs/showcase/deliverables/showcase_deck.md` — generated deck-source artifact.
