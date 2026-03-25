---
estimated_steps: 4
estimated_files: 3
skills_used:
  - verification-loop
  - test
---

# T03: Lock S04 handoff continuity and canonical replay docs for S05

**Slice:** S04 — Stronger/combined comparator with materiality gate
**Milestone:** M003-rdpeu4

## Description

Close S04 with handoff-safe tests and docs so S05/M004 can consume comparator decisions, continuity payloads, and replay diagnostics without path/schema rediscovery.

## Steps

1. Add `tests/test_m003_comparator_handoff_contract.py` to lock required manifest keys, status vocabulary, continuity fields (`split_context`, `baseline_anchor`), and required `materiality_table` columns.
2. Update `src/modeling/README.md` with canonical S04 command, required inputs, output layout, and interpretation of ready/do-not-adopt vs blocked statuses.
3. Author `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md` with executable replay checks and artifact assertions for ready and blocked branches.
4. Run the full S04 comparator test stack and docs keyword checks to confirm runtime/contract/docs alignment.

## Must-Haves

- [ ] Handoff tests fail if S04 continuity payloads drift from S01/S02 baseline and split anchors.
- [ ] Modeling docs declare exactly one canonical S04 command/path/status contract.
- [ ] UAT provides deterministic replay + triage steps using concrete artifact paths.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q`
- `rg -n "stronger_comparator|materiality_table.parquet|ready_for_closeout|blocked_upstream|adopt_recommendation" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`

## Inputs

- `tests/test_m003_track_a_stronger_comparator.py` — Runtime expectations and blocked/ready semantics from T02.
- `outputs/modeling/track_a/stronger_comparator/manifest.json` — Canonical S04 status + continuity payload for handoff locking.
- `outputs/modeling/track_a/stronger_comparator/validation_report.json` — Canonical S04 diagnostics payload for replay triage.
- `src/modeling/README.md` — Existing modeling contract docs to extend with S04 comparator runtime.

## Expected Output

- `tests/test_m003_comparator_handoff_contract.py` — Downstream continuity/contract regression coverage for S04 bundle.
- `src/modeling/README.md` — Canonical S04 comparator command and diagnostics documentation.
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md` — Replayable S04 verification + triage checklist.

## Observability Impact

- **Signals changed:** Hand-off contract tests now fail on continuity drift (`split_context`, `baseline_anchor`), status vocabulary drift, and schema/redaction regressions in `materiality_table.parquet`.
- **How future agents inspect this task:** Use `tests/test_m003_comparator_handoff_contract.py`, `src/modeling/README.md`, and `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md` together to replay canonical S04 runs and interpret `ready_for_closeout` vs `blocked_upstream` outputs.
- **New failure state visibility:** Replay docs and tests localize whether failures are contract/schema drift, missing upstream continuity payloads, or blocked-upstream gate conditions in `manifest.json` / `validation_report.json`.
