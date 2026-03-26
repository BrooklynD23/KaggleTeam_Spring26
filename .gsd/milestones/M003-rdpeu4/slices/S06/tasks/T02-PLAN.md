---
estimated_steps: 5
estimated_files: 3
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T02: Implement S02 fairness sufficiency gate with approved fallback subgroup strategy

**Slice:** S06 — Fairness-signal sufficiency replay on real upstream predictions
**Milestone:** M003-rdpeu4

## Description

Modify the fairness runtime so `ready_for_mitigation` is only emitted when non-empty subgroup/disparity signal exists, while preserving deterministic fallback behavior and explicit blocked diagnostics when signal remains insufficient.

## Steps

1. Add runtime tests first in `tests/test_m003_track_e_fairness_audit.py` for three branches: primary-sufficient, fallback-sufficient, and primary+fallback insufficient (`blocked_upstream` + fail validation + explicit reasons).
2. Update `src/modeling/track_e/fairness_audit.py` to evaluate sufficiency after primary subgroup/disparity construction and to record `signal_sufficiency` diagnostics (outcome, reasons, counts, path metadata).
3. Implement configured fallback subgroup strategy for insufficiency cases (deterministic, aggregate-safe), including row-count deltas from primary to fallback attempt.
4. Emit `ready_for_mitigation` only when sufficiency is satisfied (primary or fallback); otherwise emit `blocked_upstream` with `validation.status=fail` and explicit insufficient-signal reason payload.
5. Add any needed fallback config keys in `configs/track_e.yaml` with conservative defaults and comments aligned to governance constraints.

## Must-Haves

- [ ] Runtime no longer reports empty subgroup/disparity bundles as `ready_for_mitigation`.
- [ ] Manifest and validation outputs both include `signal_sufficiency` payload with deterministic outcomes and reason codes.
- [ ] Fallback strategy remains aggregate-safe (no row IDs/raw text/demographic columns in emitted parquet tables).

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

root = Path('outputs/modeling/track_e/fairness_audit')
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
validation = json.loads((root / 'validation_report.json').read_text(encoding='utf-8'))

signal = manifest.get('signal_sufficiency', {})
assert signal.get('outcome') in {'primary_sufficient', 'fallback_sufficient', 'insufficient'}
if manifest['status'] == 'ready_for_mitigation':
    assert int(manifest['row_counts']['subgroup_rows']) > 0
    assert int(manifest['row_counts']['disparity_rows']) > 0
    assert validation['status'] == 'pass'
else:
    assert manifest['status'] == 'blocked_upstream'
    assert validation['status'] == 'fail'
    assert signal.get('reasons')
print('s06 t02 runtime sufficiency verified')
PY`

## Observability Impact

- Signals added/changed: `signal_sufficiency` object in fairness manifest/validation with branch-specific outcome, reasons, and row-count deltas.
- How a future agent inspects this: inspect `outputs/modeling/track_e/fairness_audit/{manifest.json,validation_report.json}` and run `tests/test_m003_track_e_fairness_audit.py`.
- Failure state exposed: insufficient subgroup signal is explicit (`blocked_upstream`, `validation.status=fail`, reason list) instead of silent empty-ready outputs.

## Inputs

- `src/modeling/track_e/fairness_audit.py` — Existing S02 runtime to harden with sufficiency and fallback logic.
- `configs/track_e.yaml` — Existing fairness/subgroup thresholds used by replay runtime.
- `tests/test_m003_track_e_fairness_audit.py` — Runtime regression suite to extend with S06 branches.
- `src/modeling/common/fairness_audit_contract.py` — S06 T01 contract helpers/constants used by runtime outputs.

## Expected Output

- `src/modeling/track_e/fairness_audit.py` — Sufficiency gate, fallback strategy path, and diagnostics emission.
- `configs/track_e.yaml` — Explicit fallback strategy configuration keys/defaults.
- `tests/test_m003_track_e_fairness_audit.py` — Branch coverage for primary/fallback/insufficient replay behavior.
