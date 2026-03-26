---
estimated_steps: 4
estimated_files: 8
skills_used:
  - verification-loop
  - test
  - article-writing
  - coding-standards
---

# T03: Run the full local handoff pass and capture milestone evidence

**Slice:** S05 — Integrated local handoff verification
**Milestone:** M001-4q3lxl

## Description

Execute the real integrated handoff sequence in the required order, verify that the milestone surfaces agree after regeneration, and leave behind the operator-facing evidence docs that make the handoff into M002 reusable for a fresh agent.

## Steps

1. Run `python scripts/report_eda_completeness.py` first and confirm the steady-state result stays honest (`existing=6`, `missing=109`, `repaired=0` on rerun) while rewriting the S01 census/checklist outputs.
2. Run `python scripts/package_eda_exports.py` second, not concurrently with any other packager invocation, and confirm the rebuilt export bundle still reports the expected counts, governance markers, Track D blocker path, and Track E metadata-only validity evidence.
3. Run the integrated pytest sequence named in `S05-PLAN.md`, including `tests/test_m001_handoff_verification.py`, and investigate/fix any last-mile drift until the suite is green.
4. Write `.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md` and `.gsd/milestones/M001-4q3lxl/slices/S05/S05-SUMMARY.md` with the exact commands, observed values, key diagnostics, and clear explanation of why M002 can begin without re-deriving milestone state.

## Must-Haves

- [ ] The reporter runs before the packager, and the packager is not run concurrently with any other bundle build.
- [ ] The integrated pass records the current honest truth: `existing=6`, `missing=109`, `repaired=0`, Track D blocker at `outputs/tables/track_a_s5_candidate_splits.parquet`, Track E validity evidence exported as metadata only, and the seven-lane feature-plan architecture still present.
- [ ] `S05-UAT.md` records the exact commands and outcomes a future agent should rerun.
- [ ] `S05-SUMMARY.md` explains the integrated proof, diagnostics, residual none/closure state, and why M002 can start.

## Verification

- `python scripts/report_eda_completeness.py && python scripts/package_eda_exports.py && python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_eda_artifact_census_report.py tests/test_feature_plan_architecture.py tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q`
- `python - <<'PY'
from pathlib import Path
for path in [
    Path('.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md'),
    Path('.gsd/milestones/M001-4q3lxl/slices/S05/S05-SUMMARY.md'),
]:
    assert path.exists() and path.stat().st_size > 0, path
text = Path('.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md').read_text(encoding='utf-8')
for marker in ['existing=6', 'missing=109', 'repaired=0', 'track_a_s5_candidate_splits.parquet', 'metadata_only']:
    assert marker in text, marker
print('S05 handoff artifacts exist and capture the expected evidence markers')
PY`

## Observability Impact

- Signals added/changed: `S05-UAT.md` becomes the human-readable run log for the integrated pass, while `S05-SUMMARY.md` becomes the compressed diagnostic handoff for future milestone work.
- How a future agent inspects this: rerun the commands in `S05-UAT.md`, then inspect `outputs/tables/eda_artifact_census.csv`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/tracks/track_d/manifest.json`, `outputs/exports/eda/tracks/track_e/manifest.json`, and `tests/test_m001_handoff_verification.py`.
- Failure state exposed: the handoff docs must name which command failed, which count or marker drifted, and where to inspect the exact broken surface.

## Inputs

- `scripts/report_eda_completeness.py` — canonical S01 regeneration/verification command
- `scripts/package_eda_exports.py` — canonical S02 regeneration/verification command
- `tests/test_pipeline_dispatcher_all_tracks.py` — S01 dispatcher/summaries regression surface
- `tests/test_eda_artifact_census_report.py` — S01 census/checklist regression surface
- `tests/test_feature_plan_architecture.py` — S03 planning regression surface
- `tests/test_trust_narrative_workflow.py` — S04 narrative/workflow regression surface
- `tests/test_m001_handoff_verification.py` — S05 milestone agreement harness
- `outputs/exports/eda/manifest.json` — post-packager root manifest truth
- `outputs/tables/eda_artifact_census.csv` — post-reporter census truth
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` — repaired S04 handoff surface
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md` — repaired S04 handoff surface
- `.gsd/REQUIREMENTS.md` — requirement state truth after T02

## Expected Output

- `.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md` — integrated handoff runbook and evidence log
- `.gsd/milestones/M001-4q3lxl/slices/S05/S05-SUMMARY.md` — compressed final slice summary for M002 handoff
