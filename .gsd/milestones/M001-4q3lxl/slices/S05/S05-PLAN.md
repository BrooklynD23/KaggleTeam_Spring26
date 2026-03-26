# S05: Integrated local handoff verification

**Goal:** Prove in one local pass that the verified EDA outputs, export bundle, planning architecture, and trust-narrative handoff surfaces still agree, and leave the milestone with no fake-complete artifacts blocking M002 kickoff.
**Demo:** A sequential local verification run reruns the S01 reporter, reruns the S02 packager, passes the slice and milestone pytest contract suite including `tests/test_m001_handoff_verification.py`, replaces the S04 doctor placeholders with real completion artifacts, marks `R004` validated, and records the green handoff in `S05-UAT.md` and `S05-SUMMARY.md`.

## Must-Haves

- A thin milestone-level pytest harness verifies cross-surface agreement across S01, S02, S03, and S04 without inventing a second orchestration subsystem.
- The integrated handoff pass reruns `scripts/report_eda_completeness.py` before `scripts/package_eda_exports.py`, keeps the steady-state truth honest (`existing=6`, `missing=109`, `repaired=0` on rerun), and preserves Track D blocker plus Track E metadata-only validity evidence.
- The milestone handoff surface contains no doctor-created placeholder artifacts: `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` and `S04-UAT.md` must be real compressed docs.
- `R004` no longer remains stale once the S04 narrative/workflow contract and the integrated S05 pass are green.
- The slice leaves a reusable local operator artifact documenting the exact commands, outcomes, and failure-inspection points needed to hand off into M002 without rebuilding context.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python scripts/report_eda_completeness.py`
- `python scripts/package_eda_exports.py`
- `python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_eda_artifact_census_report.py tests/test_feature_plan_architecture.py tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q`
- `python - <<'PY'
from pathlib import Path
import re
requirements = Path('.gsd/REQUIREMENTS.md').read_text(encoding='utf-8')
for path in [
    Path('.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md'),
    Path('.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md'),
    Path('.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md'),
    Path('.gsd/milestones/M001-4q3lxl/slices/S05/S05-SUMMARY.md'),
]:
    text = path.read_text(encoding='utf-8')
    assert 'Recovery placeholder' not in text, path
    assert 'doctor-created placeholder' not in text, path
assert '### R004' in requirements
section = requirements.split('### R004', 1)[1].split('### ', 1)[0]
assert 'Status: validated' in section
print('handoff artifacts are real and R004 is validated')
PY`

## Observability / Diagnostics

- Runtime signals: `scripts/report_eda_completeness.py` summary counts, `scripts/package_eda_exports.py` emitted-file/figure counts, pytest pass/fail output, and the manifest fields `status_totals`, `blocked_by`, and `metadata_summaries`.
- Inspection surfaces: `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `outputs/exports/eda/tracks/track_d/manifest.json`, `outputs/exports/eda/tracks/track_e/manifest.json`, `tests/test_m001_handoff_verification.py`, `.gsd/REQUIREMENTS.md`, and `S05-UAT.md`.
- Failure visibility: the integrated harness must fail on exact drift classes — missing exported paths, broken showcase links, stale placeholder text, stale `R004` status, forbidden bundle files, or mismatched manifest facts.
- Redaction constraints: all verification and handoff docs must preserve the internal aggregate-safe boundary and must not introduce raw review text, copied `.parquet` / `.ndjson` / `.log` payloads, or public-hosting assumptions.

## Integration Closure

- Upstream surfaces consumed: `scripts/report_eda_completeness.py`, `scripts/package_eda_exports.py`, `scripts/pipeline_dispatcher.py`, `outputs/tables/track_a_s8_eda_summary.md`, `outputs/tables/track_b_s8_eda_summary.md`, `outputs/tables/track_c_s9_eda_summary.md`, `outputs/tables/track_d_s9_eda_summary.md`, `outputs/tables/track_e_s9_eda_summary.md`, `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `.gsd/feature-plans/README.md`, `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`, `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`, `.gsd/REQUIREMENTS.md`
- New wiring introduced in this slice: `tests/test_m001_handoff_verification.py` becomes the milestone-level agreement harness; S04 completion artifacts are rewritten from placeholder state into real handoff docs; `R004` is advanced to validated with integrated-proof language; `S05-UAT.md` and `S05-SUMMARY.md` become the operator-facing handoff record.
- What remains before the milestone is truly usable end-to-end: nothing.

## Tasks

- [x] **T01: Add the thin milestone handoff pytest harness** `est:45m`
  - Why: S05 needs one dedicated integration contract that composes existing S01-S04 truth surfaces and fails on cross-slice drift without duplicating every prior slice test.
  - Files: `tests/test_m001_handoff_verification.py`, `scripts/pipeline_dispatcher.py`, `outputs/tables/eda_artifact_census.csv`, `outputs/tables/eda_command_checklist.md`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`
  - Do: Create `tests/test_m001_handoff_verification.py` in the existing pytest style; assert that S01 handoff files exist and match the dispatcher contract, that the S02 root/per-track manifests point to real exported files and preserve `internal` + `aggregate-safe`, that Track D still surfaces `outputs/tables/track_a_s5_candidate_splits.parquet`, that Track E still exports metadata-only validity evidence, that showcase discovery docs still point to the S04 narrative/workflow docs, and that no forbidden `.parquet`, `.ndjson`, or copied `.log` files exist under `outputs/exports/eda/`; keep this harness focused on agreement rather than re-testing every slice in depth.
  - Verify: `python -m pytest tests/test_m001_handoff_verification.py -q`
  - Done when: `tests/test_m001_handoff_verification.py` exists, passes on the current worktree, and catches milestone-level cross-surface drift that prior slice-specific tests do not cover alone.
- [x] **T02: Repair stale S04 handoff artifacts and close requirement drift** `est:45m`
  - Why: The milestone is not honestly handoff-ready while S04 still exposes doctor placeholders and `R004` remains active despite passing S04 contract tests.
  - Files: `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T01-SUMMARY.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T02-SUMMARY.md`, `.gsd/REQUIREMENTS.md`, `tests/test_m001_handoff_verification.py`
  - Do: Rewrite the S04 summary and UAT files from the task summaries and real passing commands so they describe actual deliverables, diagnostics, and proof instead of recovery placeholders; update `R004` in `.gsd/REQUIREMENTS.md` from active to validated with concrete S04/S05 proof text; extend `tests/test_m001_handoff_verification.py` so it fails if either S04 artifact contains placeholder language or if `R004` is still active after the integrated handoff repair.
  - Verify: `python -m pytest tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q`
  - Done when: both S04 handoff docs are real, non-placeholder artifacts, `.gsd/REQUIREMENTS.md` records `R004` as validated with evidence, and the milestone harness locks those conditions.
- [x] **T03: Run the full local handoff pass and capture milestone evidence** `est:45m`
  - Why: The slice only closes when the real sequential commands and contract suite pass together and the repo contains an operator-facing record of the successful handoff into M002.
  - Files: `.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md`, `.gsd/milestones/M001-4q3lxl/slices/S05/S05-SUMMARY.md`, `tests/test_m001_handoff_verification.py`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`, `outputs/exports/eda/manifest.json`, `outputs/tables/eda_artifact_census.csv`, `.gsd/REQUIREMENTS.md`
  - Do: Run `scripts/report_eda_completeness.py` first and `scripts/package_eda_exports.py` second in sequence, then run the full pytest set named in slice verification; capture the exact commands, durations, counts, and key observed truths (`existing=6`, `missing=109`, `repaired=0`, Track D blocker path, Track E `metadata_only`, seven feature-plan lanes, S04 docs real, `R004` validated) in `S05-UAT.md`; write `S05-SUMMARY.md` as the compressed final slice handoff explaining what the integrated pass proved, what diagnostics future agents should inspect, and why M002 can start without rebuilding context.
  - Verify: `python scripts/report_eda_completeness.py && python scripts/package_eda_exports.py && python -m pytest tests/test_pipeline_dispatcher_all_tracks.py tests/test_eda_artifact_census_report.py tests/test_feature_plan_architecture.py tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q`
  - Done when: the full sequential pass is green, `S05-UAT.md` and `S05-SUMMARY.md` exist with real evidence, and a fresh agent can use those files plus the manifests to begin M002 without re-deriving milestone state.

## Files Likely Touched

- `tests/test_m001_handoff_verification.py`
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`
- `.gsd/REQUIREMENTS.md`
- `.gsd/milestones/M001-4q3lxl/slices/S05/S05-UAT.md`
- `.gsd/milestones/M001-4q3lxl/slices/S05/S05-SUMMARY.md`
