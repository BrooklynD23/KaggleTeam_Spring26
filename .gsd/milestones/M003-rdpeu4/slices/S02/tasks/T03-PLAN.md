---
estimated_steps: 4
estimated_files: 3
skills_used:
  - verification-loop
  - test
---

# T03: Lock S02 downstream handoff contract and UAT replay surfaces

**Slice:** S02 — Model-aware fairness audit runtime on upstream predictions
**Milestone:** M003-rdpeu4

## Description

Close S02 with explicit handoff protection so mitigation/comparator/closeout slices consume one canonical fairness bundle path, schema, and triage workflow.

## Steps

1. Add `tests/test_m003_fairness_audit_handoff_contract.py` to assert required S02 manifest keys, readiness status, baseline-anchor continuity fields, and required subgroup/disparity columns.
2. Update `src/modeling/README.md` with the canonical S02 command, required inputs, output bundle layout, and blocked-upstream triage hints.
3. Author `.gsd/milestones/M003-rdpeu4/slices/S02/S02-UAT.md` with replayable verification commands and expected success/failure signals.
4. Run the full S02 test stack to confirm runtime, handoff tests, and documentation references remain aligned.

## Must-Haves

- [ ] Handoff regression fails if S02 readiness/status fields or required columns drift.
- [ ] Modeling docs define one canonical S02 runtime path and output contract for downstream slices.
- [ ] UAT instructions are executable and reference concrete artifact paths and diagnostic fields.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q`
- `rg -n "fairness_audit|ready_for_mitigation|blocked_upstream|disparity_summary.parquet" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S02/S02-UAT.md`

## Observability Impact

- Signals added/changed: handoff regression locks the manifest/disparity/subgroup keys that downstream slices consume, and docs/UAT explicitly surface `ready_for_mitigation` vs `blocked_upstream` triage fields.
- How a future agent inspects this: run the canonical S02 pytest stack plus `rg` doc checks, then inspect `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S02/S02-UAT.md`, and `outputs/modeling/track_e/fairness_audit/{manifest.json,validation_report.json}`.
- Failure state exposed: handoff drift now fails with explicit missing-key/column assertions, while triage docs make phase-local blocked-upstream diagnostics reproducible without ad hoc investigation.

## Inputs

- `tests/test_m003_track_e_fairness_audit.py` — Runtime behavior and diagnostics expectations from T02.
- `outputs/modeling/track_e/fairness_audit/manifest.json` — Canonical readiness metadata to lock for downstream consumers.
- `outputs/modeling/track_e/fairness_audit/validation_report.json` — Canonical validation/phase diagnostics surface.
- `src/modeling/README.md` — Existing modeling contract docs to extend with S02 runtime details.

## Expected Output

- `tests/test_m003_fairness_audit_handoff_contract.py` — Downstream handoff regression coverage for S02 bundle contract.
- `src/modeling/README.md` — Canonical S02 command/output documentation and triage guidance.
- `.gsd/milestones/M003-rdpeu4/slices/S02/S02-UAT.md` — Replayable S02 verification checklist for milestone closeout and handoff.
