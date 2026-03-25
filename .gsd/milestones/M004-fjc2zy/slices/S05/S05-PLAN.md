# S05: Integrated local demo hardening and governance gate

**Goal:** Deliver a deterministic, one-command local demo gate that proves the assembled showcase runtime, report, and deck are launch-ready with explicit governance and no-live-query enforcement.
**Demo:** one end-to-end local demo path proves website + report + deck assembled reality, including smoke checks, parity checks, no-live-query assertions, and governance-safe output verification.

## Must-Haves

- A single integrated gate command exists (`python scripts/run_showcase_demo_gate.py ...`) and executes full local demo verification without manual orchestration (R011).
- The integrated gate enforces canonical continuity checks across site/report/deck contracts and fails closed on drift (R012).
- Governance markers remain explicitly asserted (`internal_only`, `aggregate_safe`, `raw_review_text_allowed=false`) and any violation fails the gate (R013).
- Blocked closeout continuity diagnostics tied to required M003 evidence pointers remain visible and are explicitly asserted in gate output (R022).
- Fairness/comparator continuity evidence rows remain asserted as required blocked/ready diagnostics in smoke + gate phases (R009, R010 support).
- The gate emits a machine-readable verification artifact at `outputs/showcase/verification/demo_gate_report.json` for closeout evidence.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_showcase_smoke_check.py tests/test_showcase_demo_gate.py -q`
- `python -m pytest tests/test_showcase_intake_contract.py tests/test_showcase_story_contract.py tests/test_showcase_track_contract.py tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q`
- `npm --prefix showcase run test -- --run`
- `npm --prefix showcase run build`
- `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json`
- `test -f outputs/showcase/verification/demo_gate_report.json`

## Observability / Diagnostics

- Runtime signals: phase-level status (`build_artifacts`, `parity`, `frontend_test`, `frontend_build`, `runtime_smoke`, `governance_boundary`) with per-phase command/result metadata.
- Inspection surfaces: `outputs/showcase/verification/demo_gate_report.json`, smoke CLI PASS/FAIL output, parity JSON output, and runbook command path.
- Failure visibility: deterministic failing phase ID, command, exit code (if any), and failure message/payload for fast triage.
- Redaction constraints: keep internal-only + aggregate-safe boundary and raw-review-text prohibition explicit; no raw review text emitted in diagnostics.

## Integration Closure

- Upstream surfaces consumed: `outputs/showcase/intake/manifest.json`, `outputs/showcase/story/sections.json`, `outputs/showcase/story/tracks.json`, `outputs/showcase/deliverables/showcase_report.md`, `outputs/showcase/deliverables/showcase_deck.md`, `outputs/showcase/deliverables/parity_report.json` plus S01–S04 builder/smoke/parity scripts.
- New wiring introduced in this slice: one integrated gate entrypoint that composes build/parity/frontend/smoke/governance phases and writes a unified gate report.
- What remains before the milestone is truly usable end-to-end: nothing beyond running the integrated gate successfully on the local demo machine.

## Tasks

- [x] **T01: Harden showcase smoke lifecycle and readiness error semantics** `est:1h 45m`
  - Why: S05 depends on deterministic runtime smoke checks; current auto-start behavior can leak dev-server descendants and blur unreachable vs HTTP-failing readiness states.
  - Files: `scripts/showcase_smoke_check.py`, `tests/test_showcase_smoke_check.py`, `docs/showcase_local_runbook.md`
  - Do: Make auto-start cleanup process-group aware, classify connection/refusal vs reachable-HTTP-error readiness failures explicitly, and preserve existing homepage/executive/track parity assertions with regression coverage for the new failure semantics.
  - Verify: `python -m pytest tests/test_showcase_smoke_check.py -q`
  - Done when: repeated smoke runs leave no stale local dev server from auto-start and failures report distinct actionable causes for unreachable host vs reachable HTTP error.

- [x] **T02: Add one-command integrated demo gate with governance and no-live-query enforcement** `est:2h 30m`
  - Why: M004 closure requires one executable assembly gate proving website/report/deck continuity and governance boundaries together, not a manual runbook chain.
  - Files: `src/showcase/demo_gate.py`, `scripts/run_showcase_demo_gate.py`, `tests/test_showcase_demo_gate.py`, `docs/showcase_local_runbook.md`, `outputs/showcase/verification/demo_gate_report.json`
  - Do: Implement a fail-closed orchestrator that runs builders/parity/frontend checks/smoke checks, add governance+no-live-query boundary assertions (including no `showcase/app/api/**` and no live-query patterns in showcase runtime code), emit machine-readable gate diagnostics JSON, and make runbook default to this command.
  - Verify: `python -m pytest tests/test_showcase_demo_gate.py -q && python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json && test -f outputs/showcase/verification/demo_gate_report.json`
  - Done when: one command produces a pass/fail gate report with phase-level evidence for parity, smoke, governance markers, and no-live-query enforcement.

## Files Likely Touched

- `scripts/showcase_smoke_check.py`
- `tests/test_showcase_smoke_check.py`
- `src/showcase/demo_gate.py`
- `scripts/run_showcase_demo_gate.py`
- `tests/test_showcase_demo_gate.py`
- `docs/showcase_local_runbook.md`
- `outputs/showcase/verification/demo_gate_report.json`
