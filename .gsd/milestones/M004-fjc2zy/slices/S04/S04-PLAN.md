# S04: Report and deck generated from shared narrative/evidence source

**Goal:** Generate final report and presentation deck artifacts from the same canonical showcase narrative/evidence contract used by the website, then prove cross-surface parity so site/report/deck cannot silently drift.
**Demo:** stakeholders can build the final report and presentation deck that mirror site section ordering, claims, and evidence anchors from one shared narrative contract rather than parallel manually curated copies.

## Must-Haves

- Report and deck source artifacts are generated from `outputs/showcase/story/sections.json` + `outputs/showcase/story/tracks.json` (not hand-authored prose copies).
- Generated report/deck preserve canonical executive ordering (`prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`) and include per-track drill-down evidence continuity.
- Claim-to-evidence rows in report/deck carry canonical pointer fields (`surface_key`, `path`, `reason`, `requirement_key`) including blocked states for missing M003 fairness/comparator/closeout surfaces.
- Governance markers (`internal_only`, `aggregate_safe`, `raw_review_text_allowed=false`) are rendered in report/deck outputs.
- A parity checker emits machine-readable diagnostics and fails when website contract artifacts and report/deck artifacts diverge on section order, claim/evidence keys, or requirement-key continuity.
- Runbook includes deterministic local commands to build report/deck and run parity checks.

## Proof Level

- This slice proves: integration

## Integration Closure

Consumes canonical outputs from S02/S03 (`sections.json`, `tracks.json`) and adds deterministic report/deck generation plus parity diagnostics for S05 integrated demo hardening. Remaining milestone closure is end-to-end runtime/demo hardening and governance gate execution in S05.

## Verification

- `python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q`
- `python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables`
- `python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables`
- `python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json`
- `test -f outputs/showcase/deliverables/showcase_report.md && test -f outputs/showcase/deliverables/showcase_deck.md && test -f outputs/showcase/deliverables/parity_report.json`

## Observability / Diagnostics

- Runtime signals: parity status per check class (`section_order`, `evidence_keys`, `pointer_fields`, `requirement_keys`, `governance_markers`) emitted in `outputs/showcase/deliverables/parity_report.json`.
- Inspection surfaces: generated deliverables (`outputs/showcase/deliverables/showcase_report.md`, `outputs/showcase/deliverables/showcase_deck.md`) and parity JSON output.
- Failure visibility: parity checker exits non-zero and records failing check IDs plus mismatch details.
- Redaction constraints: preserve `internal_only`, `aggregate_safe`, and `raw_review_text_allowed=false`; no raw review text in generated deliverables.

## Tasks

- [x] **T01: Generate report and deck artifacts from canonical story/track contracts** `est:2h 15m`
  Why: Advance R012/R011 by making report and deck deterministic outputs of the same contract already consumed by website routes, while preserving R013/R009/R010/R022 continuity fields.
Files: `src/showcase/deliverables_contract.py`, `src/showcase/__init__.py`, `scripts/build_showcase_report.py`, `scripts/build_showcase_deck.py`, `tests/test_showcase_report_contract.py`, `tests/test_showcase_deck_contract.py`, `outputs/showcase/deliverables/showcase_report.md`, `outputs/showcase/deliverables/showcase_deck.md`
Do: Implement a shared deliverables contract builder that ingests `sections.json` and `tracks.json`; render deterministic markdown report and deck-source markdown with canonical executive ordering first, then track drill-down continuity; include governance markers and canonical evidence pointer fields (including blocked diagnostics and requirement keys); add CLI scripts following existing `build_showcase_*` conventions; add regression tests asserting ordering, evidence-field parity, and governance marker preservation.
Verify: `python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py -q && python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables && python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables && test -f outputs/showcase/deliverables/showcase_report.md && test -f outputs/showcase/deliverables/showcase_deck.md`
Done when: report/deck artifacts regenerate deterministically from story/track contracts and retain required governance + blocked-evidence continuity fields.
  - Files: `src/showcase/deliverables_contract.py`, `src/showcase/__init__.py`, `scripts/build_showcase_report.py`, `scripts/build_showcase_deck.py`, `tests/test_showcase_report_contract.py`, `tests/test_showcase_deck_contract.py`, `outputs/showcase/deliverables/showcase_report.md`, `outputs/showcase/deliverables/showcase_deck.md`
  - Verify: python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py -q && python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables && python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables && test -f outputs/showcase/deliverables/showcase_report.md && test -f outputs/showcase/deliverables/showcase_deck.md

- [x] **T02: Add site-report-deck parity diagnostics and local runbook wiring** `est:1h 45m`
  Why: Close R012 continuity risk by making drift mechanically detectable and operator-visible, then document repeatable local verification for S05 handoff.
Files: `scripts/check_showcase_parity.py`, `tests/test_showcase_parity_contract.py`, `docs/showcase_local_runbook.md`, `outputs/showcase/deliverables/parity_report.json`
Do: Implement a parity checker that compares website source artifacts (`sections.json`, `tracks.json`) against generated report/deck artifacts for section order, evidence identifiers, pointer fields, requirement keys, and governance markers; emit `parity_report.json` with pass/fail checks and reason details; fail non-zero on drift; add regression tests for pass/fail cases; extend runbook with report/deck generation + parity command sequence (including optional Marp export note as packaging, not contract truth).
Verify: `python -m pytest tests/test_showcase_parity_contract.py -q && python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json && test -f outputs/showcase/deliverables/parity_report.json`
Done when: parity checker fails on contract drift, succeeds on aligned artifacts, and runbook includes end-to-end commands to regenerate and validate deliverables locally.
  - Files: `scripts/check_showcase_parity.py`, `tests/test_showcase_parity_contract.py`, `docs/showcase_local_runbook.md`, `outputs/showcase/deliverables/parity_report.json`
  - Verify: python -m pytest tests/test_showcase_parity_contract.py -q && python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json && test -f outputs/showcase/deliverables/parity_report.json

## Files Likely Touched

- src/showcase/deliverables_contract.py
- src/showcase/__init__.py
- scripts/build_showcase_report.py
- scripts/build_showcase_deck.py
- tests/test_showcase_report_contract.py
- tests/test_showcase_deck_contract.py
- outputs/showcase/deliverables/showcase_report.md
- outputs/showcase/deliverables/showcase_deck.md
- scripts/check_showcase_parity.py
- tests/test_showcase_parity_contract.py
- docs/showcase_local_runbook.md
- outputs/showcase/deliverables/parity_report.json
