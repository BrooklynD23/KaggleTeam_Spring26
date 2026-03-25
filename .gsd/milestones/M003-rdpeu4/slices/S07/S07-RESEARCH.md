# S07 — Research

**Date:** 2026-03-23

## Summary

S07 is a **high-risk integration remediation** slice: everything needed for closeout exists, but canonical replay is still blocked because S03 cannot produce non-empty mitigation deltas on the tiny real replay surface.

Current canonical truth in this worktree:
- `outputs/modeling/track_e/fairness_audit/manifest.json` is now healthy after S06 (`status=ready_for_mitigation`, `signal_sufficiency.outcome=fallback_sufficient`, `disparity_rows=8`).
- `outputs/modeling/track_e/mitigation_experiment/manifest.json` is still blocked (`status=blocked_insufficient_signal`, reason currently `no_correction_groups`).
- Lowering mitigation support floor alone is not sufficient: with `min_group_size=1` replay shifts to `no_comparison_rows_after_alignment` (still blocked).
- `python -m src.modeling.m003_closeout_gate ... --output-dir outputs/modeling/m003_closeout_tmp` now blocks **only** on S03 (`readiness_block_stage_ids=["s03_mitigation"]`), with `compute_escalation_decision=local_sufficient`.

So the real S07 problem is not S05 orchestration anymore; it is **S03 sparse-ready-path semantics on tiny test support**.

## Requirement targeting (active)

- **R009 (primary):** must land a real, non-empty authoritative mitigation pre/post delta artifact (`ready_for_closeout`) on canonical replay.
- **R010 (supporting):** preserve comparator continuity and fair context interpretation when S05 is rerun to handoff-ready.
- **R012 (supporting):** preserve machine-readable continuity (`baseline_anchor`, `split_context`, status vocab) through mitigation + closeout rerun for M004 consumers.
- **R022 (supporting via S05 rerun):** keep escalation decision evidence-based (`local_sufficient` unless runtime-capacity signals emerge).

## Skill-informed implementation rules (applied)

- From **test** skill (critical rules):
  - **MATCH EXISTING PATTERNS** (extend current pytest style and fixture patterns in `tests/test_m003_*`).
  - **READ BEFORE WRITING** (existing mitigation/handoff/closeout tests already encode status/continuity contracts).
  - **VERIFY GENERATED TESTS** (run targeted suites + canonical replay, not just unit-only confidence).
- From **verification-loop** skill:
  - Keep explicit verification phases and treat final readiness as evidence from artifacts/tests, not narrative.

## Key findings (codebase reality)

### 1) S06 solved fairness sufficiency; S03 is now the single hard readiness blocker

Observed after reruns:
- Fairness bundle:
  - `status=ready_for_mitigation`
  - `signal_sufficiency.outcome=fallback_sufficient`
  - `row_counts.primary_disparity_rows=0` but `row_counts.disparity_rows=8` via fallback strategy `split_name_metrics`.
- Closeout bundle (`outputs/modeling/m003_closeout_tmp/manifest.json`):
  - `status=blocked_upstream`
  - `readiness_block_stage_ids=["s03_mitigation"]`
  - comparator no longer contributes readiness reasons.

Implication: S07 can stay tightly scoped to mitigation readiness semantics + rerun/packaging.

### 2) There is a structural mismatch between S06 fallback subgroup signal and S03 mitigation evaluation assumptions

- S06 fallback strategy yields disparities on `subgroup_type=split_name`.
- S03 correction fitting currently targets fixed subgroup columns: `city`, `primary_category`, `price_tier`, `review_volume_tier`.
- Canonical replay uses 3 intake rows (train/validation/test = 1 each), so test-only evaluation has one group instance and cannot satisfy pairwise comparison alignment for fallback disparities.

This is why mitigation remains blocked even when fairness is ready.

### 3) Lowering support thresholds alone does not close S07

I validated with a temporary config override (`subgroups.min_group_size=1`):
- S03 no longer fails at `no_correction_groups`.
- It still fails with `no_comparison_rows_after_alignment`.

So S07 needs **tiny-test support path logic**, not only threshold tuning.

### 4) Closeout/comparator paths are already in shape once S03 becomes ready

With current fairness artifacts, comparator replay resolves fairness signal and remains `ready_for_closeout`.
S05 closeout logic already supports ready/blocked and escalation vocab correctly; once S03 flips to `ready_for_closeout`, S05 should be able to emit `ready_for_handoff` without contract redesign.

### 5) Most relevant files are concentrated and already modularized

- Core runtime seam: `src/modeling/track_e/mitigation_experiment.py`
- Existing contracts likely reusable as-is (status vocabulary does not need expansion):
  - `src/modeling/common/mitigation_contract.py`
  - `src/modeling/common/closeout_contract.py`
- Integration surfaces already stable:
  - `src/modeling/m003_closeout_gate.py`
  - `src/modeling/track_a/stronger_comparator.py`

## Recommendation

Use a **targeted S03 sparse-ready-path enhancement** (not data rehydration first, not broad orchestrator rewrite).

### Recommended behavior changes (S03)

1. Preserve existing status vocabulary and blocked semantics.
2. Add sparse-support mitigation fallback behavior for canonical tiny replay:
   - Keep fit on non-test rows.
   - Keep correction application semantics explicit.
   - Add bounded evaluation fallback when test-only alignment cannot produce comparison rows.
3. Emit deterministic diagnostics in `lever_metadata` / `insufficient_signal` so downstream can tell whether primary test-only or fallback evaluation path was used.

### Why this is preferable for S07

- Directly targets the validated failure mode (`no_comparison_rows_after_alignment`).
- Preserves S03/S05/S04 contract continuity and avoids introducing new status strings.
- Avoids rehydrating larger upstream datasets just to satisfy local replay mechanics.

### Alternate path (not recommended first)

Rehydrate canonical replay inputs (`predictions_test.parquet`, `review_fact.parquet`, `business.parquet`) to provide richer test subgroup support. This can work, but it is higher churn and less robust than fixing sparse-path runtime semantics that S06 explicitly surfaced.

## Implementation landscape

### Core files to inspect/change first

- `src/modeling/track_e/mitigation_experiment.py`
  - Signal gate currently blocks at `no_correction_groups` (or later at `no_comparison_rows_after_alignment`).
  - Main seam for sparse-ready behavior.
- `tests/test_m003_track_e_mitigation_experiment.py`
  - Add explicit regression for sparse replay path that now must produce non-empty `pre_post_delta.parquet` and `status=ready_for_closeout` (when fallback conditions are acceptable).
- `tests/test_m003_mitigation_handoff_contract.py`
  - Lock continuity + any new deterministic diagnostics fields used to explain sparse-path readiness.

### Secondary files likely touched

- `src/modeling/README.md`
  - Update mitigation replay semantics and triage order.
- `.gsd/milestones/M003-rdpeu4/slices/S07/S07-UAT.md` (new or updated in execution slice)
  - Canonical replay + assertion snippet for ready-path closure.
- `outputs/modeling/track_e/mitigation_experiment/*`
- `outputs/modeling/m003_closeout/*`
- `.gsd/REQUIREMENTS.md`, `.gsd/PROJECT.md`, `.gsd/KNOWLEDGE.md` (closure traceability)

## Natural seams for planner decomposition

1. **Mitigation runtime seam (highest risk)**
   - Implement tiny-test support path that can generate non-empty pre/post deltas without breaking blocked branches.
2. **Mitigation contract/handoff seam**
   - Ensure diagnostics for sparse-path readiness are deterministic and continuity-safe.
3. **Integrated closeout seam**
   - Canonical S05 rerun and assertion updates to prove `ready_for_handoff` with explicit escalation payload.

## Build/prove-first order

1. Add failing mitigation regression(s) for the exact sparse replay failure mode (`no_comparison_rows_after_alignment` path).
2. Implement mitigation sparse-ready behavior in runtime.
3. Update handoff tests/docs for any new diagnostics fields.
4. Rerun S03 canonical command and verify non-empty deltas + `ready_for_closeout`.
5. Rerun S05 closeout and verify `ready_for_handoff` + escalation decision semantics.

## Verification plan (authoritative)

Use:
`/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`

1. Mitigation-focused tests:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_mitigation_contract.py \
  tests/test_m003_track_e_mitigation_experiment.py \
  tests/test_m003_mitigation_handoff_contract.py -q
```

2. Canonical S03 replay:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment \
  --config configs/track_e.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --fairness-dir outputs/modeling/track_e/fairness_audit \
  --output-dir outputs/modeling/track_e/mitigation_experiment
```

3. S03 artifact assertions (must pass):
- `manifest.status == "ready_for_closeout"`
- `validation_report.status == "pass"`
- `pre_post_delta.parquet` exists and row count > 0
- required columns from `REQUIRED_PRE_POST_DELTA_COLUMNS` present
- no forbidden ID/raw-text/demographic columns

4. Canonical S05 rerun:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate \
  --track-a-config configs/track_a.yaml \
  --track-e-config configs/track_e.yaml \
  --predictions outputs/modeling/track_a/predictions_test.parquet \
  --metrics outputs/modeling/track_a/metrics.csv \
  --candidate-metrics tests/fixtures/m003_candidate_metrics.csv \
  --output-dir outputs/modeling/m003_closeout
```

5. S05 artifact assertions (must pass):
- `manifest.status == "ready_for_handoff"`
- `manifest.compute_escalation_decision in {"local_sufficient","overflow_required"}`
- `validation_report.status == "pass"`
- `stage_rollup.readiness_block_stage_ids == []`
- continuity echoes present and non-empty (`baseline_anchor`, `split_context`)

6. Optional full M003 regression after S07 integration:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_audit_intake_contract.py \
  tests/test_m003_track_a_audit_intake.py \
  tests/test_m003_intake_handoff_contract.py \
  tests/test_m003_fairness_audit_contract.py \
  tests/test_m003_track_e_fairness_audit.py \
  tests/test_m003_fairness_audit_handoff_contract.py \
  tests/test_m003_mitigation_contract.py \
  tests/test_m003_track_e_mitigation_experiment.py \
  tests/test_m003_mitigation_handoff_contract.py \
  tests/test_m003_comparator_contract.py \
  tests/test_m003_track_a_stronger_comparator.py \
  tests/test_m003_comparator_handoff_contract.py \
  tests/test_m003_closeout_contract.py \
  tests/test_m003_milestone_closeout_gate.py \
  tests/test_m003_closeout_handoff_contract.py -q
```

## Planner watchouts

- Do not infer readiness from exit code alone (S03/S04 can return 0 on blocked branches by design).
- Preserve exact continuity payload equality (`baseline_anchor`, `split_context`).
- Keep status vocab stable unless absolutely required (new status strings would ripple into S05/tests/docs).
- If you introduce sparse-path fallback diagnostics, lock them in handoff tests to prevent silent semantic drift.

## Skill Discovery (suggest)

Installed and directly relevant:
- `test`
- `verification-loop`
- `debug-like-expert`

Not installed; discovered for core stack in this slice:
- **scikit-learn** (highest installs):
  - `npx skills add davila7/claude-code-templates@scikit-learn`
- **pandas** (highest installs):
  - `npx skills add jeffallan/claude-skills@pandas-pro`
- **duckdb** (highest installs):
  - `npx skills add silvainfm/claude-skills@duckdb`

Search note:
- `npx skills find "fairlearn"` returned no matching skill.

(No skills were installed during this research.)
