---
estimated_steps: 5
estimated_files: 4
skills_used:
  - backend-patterns
  - verification-loop
  - article-writing
---

# T02: Add site-report-deck parity diagnostics and local runbook wiring

**Slice:** S04 — Report and deck generated from shared narrative/evidence source
**Milestone:** M004-fjc2zy

## Description

Add a deterministic parity gate that proves website-source artifacts and generated report/deck artifacts are aligned on ordering, evidence pointers, governance markers, and requirement continuity.

## Steps

1. Create `scripts/check_showcase_parity.py` to compare `sections.json`/`tracks.json` against generated report/deck markdown for section order, evidence IDs, pointer fields, requirement keys, and governance markers.
2. Emit machine-readable diagnostics to `outputs/showcase/deliverables/parity_report.json` with per-check pass/fail and mismatch details, and exit non-zero on drift.
3. Add `tests/test_showcase_parity_contract.py` with pass/fail fixtures proving drift detection for order, evidence-pointer fields, requirement-key continuity, and governance marker presence.
4. Update `docs/showcase_local_runbook.md` with deterministic commands to generate report/deck and execute parity checks (optional Marp export noted as packaging-only).
5. Run parity verification sequence end-to-end and confirm parity JSON is produced for S05 gate reuse.

## Must-Haves

- [ ] Parity checker fails when report/deck drift from story/track contract artifacts.
- [ ] `parity_report.json` records check-level outcomes and failure details for triage.
- [ ] Runbook documents local regeneration and parity verification flow for report/deck artifacts.

## Verification

- `python -m pytest tests/test_showcase_parity_contract.py -q`
- `python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json`
- `test -f outputs/showcase/deliverables/parity_report.json`

## Observability Impact

- Signals added/changed: parity output includes classed check results (`section_order`, `evidence_fields`, `requirement_keys`, `governance_markers`) with mismatch payloads.
- How a future agent inspects this: inspect `outputs/showcase/deliverables/parity_report.json` after running parity script.
- Failure state exposed: non-zero exit plus explicit failing check IDs/details localize continuity drift without manual diffing.

## Inputs

- `outputs/showcase/story/sections.json` — canonical executive story source.
- `outputs/showcase/story/tracks.json` — canonical track story source.
- `outputs/showcase/deliverables/showcase_report.md` — generated report artifact under validation.
- `outputs/showcase/deliverables/showcase_deck.md` — generated deck artifact under validation.
- `docs/showcase_local_runbook.md` — local operator runbook to extend.

## Expected Output

- `scripts/check_showcase_parity.py` — parity gate CLI.
- `tests/test_showcase_parity_contract.py` — parity regression tests.
- `docs/showcase_local_runbook.md` — updated report/deck + parity runbook steps.
- `outputs/showcase/deliverables/parity_report.json` — machine-readable parity diagnostics.
