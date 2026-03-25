# S04 — Research

**Date:** 2026-03-23

## Summary

S04 is a **targeted but integration-sensitive** slice: it must deliver R010’s stronger/combined model comparator with a materiality gate, while consuming S01/S02 contract surfaces exactly and avoiding model-zoo sprawl.

Current worktree truth:
- S01 intake contract exists and is healthy at `outputs/modeling/track_a/audit_intake/` (`status=ready_for_fairness_audit`, validated baseline anchor present).
- S02 fairness bundle exists and is healthy at `outputs/modeling/track_e/fairness_audit/` (`status=ready_for_mitigation`), but currently has **0 subgroup/disparity rows**.
- S03 mitigation bundle exists and is currently `blocked_insufficient_signal` (diagnostic-only, as designed).
- There is **no S04 comparator runtime/contract/test surface yet**.

Most important planning surprise: this repo now has S01/S02/S03 modeling infrastructure, but **no stronger-model producer runtime is present in this worktree** (only `track_a/audit_intake.py` and Track E fairness/mitigation). S04 should therefore be comparator/gate logic over canonical artifacts, not a new broad training subsystem.

## Requirement targeting (Active requirements)

- **R010 (active, primary owner in S04)**
  - Must emit a decision-ready comparator artifact with baseline metric, stronger/combined metric, delta, runtime cost, and adopt/do-not-adopt decision via explicit materiality gate.
- **R012 (active, supporting)**
  - Must keep canonical command/path/schema/status continuity so S05/M004 can consume without reconstruction.
- **R022 (deferred, supporting evidence only)**
  - S04 should produce runtime-cost fields that S05 can use for `local_sufficient` vs `overflow_required`; do not build HPC paths here.
- **R009 (supporting context only)**
  - S04 must consume fairness context (S02 artifacts) so adoption is not metric-only.

## Skill-informed implementation rules (applied)

- From **tdd-workflow**: **“Tests BEFORE Code”** and explicit edge/error-path coverage.
- From **verification-loop**: use explicit verification gates (targeted tests + runtime replay + artifact assertions), not narrative completion.
- From `tests/CLAUDE.md`: keep this as contract/regression testing; do not depend on full pipeline retraining and do not write to `data/curated/`.

## Key findings (codebase reality)

### 1) S04 implementation surfaces are currently missing

No comparator contract/runtime/tests/docs exist yet for S04.

Missing expected surfaces:
- `src/modeling/common/*comparator*_contract.py` (none)
- `src/modeling/track_a/*comparator*.py` (none)
- `tests/test_m003_*comparator*.py` (none)
- S04 slice docs (`S04-PLAN.md`, `S04-UAT.md`, `S04-SUMMARY.md`) not present yet

### 2) S01 provides the exact baseline anchor S04 needs

`outputs/modeling/track_a/audit_intake/manifest.json` already contains:
- `baseline_anchor.metric_values` (currently `rmse`, `mae`)
- `baseline_anchor.runtime_seconds`
- `baseline_anchor.model_name`
- `split_context` continuity payload

This is the canonical baseline side of the comparator and should be consumed directly (no ad hoc baseline rediscovery).

### 3) S02 fairness context is available but currently low-signal

`outputs/modeling/track_e/fairness_audit/manifest.json` currently reports:
- `status=ready_for_mitigation`
- `row_counts.disparity_rows=0`
- `threshold_checks.metric_thresholds` present

This means S04 can consume fairness metadata, but should explicitly handle **no-disparity-signal** as a gate reason (do-not-adopt or blocked decision rationale), not silently ignore fairness context.

### 4) Existing S01–S03 contract pattern is strong and reusable

Established pattern across `audit_intake.py`, `fairness_audit.py`, and `mitigation_experiment.py`:
- deterministic bundle roots under `outputs/modeling/...`
- canonical `manifest.json` + `validation_report.json`
- explicit status vocabularies
- phase timeline + check-level diagnostics
- exact `split_context`/`baseline_anchor` continuity checks in handoff tests

S04 should mirror this instead of inventing a new style.

### 5) Orchestration is still EDA-oriented

`scripts/pipeline_dispatcher.py` still wires EDA approaches only. M003 slices have correctly used explicit modeling CLI modules; S04 should do the same and avoid dispatcher churn.

### 6) Real stronger-model generation is not in this worktree

Despite M002 summary claims, this worktree does not currently expose Track A/B/C/D baseline training modules under `src/modeling/track_*/baseline.py`. Available modeling runtime surface is intake/fairness/mitigation only.

Implication: S04 should be **model-agnostic comparator intake + gate** over candidate metric artifacts, not “train a model zoo.”

## Recommendation

Implement S04 as a **new comparator contract + runtime bundle** that consumes:
- S01 intake bundle (baseline anchor)
- S02 fairness bundle (context/gate signals)
- one candidate stronger/combined metrics artifact (`metrics.csv`-style)

Recommended runtime surface:
- CLI: `python -m src.modeling.track_a.stronger_comparator`
- Inputs:
  - `--config configs/track_a.yaml`
  - `--intake-dir outputs/modeling/track_a/audit_intake`
  - `--fairness-dir outputs/modeling/track_e/fairness_audit`
  - `--candidate-metrics <path-to-candidate-metrics.csv>`
  - `--output-dir outputs/modeling/track_a/stronger_comparator`
- Outputs:
  - `materiality_table.parquet`
  - `manifest.json`
  - `validation_report.json`

Recommended decision logic (explicit and test-locked):
- `metric_gain = baseline_metric - candidate_metric` for minimize metrics (e.g., RMSE/MAE)
- `material_improvement = metric_gain >= min_metric_gain`
- `runtime_ok = candidate_runtime_seconds <= baseline_runtime_seconds * max_runtime_multiplier`
- `fairness_context_ok = fairness_manifest.status == ready_for_mitigation`
- `fairness_signal_available = disparity_rows > 0`
- `adopt = material_improvement AND runtime_ok AND fairness_context_ok AND fairness_signal_available`

If fairness signal is missing (current repo reality), runtime should still produce a valid comparator decision artifact with `adopt=false` and machine-readable reason (avoid silent metric-only adoption).

## Implementation landscape

### Files to reuse directly

- `src/modeling/track_a/audit_intake.py` — baseline anchor intake pattern + phased diagnostics
- `src/modeling/track_e/fairness_audit.py` — fairness bundle gating + diagnostics structure
- `src/modeling/common/audit_intake_contract.py` — intake schema gate
- `src/modeling/common/fairness_audit_contract.py` — fairness status/schema gate
- `src/modeling/common/__init__.py` — export pattern for shared contracts
- `src/modeling/README.md` — canonical command/path contract documentation style
- Existing M003 tests (`test_m003_*_handoff_contract.py`) — continuity and redaction test style

### New files likely needed

- `src/modeling/common/comparator_contract.py` (name can vary, but keep parallel to existing contracts)
- `src/modeling/track_a/stronger_comparator.py`
- `tests/test_m003_comparator_contract.py`
- `tests/test_m003_track_a_stronger_comparator.py`
- `tests/test_m003_comparator_handoff_contract.py`
- `src/modeling/README.md` (add S04 section)
- `.gsd/milestones/M003-rdpeu4/slices/S04/S04-UAT.md`

### Natural seams for planner decomposition

1. **Contract seam**
   - Define required materiality table columns, boolean fields, and manifest status vocabulary.
2. **Runtime seam**
   - Implement upstream gating + comparator math + decision reasons + bundle writing.
3. **Handoff/docs seam**
   - Continuity tests (`split_context`, `baseline_anchor`), README/UAT, canonical replay command.

## Proposed S04 contract shape (planner-facing)

### Manifest status vocabulary (recommended)

- `ready_for_closeout`
- `blocked_upstream`

`ready_for_closeout` should be used for both adopt and do-not-adopt outcomes; adoption lives in decision fields, not status.

### Required `materiality_table.parquet` columns (recommended minimum)

- `baseline_model_name`
- `candidate_model_name`
- `metric_name`
- `baseline_metric_value`
- `candidate_metric_value`
- `metric_gain`
- `min_metric_gain`
- `material_improvement` (bool)
- `baseline_runtime_seconds`
- `candidate_runtime_seconds`
- `runtime_delta_seconds`
- `max_runtime_multiplier`
- `runtime_within_budget` (bool)
- `fairness_context_ready` (bool)
- `fairness_signal_available` (bool)
- `fairness_exceeds_threshold_count`
- `adopt_recommendation` (bool)
- `decision_reason`

### Required continuity fields in manifest/validation

- exact `split_context` echo from S01/S02
- exact `baseline_anchor` echo from S01/S02
- explicit `upstream_paths` for intake/fairness/candidate metrics

## Build/prove-first order

1. Add failing contract tests (schema + status vocabulary + boolean-field validation).
2. Add failing runtime tests (ready path, blocked-upstream path, no-fairness-signal do-not-adopt path).
3. Implement comparator contract module and exports.
4. Implement runtime CLI and deterministic diagnostics bundle.
5. Add handoff contract tests for continuity + redaction.
6. Update modeling README and write S04 UAT replay docs.

## Verification plan (authoritative)

Use repo interpreter path:
`/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`

1. Targeted tests:
   - `.../.venv-local/bin/python -m pytest tests/test_m003_comparator_contract.py tests/test_m003_track_a_stronger_comparator.py tests/test_m003_comparator_handoff_contract.py -q`

2. Runtime replay (real worktree artifacts + candidate metrics path):
   - `.../.venv-local/bin/python -m src.modeling.track_a.stronger_comparator --config configs/track_a.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --candidate-metrics <candidate_metrics.csv> --output-dir outputs/modeling/track_a/stronger_comparator`

3. Artifact assertion snippet should verify:
   - required files exist
   - manifest status vocabulary valid
   - validation status/phase consistent
   - required comparator columns exist
   - boolean columns are true booleans
   - no raw-text/demographic columns in output table

4. Blocked-path regression:
   - missing candidate metrics
   - non-ready intake/fairness manifest
   - malformed candidate metrics schema

## Key fragility to lock in tests

- **Continuity drift:** `split_context`/`baseline_anchor` equality must be exact, not key-presence only.
- **Low-signal fairness context:** current S02 artifacts can be ready but `disparity_rows=0`; comparator must produce explicit do-not-adopt rationale.
- **Status/decision confusion:** avoid treating do-not-adopt as blocked-upstream; blocked should mean broken inputs/contracts.
- **Exit-code semantics:** follow S03 pattern where machine-readable artifact status is source of truth.

## Skill Discovery (suggest)

Installed and directly relevant:
- `tdd-workflow`
- `verification-loop`
- `test`

Not installed but relevant to S04 core tech:
- Scikit-learn (highest installs):
  - `npx skills add davila7/claude-code-templates@scikit-learn`
- Pandas:
  - `npx skills add jeffallan/claude-skills@pandas-pro`
- XGBoost/LightGBM (if S04 candidate source expands):
  - `npx skills add tondevrel/scientific-agent-skills@xgboost-lightgbm`

Search note:
- `npx skills find "fairlearn"` returned no results.

(No skills were installed during this research.)
