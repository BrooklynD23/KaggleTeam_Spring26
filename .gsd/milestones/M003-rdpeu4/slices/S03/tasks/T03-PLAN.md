---
estimated_steps: 4
estimated_files: 3
skills_used:
  - verification-loop
  - test
---

# T03: Lock S03 handoff continuity and replay docs for S05 consumption

**Slice:** S03 — One mitigation lever with pre/post fairness-accuracy deltas
**Milestone:** M003-rdpeu4

## Description

Close S03 with downstream-safe handoff protections so S05/M004 can trust mitigation artifacts, continuity fields, and replay instructions without re-discovering semantics.

## Steps

1. Add `tests/test_m003_mitigation_handoff_contract.py` to lock required S03 manifest keys, status vocabulary, continuity fields (`split_context`, `baseline_anchor`), and required pre/post delta columns.
2. Update `src/modeling/README.md` with canonical S03 command, required inputs, output layout, and blocked-status triage guidance.
3. Author `.gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md` with executable replay checks and artifact assertions for ready and blocked flows.
4. Run the full S03 test stack and doc keyword checks to confirm runtime/contract/docs are aligned.

## Must-Haves

- [ ] Handoff tests fail if S03 continuity payloads drift from S02 anchors.
- [ ] Modeling docs declare exactly one canonical S03 command/path/status contract.
- [ ] UAT provides deterministic verification and triage steps using concrete artifact paths.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q`
- `rg -n "mitigation_experiment|pre_post_delta.parquet|ready_for_closeout|blocked_insufficient_signal" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md`

## Observability Impact

- Signals added/changed: handoff tests now lock `manifest.json` continuity fields (`split_context`, `baseline_anchor`), mitigation status vocabulary, and pre/post delta schema columns so drift fails loudly.
- How a future agent inspects this: run `python -m pytest tests/test_m003_mitigation_handoff_contract.py -q`, then inspect `src/modeling/README.md` and `.gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md` for canonical command and replay triage steps.
- Failure state exposed: continuity drift from S02 anchors, missing required delta columns, or undocumented status semantics now surface as deterministic pytest failures and keyword-check misses.

## Inputs

- `tests/test_m003_track_e_mitigation_experiment.py` — Runtime expectations and blocked-flow semantics from T02.
- `outputs/modeling/track_e/mitigation_experiment/manifest.json` — Canonical S03 status + continuity payload for handoff locking.
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json` — Canonical S03 diagnostics payload for replay triage.
- `src/modeling/README.md` — Existing modeling contract docs to extend with mitigation runtime.

## Expected Output

- `tests/test_m003_mitigation_handoff_contract.py` — Downstream continuity/contract regression coverage for S03 bundle.
- `src/modeling/README.md` — Canonical S03 mitigation command and diagnostics documentation.
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md` — Replayable S03 verification + triage checklist.
