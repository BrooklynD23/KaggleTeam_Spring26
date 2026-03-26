---
estimated_steps: 5
estimated_files: 8
skills_used:
  - coding-standards
  - tdd-workflow
  - test
  - best-practices
  - verification-loop
---

# T03: Compose the all-track census, repair, and checklist reporting entrypoint

**Slice:** S01 — All-track EDA artifact census and gap closure
**Milestone:** M001-4q3lxl

## Description

Implement the thin S01 reporting command that turns dispatcher contract data plus the repaired summary writers into concrete handoff artifacts. The command must inspect the live filesystem, write an honest completeness matrix, emit the canonical launcher checklist, and materialize the final Track A–E summary markdowns in the current worktree.

## Steps

1. Create a reporter entrypoint at `scripts/report_eda_completeness.py` that imports the dispatcher contract helper from T01 and reads live filesystem state rather than a copied manifest.
2. Reuse the per-track summary modules so the reporter can repair or re-emit missing final summary markdowns for Tracks A–E before writing the census artifacts.
3. Write `outputs/tables/eda_artifact_census.md` and `outputs/tables/eda_artifact_census.csv` with per-track/per-stage/per-artifact status values that distinguish `existing`, `missing`, and `repaired`.
4. Write `outputs/tables/eda_command_checklist.md` using the canonical `python scripts/run_pipeline.py --approach ...` order and an explicit note that Track D depends on `outputs/tables/track_a_s5_candidate_splits.parquet`.
5. Add focused pytest coverage for the reporting command and run the command in this stripped worktree to prove it generates the summary markdowns and census artifacts without leaking raw review text.

## Must-Haves

- [ ] The reporter imports dispatcher-derived contract data instead of duplicating expected artifact names by hand.
- [ ] One command writes the census/checklist artifacts and the five final Track A–E summary markdowns.
- [ ] The generated report is honest about the stripped worktree: missing upstream data stays marked missing even when final summary markdowns are repaired.

## Verification

- `python -m pytest tests/test_eda_artifact_census_report.py`
- `python scripts/report_eda_completeness.py && test -f outputs/tables/track_a_s8_eda_summary.md && test -f outputs/tables/track_b_s8_eda_summary.md && test -f outputs/tables/track_c_s9_eda_summary.md && test -f outputs/tables/track_d_s9_eda_summary.md && test -f outputs/tables/track_e_s9_eda_summary.md && test -f outputs/tables/eda_artifact_census.md && test -f outputs/tables/eda_artifact_census.csv && test -f outputs/tables/eda_command_checklist.md`
- `rg -n "existing|missing|repaired" outputs/tables/eda_artifact_census.md && rg -n "track_a_s5_candidate_splits.parquet|python scripts/run_pipeline.py --approach track_d" outputs/tables/eda_command_checklist.md`

## Observability Impact

- Signals added/changed: the new census matrix and checklist expose artifact presence, repair actions, and blocked dependency notes as durable repo artifacts
- How a future agent inspects this: run `python scripts/report_eda_completeness.py` and read `outputs/tables/eda_artifact_census.md`, `outputs/tables/eda_artifact_census.csv`, and `outputs/tables/eda_command_checklist.md`
- Failure state exposed: missing artifact paths, unrepaired summary outputs, and Track-D dependency blockers become explicit in generated output instead of requiring manual repo inspection

## Inputs

- `scripts/pipeline_dispatcher.py` — dispatcher-derived summary contract helper added in T01
- `scripts/run_pipeline.py` — canonical launcher command surface for the checklist
- `src/eda/track_a/summary_report.py` — Track A summary regeneration entrypoint
- `src/eda/track_b/summary_report.py` — Track B summary regeneration entrypoint
- `src/eda/track_c/summary_report.py` — Track C graceful-degradation summary entrypoint
- `src/eda/track_d/summary_report.py` — Track D summary regeneration entrypoint
- `src/eda/track_e/summary_report.py` — Track E summary + validity-scan entrypoint

## Expected Output

- `scripts/report_eda_completeness.py` — canonical S01 census/repair/checklist command
- `tests/test_eda_artifact_census_report.py` — regression coverage for the reporting command and generated statuses
- `outputs/tables/eda_artifact_census.md` — markdown completeness matrix for Tracks A–E
- `outputs/tables/eda_artifact_census.csv` — machine-readable completeness matrix for downstream slices
- `outputs/tables/eda_command_checklist.md` — verified launcher/file checklist with Track D dependency note
- `outputs/tables/track_a_s8_eda_summary.md` — repaired or verified Track A final summary
- `outputs/tables/track_b_s8_eda_summary.md` — repaired or verified Track B final summary
- `outputs/tables/track_d_s9_eda_summary.md` — repaired or verified Track D final summary
