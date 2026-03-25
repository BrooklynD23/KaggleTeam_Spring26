# S05 UAT — Integrated closeout gate + conditional compute escalation

## Objective

Prove that S05 delivers one canonical M003 closeout rerun surface that:
1. Replays S01→S04 deterministically.
2. Emits contract-valid closeout artifacts.
3. Preserves fail-closed readiness truth (`blocked_upstream` when signal is insufficient).
4. Emits explicit compute escalation decisions (`local_sufficient` / `overflow_required`) from machine-readable trigger evidence.

## Preconditions

1. Working directory is:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M003-rdpeu4`
2. Python executable is:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`
3. Required inputs exist:
   - `configs/track_a.yaml`
   - `configs/track_e.yaml`
   - `outputs/modeling/track_a/predictions_test.parquet`
   - `outputs/modeling/track_a/metrics.csv`
   - `tests/fixtures/m003_candidate_metrics.csv`
4. No manual edits are made inside `outputs/modeling/m003_closeout/` between steps.

---

## Test Case 1 — S05 contract/integration/handoff test gate

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_closeout_contract.py \
  tests/test_m003_milestone_closeout_gate.py \
  tests/test_m003_closeout_handoff_contract.py -q
```

### Expected outcome

- Exit code: `0`
- Test summary: all tests pass (currently 15 passing tests in this worktree).
- Confirms:
  - contract schema/vocabulary enforcement,
  - branch behavior (`ready_for_handoff`, `blocked_upstream`, scarcity/non-overflow, overflow-required),
  - handoff continuity echoes (`baseline_anchor`, `split_context`),
  - redaction constraints.

---

## Test Case 2 — Full M003 end-to-end regression including S05

### Steps

1. Run:

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

### Expected outcome

- Exit code: `0`
- Full suite passes (currently 61 passing tests in this worktree).
- Confirms S05 remains compatible with S01–S04 contracts and handoff surfaces.

---

## Test Case 3 — Canonical closeout replay command

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate \
  --track-a-config configs/track_a.yaml \
  --track-e-config configs/track_e.yaml \
  --predictions outputs/modeling/track_a/predictions_test.parquet \
  --metrics outputs/modeling/track_a/metrics.csv \
  --candidate-metrics tests/fixtures/m003_candidate_metrics.csv \
  --output-dir outputs/modeling/m003_closeout
```

### Expected outcome

- Exit code: `0`
- Log includes: `M003 closeout gate bundle generated: outputs/modeling/m003_closeout`
- Directory contains exactly the canonical artifacts:
  - `stage_status_table.parquet`
  - `manifest.json`
  - `validation_report.json`
  - `closeout_summary.md`

---

## Test Case 4 — Artifact contract assertions (schema + redaction + continuity)

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path
import pandas as pd

root = Path('outputs/modeling/m003_closeout')
required = {'stage_status_table.parquet', 'manifest.json', 'validation_report.json', 'closeout_summary.md'}
missing = [name for name in required if not (root / name).is_file()]
assert not missing, missing

manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))
table = pd.read_parquet(root / 'stage_status_table.parquet')

assert manifest['status'] in {'ready_for_handoff', 'blocked_upstream'}, manifest['status']
assert manifest['compute_escalation_decision'] in {'local_sufficient', 'overflow_required'}, manifest['compute_escalation_decision']
assert validation['status'] in {'pass', 'fail'}, validation['status']

expected_stages = {'s01_intake', 's02_fairness', 's03_mitigation', 's04_comparator'}
assert expected_stages.issubset(set(table['stage_id'].tolist())), table['stage_id'].tolist()
required_cols = {
    'stage_id', 'manifest_status', 'validation_status', 'phase',
    'duration_seconds', 'is_hard_block', 'is_soft_block', 'artifact_dir'
}
assert required_cols.issubset(set(table.columns)), required_cols - set(table.columns)

forbidden_cols = {'review_id', 'user_id', 'business_id', 'review_text', 'raw_text', 'text', 'gender', 'race', 'income', 'ethnicity', 'nationality'}
assert forbidden_cols.isdisjoint(set(table.columns)), forbidden_cols.intersection(set(table.columns))

assert 'baseline_anchor' in manifest, 'baseline_anchor missing'
assert 'split_context' in manifest, 'split_context missing'
print('m003 s05 closeout bundle verified')
PY
```

### Expected outcome

- Exit code: `0`
- Output prints: `m003 s05 closeout bundle verified`
- Confirms canonical shape, vocabularies, stage completeness, continuity echoes, and aggregate-safe constraints.

---

## Test Case 5 — Decision/triage checks for current replay state

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path('outputs/modeling/m003_closeout/manifest.json').read_text(encoding='utf-8'))
validation = json.loads(Path('outputs/modeling/m003_closeout/validation_report.json').read_text(encoding='utf-8'))

print('status=', manifest['status'])
print('compute_escalation_decision=', manifest['compute_escalation_decision'])
print('readiness_block_stage_ids=', manifest['stage_rollup']['readiness_block_stage_ids'])
print('runtime_capacity_evidence_count=', len(manifest['escalation']['runtime_capacity_evidence']))
print('fairness_signal_scarcity_evidence_count=', len(manifest['escalation']['fairness_signal_scarcity_evidence']))
print('validation_status=', validation['status'])
PY
```

### Expected outcome (current fixture replay)

- `status= blocked_upstream`
- `compute_escalation_decision= local_sufficient`
- `readiness_block_stage_ids` contains `s03_mitigation`
- `runtime_capacity_evidence_count= 0`
- `fairness_signal_scarcity_evidence_count` is positive (currently 5)
- `validation_status= fail`

This confirms fail-closed signal scarcity and non-overflow interpretation are both explicit.

---

## Edge Cases to Recheck Before Signoff

1. **Insufficient fairness signal branch**
   - Triggered by S03 `blocked_insufficient_signal` and/or S04 `do_not_adopt_no_fairness_signal`.
   - Must remain `compute_escalation_decision=local_sufficient` unless runtime-capacity evidence is present.

2. **Runtime-capacity overflow branch (test-driven)**
   - Covered by `tests/test_m003_milestone_closeout_gate.py` overflow-required path.
   - Must emit `compute_escalation_decision=overflow_required` only when runtime-capacity trigger evidence exists.

3. **Exit-code ambiguity protection**
   - Even with command exit `0`, closeout may be blocked.
   - Always triage from `manifest.json` and `validation_report.json`, not subprocess return code.

---

## Failure Triage Sequence

1. Open `outputs/modeling/m003_closeout/validation_report.json`.
2. Check failing `checks[]` and `phases[]` for first-failure phase and reason.
3. Inspect `manifest.stage_rollup` and `manifest.stage_diagnostics` for stage-level readiness reasons.
4. Inspect `manifest.escalation.runtime_capacity_evidence` before concluding overflow is required.
5. If failure is schema/vocabulary drift, run `tests/test_m003_closeout_contract.py` first to isolate contract regressions.
