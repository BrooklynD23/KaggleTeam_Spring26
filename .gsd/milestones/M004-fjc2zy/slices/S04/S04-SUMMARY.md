---
id: S04
parent: M004-fjc2zy
milestone: M004-fjc2zy
provides:
  - Canonical report artifact generated from `sections.json` + `tracks.json`.
  - Canonical deck-source artifact generated from `sections.json` + `tracks.json`.
  - Machine-readable parity diagnostics and a fail-closed parity gate for site/report/deck continuity.
  - Runbook command sequence for deterministic local regeneration and parity validation.
requires:
  - slice: S02
    provides: Canonical executive story contract and section ordering in `outputs/showcase/story/sections.json`.
  - slice: S03
    provides: Canonical track drill-down contract and evidence pointer continuity in `outputs/showcase/story/tracks.json`.
affects:
  - S05
key_files:
  - src/showcase/deliverables_contract.py
  - scripts/build_showcase_report.py
  - scripts/build_showcase_deck.py
  - scripts/check_showcase_parity.py
  - tests/test_showcase_report_contract.py
  - tests/test_showcase_deck_contract.py
  - tests/test_showcase_parity_contract.py
  - outputs/showcase/deliverables/showcase_report.md
  - outputs/showcase/deliverables/showcase_deck.md
  - outputs/showcase/deliverables/parity_report.json
  - docs/showcase_local_runbook.md
key_decisions:
  - Generate report/deck only from canonical story and track contracts consumed by the website to eliminate parallel narrative drift.
  - Class parity diagnostics into explicit check families (`section_order`, `evidence_keys`, `pointer_fields`, `requirement_keys`, `governance_markers`) with machine-readable mismatch payloads.
  - Validate requirement continuity per `evidence_key` row rather than only global requirement-ID set membership.
patterns_established:
  - Contract-first multi-surface publishing: website/report/deck all consume the same generated story/evidence source.
  - Deterministic markdown output pattern with explicit governance markers and blocked-evidence diagnostics.
  - Fail-closed parity CLI pattern: write JSON diagnostics and return non-zero on contract drift for CI/demo gating.
observability_surfaces:
  - outputs/showcase/deliverables/parity_report.json check-level pass/fail diagnostics with mismatch payloads.
  - CLI summary signals from report/deck builders (`sections`, `tracks`, `blocked_m003`).
  - Non-zero parity CLI exit behavior for drift detection.
  - docs/showcase_local_runbook.md deterministic regenerate-and-verify command chain.
drill_down_paths:
  - .gsd/milestones/M004-fjc2zy/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S04/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-25T05:06:50.362Z
blocker_discovered: false
---

# S04: Report and deck generated from shared narrative/evidence source

**S04 shipped deterministic report/deck generators from canonical story contracts plus a machine-readable parity gate that fails on cross-surface drift.**

## What Happened

S04 completed both planned tasks and converted report/deck creation from manual prose risk to contract-driven generation. T01 introduced a shared deliverables normalization/render layer in `src/showcase/deliverables_contract.py` and wired CLI builders for report and deck so both outputs are derived from `outputs/showcase/story/sections.json` and `outputs/showcase/story/tracks.json` with canonical executive ordering, claim-to-evidence pointer fields, blocked M003 diagnostics, and governance markers preserved. T02 added `scripts/check_showcase_parity.py` and regression coverage that parses generated report/deck artifacts, compares them to canonical story/track contract truth, emits `outputs/showcase/deliverables/parity_report.json`, and exits non-zero on drift across section order, evidence keys, pointer fields, requirement continuity, and governance markers. Runbook wiring was updated so local operators can regenerate artifacts and run parity checks deterministically before demo packaging. During closure, slice-level verification was rerun end-to-end and parity diagnostics were inspected to confirm all five check classes pass with zero mismatches.

## Verification

Executed the full slice verification chain successfully: `python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q` (9 passed), `python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables`, `python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables`, `python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json`, and artifact existence checks for report/deck/parity JSON. Observability surfaces verified directly in `parity_report.json` showed `parity_passed=true`, 5/5 checks passed, and no mismatch payloads.

## Requirements Advanced

- R012 — Added deterministic report/deck generation from canonical story contracts plus parity diagnostics so narrative ordering, claims, and evidence anchors are mechanically enforced across surfaces.
- R011 — Extended local showcase delivery contract with reproducible non-UI artifacts (report/deck) built from the same exported evidence surfaces used by site routes.
- R013 — Preserved and verified governance markers (`internal_only`, `aggregate_safe`, `raw_review_text_allowed=false`) in generated report/deck outputs and parity checks.
- R009 — Carried Track E fairness/mitigation continuity through canonical pointer fields and blocked diagnostic rows in report/deck evidence tables.
- R010 — Carried stronger-comparator continuity into report/deck claim-to-evidence rows with requirement-linked pointers and parity enforcement.
- R022 — Preserved closeout compute-escalation continuity as requirement-keyed evidence pointers in canonical report/deck surfaces.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

Integrated live runtime + smoke + governance/no-live-query hardening is still pending S05 milestone closure; S04 proves contract continuity and drift detection for artifacts, not full end-to-end demo readiness.

## Follow-ups

S05 should execute one integrated gate that combines showcase runtime smoke checks with the S04 parity checker and governance/no-live-query assertions, then capture that evidence in milestone closeout artifacts.

## Files Created/Modified

- `src/showcase/deliverables_contract.py` — Added shared normalization/render contract for report/deck generation with canonical ordering, pointer fields, blocked diagnostics, and governance metadata.
- `src/showcase/__init__.py` — Exported deliverables contract primitives for script/test consumption.
- `scripts/build_showcase_report.py` — Added deterministic report builder CLI from canonical story/tracks inputs.
- `scripts/build_showcase_deck.py` — Added deterministic deck-source builder CLI from canonical story/tracks inputs.
- `tests/test_showcase_report_contract.py` — Added regression coverage for report ordering, pointer continuity, and governance marker preservation.
- `tests/test_showcase_deck_contract.py` — Added regression coverage for deck ordering, pointer continuity, and governance marker preservation.
- `scripts/check_showcase_parity.py` — Added fail-closed parity checker comparing story/tracks truth vs generated report/deck with machine-readable diagnostics.
- `tests/test_showcase_parity_contract.py` — Added pass/fail parity regression tests across section order, evidence keys, pointer fields, requirement continuity, and governance markers.
- `docs/showcase_local_runbook.md` — Documented deterministic local commands for building report/deck and running parity diagnostics, with optional packaging note.
- `outputs/showcase/deliverables/showcase_report.md` — Generated canonical report artifact from story/tracks contracts.
- `outputs/showcase/deliverables/showcase_deck.md` — Generated canonical deck-source artifact from story/tracks contracts.
- `outputs/showcase/deliverables/parity_report.json` — Generated parity diagnostics artifact with check-level pass/fail and mismatch payloads.
- `.gsd/REQUIREMENTS.md` — Updated R012 validation/ownership notes to reflect S04 report/deck continuity and parity evidence while keeping S05 integration closure pending.
- `.gsd/DECISIONS.md` — Appended D063 to record row-level requirement continuity policy in parity diagnostics.
- `.gsd/PROJECT.md` — Updated project state to mark S04 complete and note M004 now has S01–S04 done with S05 pending.
- `.gsd/KNOWLEDGE.md` — Captured S04 continuity/parity gotchas for future slices (expected T01 parity failure pre-T02 and per-evidence requirement-key validation).
