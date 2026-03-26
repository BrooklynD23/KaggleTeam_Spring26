---
estimated_steps: 4
estimated_files: 3
skills_used:
  - test
  - verification-loop
---

# T02: Lock sparse-path handoff contract and canonical mitigation replay docs

**Slice:** S07 — Mitigation ready-path delta closure + closeout rerun
**Milestone:** M003-rdpeu4

## Description

Harden S03 as a stable downstream boundary by enforcing sparse-path diagnostics in handoff tests and documenting one canonical replay/triage flow for mitigation readiness.

## Steps

1. Extend `tests/test_m003_mitigation_handoff_contract.py` to assert sparse-path diagnostics fields are present/valid and continuity payload equality (`baseline_anchor`, `split_context`) remains exact.
2. Update mitigation sections in `src/modeling/README.md` to document sparse-path interpretation, including when blocked diagnostics still represent truthful fail-closed outcomes.
3. Author `.gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md` with canonical replay commands, assertion snippets, and expected status transitions for S03 and S05.
4. Verify docs and handoff tests align to canonical output paths and status vocabulary with no alternate branch semantics.

## Must-Haves

- [ ] Handoff tests prevent silent drift in sparse-path diagnostics and continuity payload semantics.
- [ ] README + S07 UAT define one authoritative replay/triage order for this remediation slice.
- [ ] Documentation explicitly states that readiness must be inferred from artifact payloads, not process exit codes.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q`
- `rg -n "ready_for_closeout|blocked_insufficient_signal|no_comparison_rows_after_alignment|S07" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md`

## Inputs

- `tests/test_m003_mitigation_handoff_contract.py` — Existing S03 handoff assertions to extend for sparse-path diagnostics.
- `src/modeling/README.md` — Canonical modeling contract documentation used by downstream slices.
- `.gsd/milestones/M003-rdpeu4/slices/S07/S07-PLAN.md` — Slice-level goal/demo/verification contract this task must encode in docs/tests.
- `src/modeling/track_e/mitigation_experiment.py` — T01-updated runtime semantics to document and assert.

## Expected Output

- `tests/test_m003_mitigation_handoff_contract.py` — Sparse-path handoff and continuity regression checks.
- `src/modeling/README.md` — Updated mitigation contract and triage documentation for S07-ready semantics.
- `.gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md` — Canonical S07 replay/assertion playbook.

## Observability Impact

- **Signals changed:** S03 handoff contract coverage now treats `lever_metadata.evaluation_diagnostics` as a required machine-readable surface (including sparse-path markers) and enforces exact continuity payload propagation for `baseline_anchor` and `split_context`.
- **How future agents inspect:** Use `tests/test_m003_mitigation_handoff_contract.py` to detect schema/semantic drift in sparse diagnostics and continuity fields, then validate runtime artifacts via `outputs/modeling/track_e/mitigation_experiment/{manifest.json,validation_report.json}` and `outputs/modeling/m003_closeout/manifest.json` following `.gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md`.
- **Failure state visibility:** If sparse diagnostics disappear, mutate shape, or continuity payloads drift, handoff tests fail deterministically; if runtime cannot align groups, docs/tests require explicit blocked reason codes (e.g., `no_comparison_rows_after_alignment`) rather than silent success semantics.
