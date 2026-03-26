---
id: S05
parent: M004-fjc2zy
milestone: M004-fjc2zy
provides:
  - Canonical integrated local-demo gate command and report schema for end-to-end showcase verification.
  - Deterministic runtime smoke startup semantics with explicit failure taxonomy and cleanup guarantees.
  - Governance/no-live-query enforcement boundaries captured as machine-readable phase diagnostics.
requires:
  - slice: S01
    provides: Canonical intake manifest/validation surfaces and homepage blocked-diagnostic contract consumed by smoke and gate build phase.
  - slice: S02
    provides: Executive narrative contract (`sections.json`) and runtime parity assertions consumed by smoke and parity phases.
  - slice: S03
    provides: Track drill-down contract (`tracks.json`) and required evidence-pointer continuity consumed by smoke and parity checks.
  - slice: S04
    provides: Report/deck generators and parity checker outputs consumed by integrated gate parity + continuity enforcement.
affects:
  []
key_files:
  - scripts/showcase_smoke_check.py
  - src/showcase/demo_gate.py
  - scripts/run_showcase_demo_gate.py
  - tests/test_showcase_smoke_check.py
  - tests/test_showcase_demo_gate.py
  - docs/showcase_local_runbook.md
  - outputs/showcase/verification/demo_gate_report.json
  - outputs/showcase/deliverables/parity_report.json
key_decisions:
  - Use explicit startup readiness classes (`unreachable`/`http_error`/`timeout`) plus process-group teardown for deterministic smoke lifecycle management.
  - Enforce governance and no-live-query policies in a dedicated `governance_boundary` gate phase with structured machine-readable violations.
  - Keep integrated gate execution fail-closed by phase while still persisting per-phase command evidence for triage.
patterns_established:
  - One-command assembled verification gate that composes build/parity/frontend/smoke/governance into a deterministic phase contract.
  - Fail-closed orchestration with always-written JSON diagnostics for CI and manual triage parity.
  - Governance-as-code checks embedded in runtime verification (marker assertions + route/file pattern scanning).
  - Contract-first continuity where blocked evidence diagnostics remain visible and testable rather than treated as implicit failures.
observability_surfaces:
  - outputs/showcase/verification/demo_gate_report.json (phase statuses, command metadata, failing_phase_id, governance signals)
  - outputs/showcase/deliverables/parity_report.json (section/evidence/pointer/requirement/governance continuity checks)
  - showcase smoke CLI PASS/FAIL stream with explicit startup failure classes and route parity assertions
  - docs/showcase_local_runbook.md integrated-gate primary flow + fallback debug flow
drill_down_paths:
  - .gsd/milestones/M004-fjc2zy/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S05/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-25T05:34:04.665Z
blocker_discovered: false
---

# S05: Integrated local demo hardening and governance gate

**Delivered a one-command, fail-closed local demo gate that proves website/report/deck assembly with parity, smoke, governance, and no-live-query enforcement plus machine-readable diagnostics.**

## What Happened

S05 closed M004 integration risk by hardening both the runtime smoke lifecycle and the final assembled verification path. T01 upgraded `scripts/showcase_smoke_check.py` to use process-group-aware auto-start cleanup and explicit readiness outcome classes (`unreachable`, `http_error`, `timeout`) so repeated runs are deterministic and startup failures are actionable. T02 implemented `src/showcase/demo_gate.py` and `scripts/run_showcase_demo_gate.py` as a canonical integrated gate that executes build/parity/frontend/smoke/governance phases in deterministic order, fails closed on first failing phase, and persists structured report data to `outputs/showcase/verification/demo_gate_report.json`. The governance boundary phase enforces canonical markers (`internal_only=true`, `aggregate_safe=true`, `raw_review_text_allowed=false`), blocks `showcase/app/api/**`, and scans showcase runtime source for disallowed live-query patterns. The runbook was updated to make the integrated gate the default operator path, with phase-by-phase fallback commands retained for debugging.

## Verification

Executed all slice-plan verification checks and confirmed observability surfaces. Passed: `python -m pytest tests/test_showcase_smoke_check.py tests/test_showcase_demo_gate.py -q` (8 passed), `python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q` (18 passed), `npm --prefix showcase run test -- --run` (7 files / 18 tests passed), `npm --prefix showcase run build` (Next.js production build succeeded), `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json` (all 6 phases passed), and `test -f outputs/showcase/verification/demo_gate_report.json` (file present). Confirmed observability surfaces: parity report (`outputs/showcase/deliverables/parity_report.json`) passed all 5 checks; demo gate report records canonical phase order, per-command metadata, failing-phase pointer field, and governance signals (`api_route_files=[]`, `live_query_violations=0`, marker checks true).

## Requirements Advanced

- R013 — Operationalized governance continuity in end-to-end gate execution via explicit marker checks and no-live-query policy enforcement.
- R022 — Preserved and asserted blocked closeout continuity diagnostics in smoke and integrated gate outputs used by showcase/runtime surfaces.
- R009 — Kept fairness continuity evidence visible as required blocked/ready diagnostics through intake/story/tracks/smoke parity and integrated gate phases.
- R010 — Kept stronger-model comparator continuity evidence visible as required blocked/ready diagnostics in assembled demo verification.

## Requirements Validated

- R011 — Full integrated gate stack passed (smoke/demo-gate pytest suites, showcase contract suites, frontend test/build, and `run_showcase_demo_gate` with generated `outputs/showcase/verification/demo_gate_report.json`) proving local-hosted assembled runtime verification is launch-ready.
- R012 — Parity contract suites passed and `outputs/showcase/deliverables/parity_report.json` recorded all continuity checks passing; integrated gate enforces these checks in end-to-end execution, validating cross-surface narrative/evidence coherence.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

The integrated gate currently targets local assembled verification and contract continuity only; it does not execute human-experience scoring or public-hosting checks (intentionally out of scope for M004).

## Follow-ups

Milestone closeout should record M004 completion with a milestone-level summary referencing `outputs/showcase/verification/demo_gate_report.json` as the authoritative integrated proof surface.

## Files Created/Modified

- `scripts/showcase_smoke_check.py` — Hardened auto-start lifecycle with process-group cleanup and explicit readiness failure classification semantics.
- `tests/test_showcase_smoke_check.py` — Added regression coverage for process-group startup/teardown behavior and readiness classification/messaging branches.
- `src/showcase/demo_gate.py` — Implemented integrated fail-closed phase orchestrator with report schema, command metadata capture, and governance/no-live-query assertions.
- `scripts/run_showcase_demo_gate.py` — Added CLI entrypoint for one-command gate execution with output report writing and phase status reporting.
- `tests/test_showcase_demo_gate.py` — Added unit tests for phase ordering, fail-closed behavior, report shape, and governance boundary violation detection.
- `docs/showcase_local_runbook.md` — Promoted integrated demo gate to the primary operator flow and documented fallback debugging + hardened startup semantics.
- `outputs/showcase/verification/demo_gate_report.json` — Persisted machine-readable integrated verification evidence from successful gate execution.
- `outputs/showcase/deliverables/parity_report.json` — Persisted passing report/deck continuity evidence used by integrated gate parity phase.
- `.gsd/REQUIREMENTS.md` — Updated requirement states and validation evidence to mark R011 and R012 as validated and annotate R022 continuity support from S05.
- `.gsd/DECISIONS.md` — Appended D066 documenting readiness-classification and process-group-cleanup decision for smoke lifecycle determinism.
- `.gsd/KNOWLEDGE.md` — Appended S05 operational lessons on readiness failure classes and authoritative integrated gate diagnostics usage.
- `.gsd/PROJECT.md` — Refreshed project state to reflect S05 completion and M004 readiness for milestone closeout.
