# S06 UAT — Fairness-signal sufficiency replay on real upstream predictions

This UAT script is the canonical operator runbook for S06 readiness and triage.

## Preconditions

1. Working directory is repo root:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.gsd/worktrees/M003-rdpeu4`
2. Python interpreter exists:
   - `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python`
3. Upstream S01 intake bundle exists and is valid:
   - `outputs/modeling/track_a/audit_intake/scored_intake.parquet`
   - `outputs/modeling/track_a/audit_intake/manifest.json` (`status=ready_for_fairness_audit`)
   - `outputs/modeling/track_a/audit_intake/validation_report.json` (`status=pass`)
4. Output directories are writable under `outputs/modeling/track_e/`.
5. Redaction guardrail is active: outputs remain aggregate-only (no raw review text, no row-level IDs exposed in subgroup/disparity artifacts, no demographic inference fields).

---

## Test Case 1 — Contract + runtime + handoff regression gate

**Purpose:** prove sufficiency contract semantics, runtime branch behavior, and handoff continuity are all enforced.

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest \
  tests/test_m003_fairness_audit_contract.py \
  tests/test_m003_track_e_fairness_audit.py \
  tests/test_m003_fairness_audit_handoff_contract.py -q
```

### Expected Outcomes

- Exit code `0`.
- Test suite covers:
  - `signal_sufficiency` payload required fields/outcome/reason vocab,
  - allowed fairness status vocabulary (`ready_for_mitigation`, `blocked_upstream`),
  - branch behavior (primary sufficient, fallback sufficient, insufficient),
  - exact continuity equality for `baseline_anchor` and `split_context`.

---

## Test Case 2 — Canonical fairness replay

**Purpose:** regenerate authoritative fairness artifacts with sufficiency diagnostics.

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit \
  --config configs/track_e.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --output-dir outputs/modeling/track_e/fairness_audit
```

2. Verify files exist:
   - `outputs/modeling/track_e/fairness_audit/manifest.json`
   - `outputs/modeling/track_e/fairness_audit/validation_report.json`
   - `outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet`
   - `outputs/modeling/track_e/fairness_audit/disparity_summary.parquet`

### Expected Outcomes

- Command exits `0`.
- Manifest and validation include `signal_sufficiency`.
- Status semantics are truthful:
  - `ready_for_mitigation` only with sufficient signal, or
  - `blocked_upstream` with explicit insufficiency reasons.

---

## Test Case 3 — Status/outcome coupling assertion (authoritative S06 check)

**Purpose:** enforce the exact S06 contract in machine-check form.

### Steps

1. Run:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

root = Path('outputs/modeling/track_e/fairness_audit')
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))

assert manifest['status'] in {'ready_for_mitigation', 'blocked_upstream'}, manifest['status']
assert validation['status'] in {'pass', 'fail'}, validation['status']
assert 'signal_sufficiency' in manifest, 'manifest missing signal_sufficiency'
assert 'signal_sufficiency' in validation, 'validation missing signal_sufficiency'

signal = manifest['signal_sufficiency']
outcome = signal.get('outcome')
assert outcome in {'primary_sufficient', 'fallback_sufficient', 'insufficient'}, outcome

if manifest['status'] == 'ready_for_mitigation':
    assert validation['status'] == 'pass', validation['status']
    assert int(manifest['row_counts']['subgroup_rows']) > 0, manifest['row_counts']
    assert int(manifest['row_counts']['disparity_rows']) > 0, manifest['row_counts']
    assert outcome in {'primary_sufficient', 'fallback_sufficient'}, outcome
else:
    assert validation['status'] == 'fail', validation['status']
    assert outcome == 'insufficient', outcome
    reasons = set(signal.get('reasons', []))
    assert reasons, 'blocked_upstream must expose insufficient reasons'

print('m003 s06 fairness sufficiency contract verified')
PY
```

### Expected Outcomes

- Exit code `0`.
- Prints: `m003 s06 fairness sufficiency contract verified`.

---

## Test Case 4 — Mitigation readiness smoke after fairness replay

**Purpose:** confirm S06 removed the old `no_disparity_rows` blockage path when fairness is ready.

### Steps

1. Run mitigation replay:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment \
  --config configs/track_e.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --fairness-dir outputs/modeling/track_e/fairness_audit \
  --output-dir outputs/modeling/track_e/mitigation_experiment
```

2. Run smoke assertion:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

fair = json.loads(Path('outputs/modeling/track_e/fairness_audit/manifest.json').read_text(encoding='utf-8'))
mit = json.loads(Path('outputs/modeling/track_e/mitigation_experiment/manifest.json').read_text(encoding='utf-8'))

if fair['status'] == 'ready_for_mitigation' and mit['status'] == 'blocked_insufficient_signal':
    reasons = set((mit.get('insufficient_signal') or {}).get('reasons') or [])
    assert 'no_disparity_rows' not in reasons, reasons

print('m003 s06 mitigation readiness smoke verified')
PY
```

### Expected Outcomes

- Both commands exit `0`.
- Smoke script prints `m003 s06 mitigation readiness smoke verified`.
- If mitigation is blocked, reasons may include sparse-support items (example: `no_correction_groups`) but **must not** include `no_disparity_rows` when fairness status is ready.

---

## Edge Cases

### Edge Case A — Fail-closed insufficient branch remains available

**Purpose:** prove S06 still supports truthful `blocked_upstream` when signal is truly insufficient.

#### Steps

1. Create a temporary strict config that disables fallback and forces larger subgroup support:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
from pathlib import Path
import yaml

src = Path('configs/track_e.yaml')
dst = Path('outputs/modeling/track_e/_tmp_track_e_s06_edge.yaml')
config = yaml.safe_load(src.read_text(encoding='utf-8'))
config.setdefault('fairness', {}).setdefault('signal_sufficiency', {}).setdefault('fallback', {})['enabled'] = False
config.setdefault('subgroups', {})['min_group_size'] = 999

dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
print(dst)
PY
```

2. Run fairness replay with the temp config:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit \
  --config outputs/modeling/track_e/_tmp_track_e_s06_edge.yaml \
  --intake-dir outputs/modeling/track_a/audit_intake \
  --output-dir outputs/modeling/track_e/fairness_audit_edge
```

3. Assert blocked semantics:

```bash
/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path('outputs/modeling/track_e/fairness_audit_edge/manifest.json').read_text(encoding='utf-8'))
validation = json.loads(Path('outputs/modeling/track_e/fairness_audit_edge/validation_report.json').read_text(encoding='utf-8'))

assert manifest['status'] == 'blocked_upstream', manifest['status']
assert validation['status'] == 'fail', validation['status']
assert manifest['signal_sufficiency']['outcome'] == 'insufficient', manifest['signal_sufficiency']
assert manifest['signal_sufficiency']['reasons'], manifest['signal_sufficiency']
print('s06 edge blocked_upstream path verified')
PY
```

#### Expected Outcomes

- Edge replay writes deterministic blocked artifacts.
- Contract semantics still hold under insufficient conditions.

### Edge Case B — Sparse-worktree fallback-ready branch (current canonical replay)

**Purpose:** make sparse replay expectation explicit for downstream operators.

#### Steps

1. Read canonical fairness manifest and check key fields.

#### Expected Outcomes

- `status = ready_for_mitigation`
- `signal_sufficiency.outcome = fallback_sufficient`
- `row_counts.primary_subgroup_rows = 0`
- `row_counts.primary_disparity_rows = 0`
- `row_counts.subgroup_rows > 0` and `row_counts.disparity_rows > 0`

This confirms fallback recovery is active and truthful.

---

## Triage Order (when anything fails)

1. `outputs/modeling/track_e/fairness_audit/manifest.json`
   - `status`, `row_counts`, `signal_sufficiency.outcome`, `signal_sufficiency.reasons`, fallback `row_deltas`
2. `outputs/modeling/track_e/fairness_audit/validation_report.json`
   - `status`, `checks[]`, `phases[]`, `signal_sufficiency`
3. `outputs/modeling/track_e/mitigation_experiment/manifest.json`
   - `status`, `insufficient_signal.reasons`
4. Upstream intake artifacts under `outputs/modeling/track_a/audit_intake/`

## S06 Handoff-Ready Definition

S06 is handoff-ready when Test Cases 1–4 pass and fairness artifacts encode one of the only two valid states:

1. **Mitigation-ready fairness**: `ready_for_mitigation` + non-empty subgroup/disparity rows + sufficiency outcome in `{primary_sufficient, fallback_sufficient}`.
2. **Truthful blocked upstream**: `blocked_upstream` + `validation.status=fail` + `signal_sufficiency.outcome=insufficient` + explicit reason codes.
