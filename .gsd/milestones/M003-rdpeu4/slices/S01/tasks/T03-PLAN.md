---
estimated_steps: 4
estimated_files: 3
skills_used:
  - verification-loop
  - coding-standards
---

# T03: Lock downstream handoff wiring with intake contract regression and runbook updates

**Slice:** S01 — Upstream audit-intake contract on reproducible scored artifacts
**Milestone:** M003-rdpeu4

## Description

Close S01 by making downstream consumption explicit: add a handoff regression test, document the authoritative intake command/layout, and publish an S01 UAT checklist that future slices can replay.

## Steps

1. Add a handoff contract test that asserts required manifest fields, intake status, and minimum scored-intake columns expected by S02/S03/S04.
2. Update modeling documentation with the canonical intake command, required inputs, and output bundle layout.
3. Create S01 UAT instructions that replay the slice verification commands in milestone-local context.
4. Run the full S01 verification suite to confirm tests, docs, and runtime command stay aligned.

## Must-Haves

- [ ] Downstream slices have one documented canonical intake path and do not rely on ad hoc file/column discovery.
- [ ] Handoff tests fail if readiness status, schema fields, or manifest anchors drift.
- [ ] S01 UAT instructions are executable and reference concrete commands/paths in this repo.

## Verification

- `python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py`
- `rg -n "audit_intake|ready_for_fairness_audit|scored_intake.parquet|validation_report.json" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md`

## Observability Impact

- Signals changed: `tests/test_m003_intake_handoff_contract.py` becomes the canonical drift alarm for readiness status, manifest anchors, and scored-intake handoff columns consumed by S02/S03/S04.
- Inspection surfaces: run `python -m pytest tests/test_m003_intake_handoff_contract.py` and inspect `outputs/modeling/track_a/audit_intake/manifest.json` + `validation_report.json` when failures occur.
- Failure visibility: pytest assertions expose explicit missing/changed manifest keys, readiness-status drift, and required-column drift instead of downstream runtime joins failing later.

## Inputs

- `tests/test_m003_track_a_audit_intake.py` — Existing runtime/failure-path checks from T02
- `outputs/modeling/track_a/audit_intake/manifest.json` — Canonical readiness metadata to lock with handoff tests
- `outputs/modeling/track_a/audit_intake/validation_report.json` — Contract validation diagnostics surface
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-ROADMAP.md` — Expected downstream dependency wiring for S02/S03/S04

## Expected Output

- `tests/test_m003_intake_handoff_contract.py` — Downstream intake handoff regression test
- `src/modeling/README.md` — Canonical intake command and output layout documentation
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md` — Replayable S01 verification/runbook for future slices
