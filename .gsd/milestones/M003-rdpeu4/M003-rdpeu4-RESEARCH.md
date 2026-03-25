# M003-rdpeu4 — Research

**Date:** 2026-03-23

## Summary

M003 should start with a **reality-check gate** before any fairness or stronger-model work: this worktree currently contains robust Track E EDA and Track A/D EDA artifacts logic, but **does not contain the modeled-source surfaces that M003 assumes** (`src/modeling/*`, `tests/test_track_*_baseline_model.py`, `outputs/modeling/*`).

That means the first thing to prove is not “fairness mitigation works,” but “the upstream model artifacts for audit are present and reproducible in this worktree.”

If that gate is passed (or rehydrated), the natural path is:
1. audit Track A first (default target already established in M002 docs),
2. add one executable mitigation lever with pre/post fairness + accuracy metrics,
3. run stronger/combined model passes only where gains are material to framing questions,
4. keep Colab/HPC as a conditional fallback only.

## Key Findings (Codebase Reality)

### 1) Track E is implemented as **data-level fairness diagnostics**, not model audit

Relevant files:
- `src/eda/track_e/fairness_baseline.py`
- `src/eda/track_e/mitigation_candidates.py`
- `src/eda/track_e/summary_report.py`

Current Track E Stage 7 computes subgroup gaps from Stage 2–4 data aggregates (`mean_stars`, `mean_useful`, coverage, KS results), not from model predictions or decision outcomes. Stage 8 produces mitigation guidance markdown, but no executable pre/post mitigation experiment.

Implication for M003: we need a new model-audit layer (or extension) that consumes upstream model outputs and computes fairness-vs-accuracy tradeoffs on real predictions.

### 2) Strong leakage/governance guardrails already exist and should be reused

- Track A leakage checks: `src/eda/track_a/leakage_audit.py`
- Track D leakage hard gate: `src/eda/track_d/leakage_check.py` + tests
- Track E no-demographic-inference/banned-column enforcement: `src/eda/track_e/common.py`, `tests/test_track_e_no_demographic_inference.py`

Implication: M003 should extend these patterns instead of inventing new policy surfaces.

### 3) Major integration risk: M002 docs assert modeling surfaces that are absent here

Filesystem checks in this worktree show:
- `src/modeling`: missing
- `outputs/modeling`: missing
- `tests/test_m002_modeling_contract.py`: missing
- `tests/test_m002_handoff_verification.py`: missing
- `tests/test_track_a_baseline_model.py`: missing

Yet M002 milestone docs under `.gsd/milestones/M002-c1uww6/...` describe those surfaces as complete.

Implication: roadmap must include an early **intake integrity slice** to reconcile doc-state vs code-state before planning fairness/stronger modeling slices.

### 4) Orchestration currently covers EDA only

- `scripts/pipeline_dispatcher.py` and `scripts/run_pipeline.py` expose shared + Track A/B/C/D/E EDA approaches.
- No modeling approach wiring is present in dispatcher/launcher.

Implication: M003 either needs separate modeling/fairness entrypoints (explicit commands), or orchestration expansion if the team wants single-command reproducibility.

### 5) Compute path prior art exists for local GPU acceleration, not Colab/HPC automation

- `docs/gpu_acceleration.md`
- `src/common/gpu_check.py`
- `src/common/parquet_io.py`

Current support is local/WSL GPU acceleration via cudf-polars; there is no implemented Colab/HPC workflow contract in repo code yet.

Implication: R022 should remain optional unless a measured runtime/quality trigger is hit.

## What Should Be Proven First

1. **Upstream audit intake exists in this worktree**
   - One authoritative upstream model target (Track A default, Track D secondary) with reproducible prediction artifacts.
2. **Model-aware fairness metrics run end-to-end on that target**
   - Not just data-level disparity; actual model prediction/decision fairness metrics.
3. **One mitigation lever is executable and measurable**
   - Pre/post fairness and pre/post accuracy in one table.
4. **Only then run stronger/combined model passes**
   - Require explicit material-gain rule to avoid model-zoo drift.

## Existing Patterns to Reuse

- **Artifact contract pattern** from M002 docs: per-track metrics/config/summary + scored outputs under stable output roots.
- **Track E subgroup/coverage/proxy pipeline** as fairness feature backbone.
- **Track A split/leakage semantics** for strict temporal fairness evaluation.
- **Track D D1-vs-D2 boundary rule** (D1 required, D2 optional/non-blocking) to avoid recommender scope creep.
- **Pytest-first contract enforcement** (existing repo style) for drift visibility.

## Boundary Contracts That Matter for M003

### A) Upstream model intake contract (must be explicit)

For whichever upstream target is chosen, require a stable scored artifact schema (candidate fields):
- `entity_id` (review/business/user id depending on track)
- `as_of_date` / split marker
- `y_true`
- `y_pred` or ranking score
- `subgroup join key` (at minimum `business_id` for Track E subgroup linkage)
- `model_name`

### B) Fairness audit output contract

A machine-readable artifact that includes per-subgroup:
- fairness metric values,
- disparity vs reference,
- threshold flags,
- sample/support counts,
- paired accuracy metric context.

### C) Mitigation experiment contract

One pre/post table with:
- mitigation name,
- baseline fairness + accuracy,
- mitigated fairness + accuracy,
- deltas,
- pass/fail against configured thresholds.

### D) Stronger-model comparator contract

For each stronger/combined pass:
- baseline metric,
- stronger metric,
- delta,
- runtime cost,
- “material improvement” boolean by predefined threshold.

### E) Compute escalation contract (optional)

Escalate to Colab/HPC only if local runs violate explicit trigger(s), e.g.:
- runtime ceiling exceeded,
- memory constraints,
- inability to complete required comparisons within milestone window.

## Known Failure Modes That Should Drive Slice Ordering

1. **Doc-code drift** (claimed baseline artifacts absent locally) can invalidate all downstream fairness work.
2. **Track E vagueness risk** if audit is left as descriptive EDA rather than model-bound audit.
3. **Mitigation theater risk** if mitigation is narrative-only without measured tradeoff.
4. **Model-zoo drift** if stronger models are explored without framing-question gain criteria.
5. **Premature infrastructure drag** if Colab/HPC setup starts before local evidence shows need.

## Requirement Analysis (M003 Focus)

### Table stakes for this milestone

- **R009**: mandatory; this is the core accountability deliverable.
- **R010**: mandatory but constrained; stronger models only where gains are material.

### Continuity expectations (active but mostly downstream)

- **R012** (coherent trust story) should influence M003 artifact wording now.
- **R011** (showcase build) is M004-owned, but M003 should emit clean inputs for it.

### Deferred/optional in M003 unless trigger is hit

- **R022**: keep deferred unless local runtime/quality evidence forces escalation.

### Overbuild risks

- Treating Track E as standalone predictive track (already out-of-scope by project guardrails).
- Turning stronger-model exploration into broad benchmark exercises unrelated to framing questions.

## Suggested Slice Boundaries for Roadmap Planner

1. **S1 — Intake integrity + contract rehydration**
   - Reconcile M002 modeled-surface assumptions with actual worktree state.
   - Recreate/verify baseline source + artifact contracts needed for M003.

2. **S2 — Model-aware fairness audit (Track A default)**
   - Build executable fairness audit against real upstream predictions.
   - Persist fairness artifact bundle + tests.

3. **S3 — One mitigation lever with measured tradeoff**
   - Implement one lever (e.g., reweighting or threshold post-processing),
   - emit pre/post fairness-accuracy delta table and summary.

4. **S4 — Stronger/combined modeling pass with materiality gate**
   - Run only preselected stronger candidate(s),
   - require explicit gain-vs-cost decision record.

5. **S5 — Optional compute overflow enablement (conditional)**
   - Only if S2–S4 evidence shows local path insufficient.

## Skill Discovery (suggest)

Installed skills already relevant to execution quality:
- `debug-like-expert`
- `test`
- `tdd-workflow`
- `verification-loop`

External skill candidates found (not installed):

- **scikit-learn**
  - `npx skills add davila7/claude-code-templates@scikit-learn` (highest installs in results)
- **duckdb**
  - `npx skills add silvainfm/claude-skills@duckdb`
- **pandas**
  - `npx skills add jeffallan/claude-skills@pandas-pro`
- **xgboost/lightgbm** (if stronger-model passes choose boosting outside sklearn HGB)
  - `npx skills add tondevrel/scientific-agent-skills@xgboost-lightgbm`

Not found via skill search:
- `fairlearn` (no matching skill discovered)

## Candidate Requirements (Advisory, Not Auto-Binding)

1. **Candidate:** M003 upstream-intake schema requirement
   - Why: prevents fairness pipeline from depending on ad hoc prediction files.

2. **Candidate:** Mandatory pre/post fairness-accuracy delta artifact for mitigation claim
   - Why: enforces measurable tradeoff, directly supporting R009.

3. **Candidate:** Materiality threshold requirement for stronger-model adoption
   - Why: keeps R010 disciplined and avoids overbuild.

4. **Candidate:** Compute escalation trigger criteria
   - Why: keeps R022 genuinely conditional and auditable.

## Direct Answers to Strategic Questions

- **What should be proven first?**
  - Upstream modeled artifacts exist and are reproducible in this worktree.

- **What existing patterns should be reused?**
  - Track E subgroup/proxy/fairness scaffolding, Track A/D leakage contracts, and M002-style artifact/test contracts.

- **What boundary contracts matter?**
  - Upstream prediction schema, fairness artifact schema, mitigation pre/post delta schema, stronger-model materiality gate, compute-escalation trigger.

- **What constraints does the codebase impose?**
  - No raw text, no demographic inference, strict as-of logic, D1/D2 separation, config-driven paths, and currently EDA-only orchestration.

- **Known failure modes shaping slice order?**
  - Doc-code drift first, then fairness-vagueness risk, mitigation-theater risk, model-zoo risk, and premature HPC drag.

- **Missing vs optional behaviors from requirements?**
  - Missing: explicit audit intake schema + tradeoff artifact contracts.
  - Optional: Colab/HPC path until measured trigger.
  - Out of scope: standalone Track E predictor.
