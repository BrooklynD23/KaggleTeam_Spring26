# S06 — Research

**Date:** 2026-03-23

## Summary

S06 is a **high-risk remediation slice** focused on one boundary: S02 currently produces a contract-valid fairness bundle with **zero subgroup/disparity signal**, which leaves S03 mitigation blocked on real replay.

Current canonical state in this worktree:
- `outputs/modeling/track_e/fairness_audit/manifest.json` → `status=ready_for_mitigation`, but `row_counts.subgroup_rows=0`, `row_counts.disparity_rows=0`, `dropped_by_min_group_size=4`.
- `outputs/modeling/track_e/mitigation_experiment/manifest.json` → `status=blocked_insufficient_signal` with reasons `no_disparity_rows`, `no_correction_groups`.
- Milestone validator marks this as remediation-required (`.gsd/milestones/M003-rdpeu4/M003-rdpeu4-VALIDATION.md`).

So S06 should not add another broad subsystem; it should tighten the S02 signal-sufficiency behavior so downstream mitigation has actionable fairness signal (or explicitly declared fallback strategy) with machine-readable diagnostics.

## Requirement targeting (active)

- **R009 (primary support in S06):** fairness audit must be materially usable for mitigation tradeoff, not just schema-valid.
- **R010 (supporting):** comparator fairness context should reflect real signal availability (avoid permanent `no_fairness_signal` drift).
- **R012 (continuity support):** preserve canonical handoff truth in manifest/validation payloads for S07/S05/M004.

## Skill-informed implementation rules (applied)

- From **tdd-workflow**: “Tests BEFORE Code” and explicit edge/error branch coverage (add failing sufficiency tests before runtime edits).
- From **verification-loop**: use explicit verification gates (pytest + canonical replay + artifact assertions), not narrative-only closure.

## Key findings (codebase reality)

### 1) S02 runtime currently allows empty-but-pass fairness outputs by design

- `src/modeling/track_e/fairness_audit.py` computes subgroup metrics on fixed dimensions: `city`, `primary_category`, `price_tier`, `review_volume_tier`.
- It sets `status = STATUS_READY_FOR_MITIGATION` after schema checks even if row counts are zero.
- Contract validators in `src/modeling/common/fairness_audit_contract.py` check required columns + boolean field validity, but **do not enforce non-empty rows**.

This is why S02 can pass while S03 remains materially blocked.

### 2) The immediate root causes in this worktree are data-shape constraints, not runtime crashes

- `configs/track_e.yaml` sets `subgroups.min_group_size: 10`.
- `data/curated/business.parquet` is absent; fairness runtime uses synthetic shell rows with unknown attributes.
- `outputs/modeling/track_a/audit_intake/scored_intake.parquet` has only 3 rows (train/validation/test = 1 each).
- `data/curated/review_fact.parquet` has 3 rows.

Given this shape, all subgroup candidates collapse or get filtered.

### 3) Downstream compatibility constrains how S06 can change S02

- S03 and S04 currently hard-check fairness manifest status as exactly `ready_for_mitigation`.
  - `src/modeling/track_e/mitigation_experiment.py`
  - `src/modeling/track_a/stronger_comparator.py`
- Introducing a new fairness status (e.g., `ready_with_fallback`) will cascade into S03/S04/S05 and test updates.

Pragmatic implication: keep status vocabulary stable if possible; encode sufficiency/fallback in additional fields.

### 4) Important forward signal for S07: non-empty S02 alone may still leave S03 blocked

I validated a synthetic non-empty disparity input against current 3-row intake: S03 can still block with `no_comparison_rows_after_alignment` because mitigation evaluates on test split and this replay has only one test row.

So S06 should still focus on S02 sufficiency, but planner should expect S07 to likely adjust mitigation evaluation readiness logic for tiny test support.

### 5) There is no richer upstream predictions artifact in this worktree today

Only these exist:
- `outputs/modeling/track_a/predictions_test.parquet`
- `outputs/modeling/track_a/metrics.csv`

No alternate larger predictions artifact is present locally for replay.

## Recommendation

Implement S06 as a **targeted S02 sufficiency hardening + fallback strategy declaration**, not a full modeling rebuild.

### Recommended behavior

1. Run primary S02 logic exactly as today.
2. Add a **signal sufficiency check** after subgroup/disparity construction.
3. If primary signal is empty, attempt an **explicitly configured fallback subgroup strategy** (approved, deterministic, aggregate-safe).
4. Emit machine-readable diagnostics declaring which path was used and whether sufficiency was achieved.

### Practical compatibility recommendation

- Keep fairness manifest status `ready_for_mitigation` when sufficiency is achieved (primary or fallback).
- If both primary and fallback are insufficient, emit `blocked_upstream` with explicit insufficient-signal reason payload (so failure is visible and not silently “ready”).
- Avoid adding new status vocabulary unless planner accepts S03/S04/S05 ripple edits.

## Implementation landscape

### Core files likely touched

- `src/modeling/track_e/fairness_audit.py`  
  Add sufficiency gate, fallback execution path, diagnostics payload fields.

- `src/modeling/common/fairness_audit_contract.py`  
  Extend contract checks for sufficiency diagnostics structure (not necessarily row-count hard requirement at contract layer unless explicitly chosen).

- `src/modeling/common/__init__.py`  
  Export any new constants/helpers.

- `tests/test_m003_track_e_fairness_audit.py`  
  Add replay tests for:
  - primary-sufficient path,
  - fallback-used-sufficient path,
  - primary+fallback insufficient path (blocked with reasons).

- `tests/test_m003_fairness_audit_contract.py`  
  Add validator tests for new sufficiency diagnostics fields/semantics.

- `tests/test_m003_fairness_audit_handoff_contract.py`  
  Lock continuity + sufficiency metadata expectations.

- `src/modeling/README.md` and `.gsd/milestones/M003-rdpeu4/slices/S06/S06-UAT.md` (next slice docs)

### Natural seams for planner decomposition

1. **Contract seam**: define sufficiency diagnostics schema + allowed semantics.
2. **Runtime seam**: implement sufficiency gate and fallback strategy execution.
3. **Handoff seam**: tests/docs/UAT updates and canonical replay assertions.

## Proposed S06 acceptance shape (planner-facing)

S06 done when S02 replay produces either:

- **Path A (primary sufficient):**
  - `manifest.status=ready_for_mitigation`
  - `row_counts.subgroup_rows > 0`
  - `row_counts.disparity_rows > 0`
  - sufficiency payload indicates primary path.

or

- **Path B (fallback sufficient):**
  - `manifest.status=ready_for_mitigation`
  - non-zero subgroup/disparity rows from declared fallback strategy
  - sufficiency payload includes strategy name, trigger reason, and row deltas.

and if neither path yields signal:

- `manifest.status=blocked_upstream`
- `validation.status=fail`
- explicit insufficient-signal reasons in canonical diagnostics.

## Build/prove-first order

1. Add failing tests for sufficiency/fallback semantics in S02 runtime + contract/handoff suites.
2. Implement runtime sufficiency gate in `fairness_audit.py`.
3. Implement/lock sufficiency diagnostics schema in contract helpers.
4. Update README/UAT contract language.
5. Run targeted tests and canonical replay; assert artifact truth.

## Verification plan (authoritative)

Use:
`/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`

1. Targeted S02 tests:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_fairness_audit_contract.py \
  tests/test_m003_track_e_fairness_audit.py \
  tests/test_m003_fairness_audit_handoff_contract.py -q
```

2. Canonical S02 replay:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit \
  --config configs/track_e.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --output-dir outputs/modeling/track_e/fairness_audit
```

3. Artifact assertions (S06-specific):
- canonical files exist,
- status/validation semantics match sufficiency outcome,
- sufficiency diagnostics payload is present and structured,
- no forbidden raw-text/demographic columns.

4. Downstream smoke (informational for S07 planning):

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment \
  --config configs/track_e.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --fairness-dir outputs/modeling/track_e/fairness_audit \
  --output-dir outputs/modeling/track_e/mitigation_experiment
```

Record whether blockage reason shifts from `no_disparity_rows` to alignment/test-support reasons; that is key S07 input.

## Planner watchouts

- Do **not** rely on process exit codes for readiness; use manifest/validation statuses.
- Avoid introducing new fairness status strings unless explicitly planning S03/S04 compatibility updates.
- Keep `baseline_anchor` and `split_context` exact continuity (existing handoff tests enforce equality).
- Keep subgroup outputs aggregate-safe; do not leak row IDs in subgroup values.

## Skill Discovery (suggest)

Installed and directly relevant:
- `tdd-workflow`
- `verification-loop`
- `test`

Not installed; discovered for core stack in this slice:

- **scikit-learn** (highest installs):
  - `npx skills add davila7/claude-code-templates@scikit-learn`
- **duckdb** (highest installs):
  - `npx skills add silvainfm/claude-skills@duckdb`
- **pandas** (highest installs):
  - `npx skills add jeffallan/claude-skills@pandas-pro`

Search note:
- `npx skills find "fairlearn"` returned no results.

(No skills were installed during this research.)
