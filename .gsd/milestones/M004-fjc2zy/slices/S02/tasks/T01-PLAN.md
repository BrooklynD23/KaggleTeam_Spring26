---
estimated_steps: 6
estimated_files: 7
skills_used:
  - coding-standards
  - backend-patterns
  - verification-loop
---

# T01: Define executive story contract and generate canonical section/evidence artifacts

Create the canonical S02 story contract that converts intake diagnostics into executive narrative sections with explicit evidence pointers and blocked semantics. Retire narrative-drift risk first by establishing one machine-readable artifact surface consumed by UI, smoke checks, and later report/deck slices.

1. Extend `configs/showcase.yaml` with executive section mapping and fixed ordering (`prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`).
2. Implement `src/showcase/story_contract.py` to merge config + intake manifest into section/evidence readiness payloads.
3. Add `scripts/build_showcase_story.py` and export symbols via `src/showcase/__init__.py`.
4. Emit deterministic governance markers + blocked reason diagnostics in `sections.json` and `validation_report.json`.
5. Add regression coverage in `tests/test_showcase_story_contract.py` for ready/blocked branches and CLI output shape.

## Inputs

- `configs/showcase.yaml`
- `src/showcase/intake_contract.py`
- `outputs/showcase/intake/manifest.json`
- `.gsd/REQUIREMENTS.md`

## Expected Output

- `configs/showcase.yaml`
- `src/showcase/story_contract.py`
- `src/showcase/__init__.py`
- `scripts/build_showcase_story.py`
- `tests/test_showcase_story_contract.py`
- `outputs/showcase/story/sections.json`
- `outputs/showcase/story/validation_report.json`

## Verification

python -m pytest tests/test_showcase_story_contract.py -q && python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && test -f outputs/showcase/story/sections.json && test -f outputs/showcase/story/validation_report.json

## Observability Impact

Introduces story-level readiness + validation diagnostics that localize section/evidence failures before UI rendering.
