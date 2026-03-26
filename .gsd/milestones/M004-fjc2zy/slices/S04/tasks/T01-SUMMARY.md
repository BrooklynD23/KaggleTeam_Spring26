---
id: T01
parent: S04
milestone: M004-fjc2zy
key_files:
  - src/showcase/deliverables_contract.py
  - src/showcase/__init__.py
  - scripts/build_showcase_report.py
  - scripts/build_showcase_deck.py
  - tests/test_showcase_report_contract.py
  - tests/test_showcase_deck_contract.py
  - outputs/showcase/deliverables/showcase_report.md
  - outputs/showcase/deliverables/showcase_deck.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Centralized report/deck generation through a single deliverables normalization/render contract to prevent cross-surface drift.
  - Standardized markdown evidence tables across report/deck to always include canonical pointer fields and blocked M003 diagnostics for downstream parity tooling.
  - Embedded governance markers and source-artifact references directly in generated deliverables as first-class observability signals.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T05:00:20.526Z
blocker_discovered: false
---

# T01: Implement shared showcase deliverables contract and deterministic report/deck generators with regression coverage.

**Implement shared showcase deliverables contract and deterministic report/deck generators with regression coverage.**

## What Happened

Activated required skills, validated local S04/T01 plan context, and inspected existing showcase intake/story/track contract + CLI patterns before editing. Implemented `src/showcase/deliverables_contract.py` as the shared normalization/render layer that loads `sections.json` + `tracks.json`, enforces canonical executive/track ordering, normalizes pointer fields (`surface_key`, `path`, `reason`, `requirement_key`), and emits blocked M003 diagnostics. Added deterministic markdown renderers for both report and deck outputs, including governance markers (`internal_only`, `aggregate_safe`, `raw_review_text_allowed`) and continuity rollups/source references for observability. Added new CLIs `scripts/build_showcase_report.py` and `scripts/build_showcase_deck.py` following existing `build_showcase_*` conventions; both write deterministic artifacts under `outputs/showcase/deliverables/` and print summary signals (`sections`, `tracks`, `blocked_m003`). Wired exports in `src/showcase/__init__.py`. Added regression suites `tests/test_showcase_report_contract.py` and `tests/test_showcase_deck_contract.py` to verify canonical ordering, governance marker rendering, pointer-field continuity, blocked M003 diagnostics presence, and CLI artifact creation. Generated deliverables from real story/track inputs and confirmed report/deck artifacts materialize with required contract fields. Also ran slice-level checks; parity-specific checks failed as expected because parity test/script are owned by T02 and are not present yet. Recorded one architecture decision in DECISIONS (D062) and added a knowledge entry clarifying expected T01 parity-check failure mode.

## Verification

Task-level verification passed end-to-end: pytest for new report/deck suites succeeded, both build scripts generated artifacts from canonical story/track inputs, and required report/deck files exist. Observability impact was verified directly by inspecting generated markdown artifacts and confirming source artifact references, section/track rollup counts, governance markers, and blocked M003 diagnostics tables are present. Slice-level full verification was also executed: parity checks currently fail due missing T02-owned parity test/script/parity JSON output, which is expected at this intermediate task boundary.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py -q && python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables && python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables && test -f outputs/showcase/deliverables/showcase_report.md && test -f outputs/showcase/deliverables/showcase_deck.md` | 0 | ✅ pass | 441ms |
| 2 | `python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q` | 4 | ❌ fail | 157ms |
| 3 | `python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json` | 2 | ❌ fail | 16ms |
| 4 | `test -f outputs/showcase/deliverables/showcase_report.md && test -f outputs/showcase/deliverables/showcase_deck.md && test -f outputs/showcase/deliverables/parity_report.json` | 1 | ❌ fail | 1ms |


## Deviations

Ran full slice-level verification commands in addition to T01 verification to capture intermediate-state evidence; parity-related checks failed because T02 artifacts are not implemented yet.

## Known Issues

Slice-level parity checks remain failing until T02 adds `tests/test_showcase_parity_contract.py`, `scripts/check_showcase_parity.py`, and `outputs/showcase/deliverables/parity_report.json`.

## Files Created/Modified

- `src/showcase/deliverables_contract.py`
- `src/showcase/__init__.py`
- `scripts/build_showcase_report.py`
- `scripts/build_showcase_deck.py`
- `tests/test_showcase_report_contract.py`
- `tests/test_showcase_deck_contract.py`
- `outputs/showcase/deliverables/showcase_report.md`
- `outputs/showcase/deliverables/showcase_deck.md`
- `.gsd/KNOWLEDGE.md`
