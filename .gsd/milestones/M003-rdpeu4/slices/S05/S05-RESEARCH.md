# S05 — Research

**Date:** 2026-03-23

## Summary

S05 is a **targeted integration closeout** slice (not new modeling R&D). The codebase already has working S01–S04 runtimes and contracts; what is missing is one canonical integrated rerun gate that:

1. reruns the canonical S01→S04 commands,
2. emits one machine-readable closeout bundle,
3. makes an explicit compute escalation decision (`local_sufficient` or `overflow_required`), and
4. provides a clean M004 handoff surface.

Current worktree truth after replay in this environment:
- S01 intake: `ready_for_fairness_audit` / validation `pass`
- S02 fairness: `ready_for_mitigation` / validation `pass` (0 disparity rows)
- S03 mitigation: `blocked_insufficient_signal` / validation `fail` (expected fail-closed branch)
- S04 comparator: `ready_for_closeout` / validation `pass`, `adopt_recommendation=false`, `decision_reason=do_not_adopt_no_fairness_signal`
- All M003 tests for S01–S04 currently pass together: `46 passed`

So S05 should be built as a thin integration/decision layer over existing contracts, mirroring prior integrated closeout style (M002 S06 pattern), not as dispatcher churn or new training flow.

## Requirement targeting (Active requirements)

- **R010 (active, supported by S05):** consume comparator outputs and preserve materiality decision continuity in integrated closeout.
- **R009 (active, supported by S05):** carry mitigation/fairness/runtime evidence into one authoritative closeout surface; do not hide blocked-insufficient-signal outcomes.
- **R012 (active, continuity support):** produce canonical replay + handoff artifacts so M004 can consume without reconstruction.
- **R022 (active in roadmap, conditional owner S05):** emit explicit compute escalation disposition with evidence-backed trigger evaluation.

Important drift to fix during/after S05 closure: `.gsd/REQUIREMENTS.md` traceability table still shows **R022 deferred/unmapped**, which conflicts with M003 roadmap ownership.

## Skill-informed implementation rules (applied)

- From **tdd-workflow**: **“Tests BEFORE Code”** and explicit edge/error branch coverage.
- From **verification-loop**: close with explicit verification gates (tests + rerun + artifact assertions), not narrative-only completion.
- From `tests/CLAUDE.md`: keep tests contract/integration focused; avoid full training/pipeline rebuild behavior in tests.

## Key findings (codebase reality)

### 1) S05 runtime/contract surface does not exist yet

No integrated closeout module currently exists under `src/modeling/`.

Existing modeled runtimes are only:
- `src/modeling/track_a/audit_intake.py` (S01)
- `src/modeling/track_e/fairness_audit.py` (S02)
- `src/modeling/track_e/mitigation_experiment.py` (S03)
- `src/modeling/track_a/stronger_comparator.py` (S04)

No `test_m003_*closeout*` tests exist yet.

### 2) Existing S01–S04 contracts are strong and should be composed, not replaced

Canonical bundle roots already locked:
- `outputs/modeling/track_a/audit_intake/`
- `outputs/modeling/track_e/fairness_audit/`
- `outputs/modeling/track_e/mitigation_experiment/`
- `outputs/modeling/track_a/stronger_comparator/`

All include `manifest.json` + `validation_report.json` with phase/check diagnostics and continuity fields (`split_context`, `baseline_anchor`).

### 3) Exit-code semantics are intentionally non-uniform (critical for S05)

From existing runtime behavior and knowledge log:
- S03/S04 intentionally return exit `0` on blocked branches after writing deterministic artifacts.
- Therefore S05 **must key off manifest/validation statuses, not process exit codes**.

This is a hard integration rule for closeout decision correctness.

### 4) Current integrated replay indicates signal/data limitations, not compute limitations

Observed in canonical artifacts:
- S02 `disparity_rows=0`, `dropped_by_min_group_size=4`
- S03 `blocked_insufficient_signal` reasons include `no_disparity_rows`, `no_correction_groups`
- S04 runtime gate passes (`runtime_within_budget=true`) but fairness signal unavailable (`fairness_signal_available=false`), producing deterministic do-not-adopt

This means current blockers are fairness-signal/data-shape constraints, not local runtime overflow.

### 5) S05 should avoid pipeline dispatcher expansion

`scripts/pipeline_dispatcher.py` remains EDA-centric. M003 slices established explicit modeling CLI entrypoints; S05 should continue this pattern with one closeout CLI rather than broad dispatcher rewiring.

## Recommendation

Implement S05 as a **new integrated closeout gate runtime + contract + handoff tests/docs**.

Recommended CLI surface:

```bash
python -m src.modeling.m003_closeout_gate \
  --track-a-config configs/track_a.yaml \
  --track-e-config configs/track_e.yaml \
  --predictions outputs/modeling/track_a/predictions_test.parquet \
  --metrics outputs/modeling/track_a/metrics.csv \
  --candidate-metrics tests/fixtures/m003_candidate_metrics.csv \
  --output-dir outputs/modeling/m003_closeout
```

Recommended runtime behavior:
1. Execute canonical S01→S04 commands in sequence (always attempt each stage, even if earlier status blocks).
2. Read all four stage manifests/validation reports.
3. Build one closeout decision payload including:
   - stage readiness matrix,
   - continuity checks,
   - mitigation/comparator decision interpretation,
   - compute escalation trigger evaluation,
   - final `compute_escalation_decision` (`local_sufficient`/`overflow_required`).
4. Write deterministic closeout artifacts regardless of branch.

## Implementation landscape

### Existing files to reuse directly

- `src/modeling/track_a/audit_intake.py`
  - canonical S01 rerun command + status schema (`ready_for_fairness_audit` / `blocked_upstream`).
- `src/modeling/track_e/fairness_audit.py`
  - canonical S02 readiness gate and fairness diagnostics.
- `src/modeling/track_e/mitigation_experiment.py`
  - blocked-insufficient-signal semantics + mitigation diagnostics surface.
- `src/modeling/track_a/stronger_comparator.py`
  - runtime/materiality/fairness-aware adoption context.
- `src/modeling/common/{audit_intake_contract.py,fairness_audit_contract.py,mitigation_contract.py,comparator_contract.py}`
  - status vocabulary and schema validator patterns.
- `src/modeling/README.md`
  - canonical command/path/status documentation pattern.
- `tests/test_m003_*_handoff_contract.py`
  - continuity/redaction handoff regression style.

### New files likely needed

- `src/modeling/common/closeout_contract.py`
- `src/modeling/common/__init__.py` (export closeout constants/validators)
- `src/modeling/m003_closeout_gate.py`
- `tests/test_m003_closeout_contract.py`
- `tests/test_m003_milestone_closeout_gate.py`
- `tests/test_m003_closeout_handoff_contract.py`
- `src/modeling/README.md` (S05 section)
- `.gsd/milestones/M003-rdpeu4/slices/S05/S05-UAT.md`

### Natural seams for planner decomposition

1. **Contract seam**
   - define closeout manifest status vocabulary, required stage matrix columns, escalation decision vocabulary.
2. **Runtime seam**
   - orchestrate rerun, collect stage artifacts, evaluate escalation triggers, write closeout bundle.
3. **Handoff/docs seam**
   - continuity regression tests, canonical replay docs, triage instructions.

## Proposed S05 closeout contract shape (planner-facing)

### Bundle root

`outputs/modeling/m003_closeout/`

### Required files

- `stage_status_table.parquet`
- `manifest.json`
- `validation_report.json`
- `closeout_summary.md`

### Suggested manifest status vocabulary

- `ready_for_handoff`
- `blocked_upstream`

### Required decision vocabulary

- `compute_escalation_decision`: `local_sufficient` | `overflow_required`

### Suggested stage table columns

- `stage_id` (`s01_intake`, `s02_fairness`, `s03_mitigation`, `s04_comparator`)
- `manifest_status`
- `validation_status`
- `phase`
- `duration_seconds`
- `is_hard_block`
- `is_soft_block`
- `artifact_dir`

### Escalation trigger guidance (explicit)

Recommended `overflow_required` triggers:
- comparator runtime gate exceeded (`runtime_within_budget == false`), or
- explicit runtime capacity failures found in diagnostics (`oom|out of memory|timeout|killed`), or
- configured closeout runtime ceiling exceeded.

Recommended **non-triggers** (stay `local_sufficient`):
- S03 `blocked_insufficient_signal` due subgroup/data signal constraints,
- comparator do-not-adopt caused by `no_fairness_signal` alone.

This preserves R022 as conditional compute escalation rather than using compute overflow to mask data-signal limitations.

## Build/prove-first order

1. Add failing closeout contract tests (`test_m003_closeout_contract.py`).
2. Add failing runtime integration tests for:
   - happy integrated replay,
   - blocked-upstream propagation,
   - blocked-insufficient-signal + local_sufficient decision,
   - overflow-trigger branch.
3. Implement `closeout_contract.py` and exports.
4. Implement `m003_closeout_gate.py` runtime.
5. Add handoff continuity tests + README/UAT docs.
6. Run integrated verification sequence and capture outputs.

## Verification plan (authoritative)

Use project interpreter:
`/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`

1. New S05 tests:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_closeout_contract.py \
  tests/test_m003_milestone_closeout_gate.py \
  tests/test_m003_closeout_handoff_contract.py -q
```

2. Full M003 regression + S05 closeout gate:

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

3. Canonical closeout replay:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate \
  --track-a-config configs/track_a.yaml \
  --track-e-config configs/track_e.yaml \
  --predictions outputs/modeling/track_a/predictions_test.parquet \
  --metrics outputs/modeling/track_a/metrics.csv \
  --candidate-metrics tests/fixtures/m003_candidate_metrics.csv \
  --output-dir outputs/modeling/m003_closeout
```

4. Artifact assertion snippet should verify:
- closeout files exist,
- closeout status vocabulary valid,
- escalation decision vocabulary valid,
- stage status table has all four stages,
- continuity echoes (`baseline_anchor`, `split_context`) preserved,
- no raw-text/demographic forbidden fields in stage table/summary context.

## Key fragility to lock in tests

- **Status interpretation drift:** using process exit code instead of manifest status will misclassify S03/S04 outcomes.
- **Continuity drift:** S05 must preserve/echo exact upstream `baseline_anchor` + `split_context` lineage.
- **False compute escalation:** do not classify fairness-signal scarcity as compute insufficiency.
- **Requirements-state drift:** R022 mapping/status in `.gsd/REQUIREMENTS.md` must align with S05 closeout evidence.

## Skill Discovery (suggest)

Installed and directly relevant:
- `tdd-workflow`
- `verification-loop`
- `test`

Not installed; discovered for S05-adjacent core tech:
- Pandas (highest install count):
  - `npx skills add jeffallan/claude-skills@pandas-pro`
- DuckDB:
  - `npx skills add silvainfm/claude-skills@duckdb`

For compute-escalation infra research:
- `npx skills find "hpc"` returned no direct skill.

(No skills were installed during this research.)
