# S02 — Research

**Date:** 2026-03-23

## Summary

S02 is a **high-risk integration slice**: it must convert S01’s upstream scored-intake bundle into a real, model-aware fairness audit surface (per-subgroup fairness + disparity + support + accuracy context) and keep failure visibility as explicit as S01.

Primary requirement targeting:
- **Owns the first executable closure block for R009** (model-bound fairness audit on real predictions; mitigation remains S03).
- **Supports R012** by producing machine-readable, report-ready accountability evidence.
- **Supports R010/S04 indirectly** by providing fairness context that later gates stronger-model adoption decisions.

Current worktree truth:
- S01 intake contract is present and valid at `outputs/modeling/track_a/audit_intake/` with `manifest.status=ready_for_fairness_audit` and `validation.status=pass`.
- Existing Track E runtime (`src/eda/track_e/*`) is still **EDA/data-level disparity**, not prediction-level fairness audit.
- There is no modeling fairness runtime yet (`src/modeling/track_e/` does not exist).

## Skill-informed implementation rules (applied)

- From **tdd-workflow**: “**Tests BEFORE Code**.” S02 should start by adding failing contract/integration tests for fairness audit bundle shape and failure diagnostics before runtime implementation.
- From **verification-loop**: use explicit phase gates (tests + runtime command + diagnostics assertions), not narrative-only completion.

## Recommendation

Implement S02 as a **new modeling fairness-audit bundle** (parallel to S01’s intake bundle pattern), not as edits inside EDA Stage 7.

Recommended runtime surface:
- CLI module: `python -m src.modeling.track_e.fairness_audit`
- Canonical output root: `outputs/modeling/track_e/fairness_audit/`
- Canonical bundle files:
  - `subgroup_metrics.parquet` (per subgroup support + fairness + accuracy-context columns)
  - `disparity_summary.parquet` (reference comparisons + signed deltas + threshold flags)
  - `manifest.json` (readiness/status metadata)
  - `validation_report.json` (check-level diagnostics + phase timeline)

Why this path:
- Preserves S01’s established contract style (`ready_*` / `blocked_*`, deterministic JSON diagnostics).
- Avoids conflating EDA descriptive artifacts with model-evaluation accountability artifacts.
- Gives S03 a clean pre-mitigation baseline artifact to diff against.

## Implementation Landscape

### Files that exist and are directly reusable

- `src/modeling/track_a/audit_intake.py`
  - S01 runtime pattern for phased diagnostics, canonical bundle writing, and fail-closed behavior.
- `src/modeling/common/audit_intake_contract.py`
  - Existing contract validator for scored intake; should be reused as an input guard in S02.
- `src/eda/track_e/subgroup_definition.py`
  - Reusable subgroup derivation logic (`build_subgroup_definitions`) from `business` + review counts.
- `src/eda/track_e/common.py`
  - Guardrails and helpers (`write_parquet`, banned/demographic column blocking, min-group helper).
- `configs/track_e.yaml`
  - Existing fairness thresholds and `subgroups.min_group_size` defaults.

### Files/surfaces currently missing (S02 delivery target)

- `src/modeling/track_e/` package (new).
- S02-specific fairness contract helper under `src/modeling/common/` (new recommended).
- S02-specific pytest suite in `tests/` (new).
- S02 UAT + summary docs under `.gsd/milestones/M003-rdpeu4/slices/S02/` (new).

### Natural seams for planner decomposition

1. **Contract seam (first):** define fairness-audit output schema + validation checks.
2. **Runtime seam:** build CLI that consumes S01 intake + subgroup context and emits bundle.
3. **Failure-visibility seam:** explicit blocked states for missing/bad intake or missing join context.
4. **Handoff seam:** tests + README/UAT updates to lock canonical path and required fields.

### Build/prove-first order

1. Write failing tests for fairness bundle contract and diagnostics behavior.
2. Implement contract helper + runtime module.
3. Run targeted pytest suite.
4. Run one CLI regeneration command and assert manifest/validation + output schema.

## Proposed S02 contract shape (for planner)

### Upstream gates (must pass)

- Intake bundle exists at provided path.
- `manifest.json` has `status == ready_for_fairness_audit`.
- `validation_report.json` has `status == pass`.
- `scored_intake.parquet` validates against `validate_audit_intake_dataframe(...)`.

### Core output expectations

`subgroup_metrics.parquet` (aggregate-only) should include at least:
- `subgroup_type`, `subgroup_value`
- `support_count`
- prediction fairness context (e.g., `mean_y_pred`, `mean_y_true`, `mean_signed_error`)
- paired accuracy context (e.g., `mae`, `rmse` or `within_1_star_rate`)
- optional split/model columns for traceability (`split_name`, `model_name`)

`disparity_summary.parquet` should include at least:
- `subgroup_type`, `metric_name`
- `reference_group`, `comparison_group`
- `reference_value`, `comparison_value`
- `delta`, optional `ratio`
- `exceeds_threshold` (boolean)
- support context columns used for interpretability

`manifest.json` should include at least:
- status (`ready_for_mitigation` recommended) or `blocked_upstream`
- phase, row counts, split context
- baseline anchor echo from S01 for downstream continuity
- bundle file map + upstream path echoes

`validation_report.json` should include at least:
- check-level statuses
- explicit phase timeline
- blocking reason + missing inputs when failed

## Constraints

- Keep **aggregate-only** fairness artifacts (no row-level scored dumps in S02 outputs).
- Preserve no-raw-text and no-demographic-inference guardrails via existing helpers/policies.
- Keep commands config/path driven; no hardcoded absolute paths.
- Do not expand dispatcher/orchestration in S02 unless required for verification; explicit CLI is enough.
- Be explicit about evaluation split policy (defaulting to `test` is safer; if not, document why).

## Common pitfalls

- Reusing `src/eda/track_e/fairness_baseline.py` directly and calling it “model-aware” (it is currently data-level disparity).
- Skipping readiness checks and reading `scored_intake.parquet` directly without manifest/validation gates.
- Emitting fairness gaps without paired accuracy context (fails S02 acceptance intent).
- Using tiny local fixture intake (3 rows) as if it were substantive fairness evidence.
- Silent failure behavior (must emit machine-readable blocked diagnostics, like S01).

## Verification approach (authoritative sequence)

Use repo interpreter (current known-good path in this worktree):

1. Targeted tests:
   - `.../.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q`
2. Runtime command:
   - `.../.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
3. Artifact assertions (python snippet):
   - required files exist
   - `manifest.status` is ready-state (not blocked)
   - `validation.status == pass`
   - required columns exist in both parquet outputs
4. Failure-path regression:
   - missing intake path or non-ready intake manifest should produce `blocked_upstream` + phase-local reason in JSON diagnostics.

## Skill Discovery (suggest)

Installed and directly relevant skills already available:
- `tdd-workflow`
- `verification-loop`
- `test`

Potential external skills for S02 technologies (not installed):
- scikit-learn: `npx skills add davila7/claude-code-templates@scikit-learn`
- pandas: `npx skills add jeffallan/claude-skills@pandas-pro`
- duckdb: `npx skills add silvainfm/claude-skills@duckdb`

Search result notes:
- `npx skills find "fairlearn"` returned no results.
- No installation performed in this slice.
