# S03 — Research

**Date:** 2026-03-23

## Summary

S03 is the **R009 closure slice**: S01+S02 already prove intake + model-aware fairness runtime, but mitigation pre/post fairness-vs-accuracy evidence is still missing. There is currently no S03 runtime, no S03 contract module, and no S03 tests.

Most important surprise for planning: the currently committed S02 replay artifacts are valid but **empty for subgroup/disparity rows** (`row_counts.subgroup_rows=0`, `disparity_rows=0`) because this worktree has tiny fixture intake (3 rows), `min_group_size=10`, and no `data/curated/business.parquet` (runtime uses synthetic unknown context). If S03 does not explicitly gate/diagnose this condition, mitigation claims can become theater.

## Requirement targeting (Active requirements)

- **R009 (active)** — S03 is the remaining closure owner for mitigation evidence:
  - must execute one mitigation lever,
  - must emit authoritative pre/post fairness + accuracy deltas,
  - must include threshold pass/fail outcomes.
- **R012 (active, continuity support)** — S03 must preserve handoff continuity for M004/S05 via machine-readable artifacts and reproducible command surface.
- **R010 (active, supporting only)** — S03 should preserve fairness context quality for S04 adoption gating (no metric-only story).

## Skill-informed implementation rules used

- From **tdd-workflow**: **“Tests BEFORE Code”** and include edge/error-path coverage, not just happy path.
- From **verification-loop**: close with explicit verification gates (tests + runtime replay + artifact assertions), not narrative completion.

## Key findings (codebase reality)

### 1) S03 runtime surface does not exist yet

No `src/modeling/track_e/*` mitigation module exists beyond S02 fairness audit.

Current modeling tree:
- `src/modeling/track_a/audit_intake.py` (S01)
- `src/modeling/track_e/fairness_audit.py` (S02)
- no mitigation runtime or mitigation contract module.

### 2) S02 artifacts are canonical and must be consumed as-is

Authoritative input bundle for S03 is fixed by S02:
- `outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet`
- `outputs/modeling/track_e/fairness_audit/disparity_summary.parquet`
- `outputs/modeling/track_e/fairness_audit/manifest.json`
- `outputs/modeling/track_e/fairness_audit/validation_report.json`

S03 should gate on:
- `manifest.status == "ready_for_mitigation"`
- `validation_report.status == "pass"`
- strict continuity echoes (`split_context`, `baseline_anchor`) per D030-style handoff discipline.

### 3) Current replay data cannot support meaningful mitigation deltas without explicit handling

Observed in current worktree outputs:
- S01 intake row_count: 3
- S02 subgroup/disparity rows: 0
- `data/curated/business.parquet`: missing

Implication: S03 needs an explicit “insufficient subgroup signal” branch (blocked status + reason) or mitigation results will be numerically vacuous.

### 4) Existing EDA mitigation code is narrative-only (not executable tradeoff)

`src/eda/track_e/mitigation_candidates.py` writes markdown recommendations only; it does not run a mitigation experiment or compute pre/post deltas on model predictions.

### 5) Guardrails are already reusable and should stay centralized

- No raw text / no demographic-inference output enforcement is already in `src/eda/track_e/common.write_parquet`.
- Intake/fairness contract patterns with fail-closed manifest + validation JSON are already established in S01/S02 and should be mirrored for S03.

## Recommendation

Implement S03 as a **new modeling runtime + contract bundle**, separate from EDA:

- CLI: `python -m src.modeling.track_e.mitigation_experiment`
- Inputs:
  - `--config configs/track_e.yaml`
  - `--intake-dir outputs/modeling/track_a/audit_intake`
  - `--fairness-dir outputs/modeling/track_e/fairness_audit`
  - `--output-dir outputs/modeling/track_e/mitigation_experiment`
- Canonical outputs:
  - `pre_post_delta.parquet` (authoritative pre/post fairness+accuracy delta table)
  - `manifest.json`
  - `validation_report.json`

Recommended first mitigation lever (bounded + executable):
- **Group-wise residual correction** (post-hoc additive shift), fit on non-test splits and evaluated on test split.
- Clamp mitigated predictions to valid star range (e.g., `[1, 5]`).
- Compute both fairness disparity deltas and overall accuracy deltas.

Why this lever first:
- Requires no new model-training pipeline.
- Uses existing intake schema (`split_name`, `y_true`, `y_pred`) and subgroup mapping utilities.
- Produces explicit fairness-vs-accuracy tradeoff evidence.

## Implementation landscape

### Existing files to reuse

- `src/modeling/track_e/fairness_audit.py`
  - intake gating + fail-closed diagnostics structure.
- `src/modeling/common/fairness_audit_contract.py`
  - parity/threshold contract style to mirror for mitigation outputs.
- `src/eda/track_e/subgroup_definition.py`
  - subgroup derivation logic.
- `src/eda/track_e/common.py`
  - path resolution + safe parquet writer guardrails.
- `tests/test_m003_track_e_fairness_audit.py`
  - integration-test style template for runtime + blocked-upstream checks.
- `tests/test_m003_fairness_audit_handoff_contract.py`
  - continuity/handoff test style template.

### New files likely needed

- `src/modeling/common/mitigation_contract.py`
- `src/modeling/track_e/mitigation_experiment.py`
- Update exports in `src/modeling/common/__init__.py`
- Update exports in `src/modeling/track_e/__init__.py`
- `tests/test_m003_mitigation_contract.py`
- `tests/test_m003_track_e_mitigation_experiment.py`
- `tests/test_m003_mitigation_handoff_contract.py`
- `src/modeling/README.md` (S03 section)
- `.gsd/milestones/M003-rdpeu4/slices/S03/S03-UAT.md`

### Natural seams for planner decomposition

1. **Contract seam**
   - Define required `pre_post_delta` columns + status vocabulary + validators.
2. **Runtime seam**
   - Intake/fairness gating, mitigation transform, delta computation, artifact writing.
3. **Handoff/docs seam**
   - Continuity tests, README command contract, UAT replay.

## Build/prove-first order

1. Add failing tests for contract schema and blocked diagnostics (including “no subgroup comparisons” case).
2. Implement mitigation contract module.
3. Implement mitigation runtime with fail-closed semantics.
4. Add handoff continuity tests (`baseline_anchor`/`split_context` equality from S02->S03).
5. Run canonical verification sequence and regenerate bundle artifacts.

## Verification plan (authoritative)

1. Contract + runtime + handoff tests:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py -q`
2. Runtime replay:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`
3. Artifact assertion snippet should verify:
   - required files exist,
   - `manifest.status` ready-state,
   - `validation_report.status == pass`,
   - required delta columns present,
   - threshold pass/fail fields present,
   - forbidden raw-text/demographic columns absent.
4. Blocked-path tests:
   - missing/invalid S02 bundle,
   - insufficient subgroup comparisons (current fixture-like condition),
   - invalid intake/fairness status values.

## Key fragility to lock in tests

- Exact continuity of `baseline_anchor` and `split_context` from S02 outputs (not key-presence only).
- Deterministic behavior when S02 has 0 subgroup/disparity rows.
- Avoid using test/eval rows to *fit* mitigation parameters (leakage-risk in mitigation theater).

## Skill Discovery (suggest)

Installed and directly relevant now:
- `tdd-workflow`
- `verification-loop`
- `test`

Not installed but potentially relevant to S03 core tech:
- Scikit-learn (highest install result):
  - `npx skills add davila7/claude-code-templates@scikit-learn`
- Pandas-heavy workflow support:
  - `npx skills add jeffallan/claude-skills@pandas-pro`

Fairness-specific search result:
- `npx skills find "fairlearn"` returned no skill.
- Generic fairness skill exists but low-install niche:
  - `npx skills add jeremylongshore/claude-code-plugins-plus-skills@validating-ai-ethics-and-fairness`

(No skills were installed during this research.)
