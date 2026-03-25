---
id: T02
parent: S04
milestone: M004-fjc2zy
key_files:
  - scripts/check_showcase_parity.py
  - tests/test_showcase_parity_contract.py
  - docs/showcase_local_runbook.md
  - outputs/showcase/deliverables/parity_report.json
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Parity diagnostics are classed into five explicit check classes (`section_order`, `evidence_keys`, `pointer_fields`, `requirement_keys`, `governance_markers`) with structured mismatch payloads so drift triage does not require manual markdown diffing.
  - Requirement continuity validation compares expected `requirement_key` per `evidence_key` (not only global requirement-key set membership) to catch row-level contract drift that set-based checks can miss.
duration: ""
verification_result: passed
completed_at: 2026-03-25T05:04:47.692Z
blocker_discovered: false
---

# T02: Implemented deterministic showcase parity CLI, regression tests, and runbook wiring for site-report-deck drift diagnostics.

**Implemented deterministic showcase parity CLI, regression tests, and runbook wiring for site-report-deck drift diagnostics.**

## What Happened

Implemented `scripts/check_showcase_parity.py` as a deterministic parity gate that loads canonical story/track artifacts, parses generated report/deck markdown, and evaluates five check classes: `section_order`, `evidence_keys`, `pointer_fields`, `requirement_keys`, and `governance_markers`. The CLI now emits machine-readable diagnostics to `parity_report.json`, including per-check pass/fail plus mismatch payloads, and exits non-zero on drift. Added `tests/test_showcase_parity_contract.py` with pass/fail fixtures that prove drift detection for section ordering, pointer-field continuity, requirement-key continuity, and governance markers. Updated `docs/showcase_local_runbook.md` to include deterministic report/deck regeneration and parity execution commands, plus optional Marp packaging guidance explicitly marked as packaging-only. Verified observability impact by inspecting `outputs/showcase/deliverables/parity_report.json` and confirming it records check-level status and mismatch fields for triage.

## Verification

Ran task-level checks (`test_showcase_parity_contract.py`, parity CLI, parity file presence) and then executed full slice-level verification (`report/deck/parity` tests, report/deck generators, parity checker, and file existence gate). All commands passed. Inspected parity JSON directly to confirm required diagnostic classes and mismatch surfaces are emitted.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_parity_contract.py -q` | 0 | ✅ pass | 499ms |
| 2 | `python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json` | 0 | ✅ pass | 60ms |
| 3 | `test -f outputs/showcase/deliverables/parity_report.json` | 0 | ✅ pass | 0ms |
| 4 | `python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q` | 0 | ✅ pass | 620ms |
| 5 | `python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables` | 0 | ✅ pass | 51ms |
| 6 | `python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables` | 0 | ✅ pass | 55ms |
| 7 | `python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json` | 0 | ✅ pass | 59ms |
| 8 | `test -f outputs/showcase/deliverables/showcase_report.md && test -f outputs/showcase/deliverables/showcase_deck.md && test -f outputs/showcase/deliverables/parity_report.json` | 0 | ✅ pass | 0ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `scripts/check_showcase_parity.py`
- `tests/test_showcase_parity_contract.py`
- `docs/showcase_local_runbook.md`
- `outputs/showcase/deliverables/parity_report.json`
- `.gsd/KNOWLEDGE.md`
