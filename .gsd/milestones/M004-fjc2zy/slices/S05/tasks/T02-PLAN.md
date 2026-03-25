---
estimated_steps: 5
estimated_files: 5
skills_used:
  - verification-loop
  - react-best-practices
  - e2e-testing
---

# T02: Add one-command integrated demo gate with governance and no-live-query enforcement

**Slice:** S05 — Integrated local demo hardening and governance gate
**Milestone:** M004-fjc2zy

## Description

Create the final assembly gate command that executes the full showcase verification chain (artifact build, parity, frontend checks, smoke, governance/no-live-query assertions) and emits one machine-readable closeout report.

## Steps

1. Add orchestration module `src/showcase/demo_gate.py` that defines ordered gate phases and a fail-closed runner for build/parity/frontend/smoke/governance checks.
2. Add CLI entrypoint `scripts/run_showcase_demo_gate.py` that accepts config/base-url/output arguments, executes phases, and writes `outputs/showcase/verification/demo_gate_report.json`.
3. Implement governance/no-live-query assertion phase that checks canonical governance markers and blocks prohibited runtime patterns (e.g., live query imports/patterns in `showcase/app` + `showcase/lib`, and presence of `showcase/app/api/**`).
4. Add `tests/test_showcase_demo_gate.py` covering report schema, phase ordering, fail-closed semantics, and representative governance/no-live-query violations.
5. Update `docs/showcase_local_runbook.md` so the one-command integrated gate is the primary local demo flow, with existing step-by-step commands kept as fallback debugging path.

## Must-Haves

- [ ] One command runs all required S05 verification phases and exits non-zero on first failing phase.
- [ ] Gate report is machine-readable and includes per-phase status with failure context.
- [ ] Governance markers and no-live-query boundaries are explicitly asserted by the gate.
- [ ] Runbook starts with the integrated gate command and references fallback phase-by-phase debugging.

## Verification

- `python -m pytest tests/test_showcase_demo_gate.py -q`
- `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json`
- `test -f outputs/showcase/verification/demo_gate_report.json`

## Observability Impact

- Signals added/changed: per-phase gate status and failure payloads persisted to `demo_gate_report.json`.
- How a future agent inspects this: open `outputs/showcase/verification/demo_gate_report.json` and identify the first failing phase + message.
- Failure state exposed: explicit gate failure class for parity drift, frontend test/build failure, smoke mismatch, governance marker breach, or no-live-query boundary violation.

## Inputs

- `configs/showcase.yaml` — canonical intake/story/tracks/report/deck configuration and governance markers.
- `scripts/build_showcase_intake.py` — intake artifact generation phase.
- `scripts/build_showcase_story.py` — executive story artifact generation phase.
- `scripts/build_showcase_tracks.py` — track artifact generation phase.
- `scripts/build_showcase_report.py` — report generation phase.
- `scripts/build_showcase_deck.py` — deck generation phase.
- `scripts/check_showcase_parity.py` — report/deck parity gate phase.
- `scripts/showcase_smoke_check.py` — runtime parity smoke phase.
- `docs/showcase_local_runbook.md` — local demo operator instructions to update.

## Expected Output

- `src/showcase/demo_gate.py` — integrated gate orchestration + boundary assertion logic.
- `scripts/run_showcase_demo_gate.py` — one-command demo gate CLI.
- `tests/test_showcase_demo_gate.py` — integration/hardening regression coverage for gate behavior.
- `docs/showcase_local_runbook.md` — one-command-first runbook flow.
- `outputs/showcase/verification/demo_gate_report.json` — machine-readable closeout evidence artifact from gate runs.
