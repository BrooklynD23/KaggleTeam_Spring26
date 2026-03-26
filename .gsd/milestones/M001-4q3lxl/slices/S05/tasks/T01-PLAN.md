---
estimated_steps: 4
estimated_files: 8
skills_used:
  - coding-standards
  - test
  - verification-loop
  - debug-like-expert
---

# T01: Add the thin milestone handoff pytest harness

**Slice:** S05 — Integrated local handoff verification
**Milestone:** M001-4q3lxl

## Description

Create the dedicated milestone-level pytest harness that composes the already-established S01, S02, S03, and S04 truth surfaces. This task should add only the cross-surface agreement checks that the milestone still lacks: exported-file pointer integrity, governance markers, dispatcher-aligned summary expectations, showcase discovery continuity, and forbidden-artifact drift detection.

## Steps

1. Read the existing slice-specific regression files and the current export/planning surfaces so the new harness reuses repo conventions instead of inventing a new verification style.
2. Create `tests/test_m001_handoff_verification.py` using the existing pytest idioms from the repo, especially the contract-style assertions used in `tests/test_eda_artifact_census_report.py`, `tests/test_package_eda_exports.py`, `tests/test_feature_plan_architecture.py`, and `tests/test_trust_narrative_workflow.py`.
3. Assert milestone-level agreement only: required S01 handoff files exist and line up with `get_eda_summary_contract()`, the S02 root/per-track manifests point to real exported files and preserve `internal` + `aggregate-safe`, Track D still exposes `outputs/tables/track_a_s5_candidate_splits.parquet`, Track E still exposes metadata-only validity evidence, the showcase docs still point to the S04 narrative/workflow docs, and the export bundle contains no forbidden `.parquet`, `.ndjson`, or copied `.log` files.
4. Run the new test file and tighten any overly broad assertions until it passes cleanly and fails only on real cross-surface drift.

## Must-Haves

- [ ] `tests/test_m001_handoff_verification.py` focuses on milestone agreement and does not duplicate every assertion already covered by earlier slice tests.
- [ ] The harness reads current repo truth from dispatcher/export/planning docs rather than hardcoding a second milestone manifest.
- [ ] The test explicitly protects the Track D blocker path, Track E `metadata_only` validity evidence, and the export bundle forbidden-artifact boundary.
- [ ] `python -m pytest tests/test_m001_handoff_verification.py -q` passes at the end of the task.

## Verification

- `python -m pytest tests/test_m001_handoff_verification.py -q`
- `python - <<'PY'
from pathlib import Path
path = Path('tests/test_m001_handoff_verification.py')
text = path.read_text(encoding='utf-8')
for marker in [
    'track_a_s5_candidate_splits.parquet',
    'metadata_only',
    'aggregate-safe',
    'TRUST_NARRATIVE.md',
    'INTERN_EXPLAINER_WORKFLOW.md',
]:
    assert marker in text, marker
print('milestone handoff test contains required markers')
PY`

## Inputs

- `tests/test_pipeline_dispatcher_all_tracks.py` — existing dispatcher-contract regression style
- `tests/test_eda_artifact_census_report.py` — S01 completeness/report contract reference
- `tests/test_package_eda_exports.py` — S02 export/governance contract reference
- `tests/test_feature_plan_architecture.py` — S03 planning contract reference
- `tests/test_trust_narrative_workflow.py` — S04 narrative/workflow contract reference
- `scripts/pipeline_dispatcher.py` — source of truth for EDA summary contract metadata
- `outputs/tables/eda_artifact_census.csv` — current S01 census truth
- `outputs/tables/eda_command_checklist.md` — current S01 command checklist
- `outputs/exports/eda/manifest.json` — current S02 root manifest truth
- `outputs/exports/eda/EXPORT_CONTRACT.md` — current S02 governance contract
- `outputs/exports/eda/tracks/track_d/manifest.json` — Track D blocker metadata
- `outputs/exports/eda/tracks/track_e/manifest.json` — Track E validity metadata
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md` — showcase discovery surface
- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` — S04 narrative target
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` — S04 workflow target

## Expected Output

- `tests/test_m001_handoff_verification.py` — dedicated milestone-level pytest harness for cross-surface agreement

## Observability Impact

- Signals changed: milestone-level drift now becomes directly visible in one pytest surface instead of being inferred across separate S01-S04 test files.
- How to inspect later: run `python -m pytest tests/test_m001_handoff_verification.py -q` and inspect the underlying truth surfaces it composes — `scripts/pipeline_dispatcher.py`, `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, and the showcase-system docs.
- Failure states made visible: missing exported-file targets, lost `internal` / `aggregate-safe` governance markers, missing Track D blocker evidence, missing Track E `metadata_only` validity evidence, broken showcase links to S04 docs, and forbidden `.parquet`, `.ndjson`, or copied `.log` files inside the export bundle.
