# S06: Fairness-signal sufficiency replay on real upstream predictions

**Goal:** Make S02 fairness replay materially usable for S03 by requiring non-empty subgroup/disparity signal on real S01 predictions, or by emitting an explicitly declared fallback strategy with deterministic diagnostics.
**Demo:** Running `python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit` regenerates a canonical fairness bundle where either (a) `status=ready_for_mitigation` with non-zero subgroup/disparity rows and `signal_sufficiency.outcome` showing `primary_sufficient` or `fallback_sufficient`, or (b) `status=blocked_upstream` with `validation.status=fail` and explicit insufficient-signal diagnostics.

## Must-Haves

- Advance **R009** by removing empty-but-pass fairness outcomes: S02 must publish actionable subgroup/disparity signal (or explicit blocked insufficiency) on real upstream predictions.
- Advance **R010** support by preserving fair-comparator context continuity (`baseline_anchor`, `split_context`) while making fairness-signal availability explicit and machine-readable.
- Advance **R012** continuity support by documenting one canonical S06 replay + triage path and locking handoff contract tests for sufficiency diagnostics.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
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
PY`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

fair = json.loads(Path('outputs/modeling/track_e/fairness_audit/manifest.json').read_text(encoding='utf-8'))
mit = json.loads(Path('outputs/modeling/track_e/mitigation_experiment/manifest.json').read_text(encoding='utf-8'))

if fair['status'] == 'ready_for_mitigation' and mit['status'] == 'blocked_insufficient_signal':
    reasons = set((mit.get('insufficient_signal') or {}).get('reasons') or [])
    assert 'no_disparity_rows' not in reasons, reasons

print('m003 s06 mitigation readiness smoke verified')
PY`

## Observability / Diagnostics

- Runtime signals: `signal_sufficiency` diagnostics in fairness `manifest.json` and `validation_report.json` (primary/fallback path, sufficiency outcome, reasons, row deltas).
- Inspection surfaces: `outputs/modeling/track_e/fairness_audit/{manifest.json,validation_report.json,subgroup_metrics.parquet,disparity_summary.parquet}` plus focused pytest suites.
- Failure visibility: blocked insufficiency must report deterministic reason codes and phase-local checks instead of silent empty-success outputs.
- Redaction constraints: subgroup/disparity artifacts remain aggregate-only and must not expose row-level IDs, raw text, or demographic-inference fields.

## Integration Closure

- Upstream surfaces consumed: `outputs/modeling/track_a/audit_intake/{manifest.json,validation_report.json,scored_intake.parquet}`, `configs/track_e.yaml`, `src/eda/track_e/subgroup_definition.py`.
- New wiring introduced in this slice: fairness sufficiency gate + fallback subgroup strategy in `src/modeling/track_e/fairness_audit.py`, shared sufficiency contract helpers in `src/modeling/common/fairness_audit_contract.py`, and handoff/UAT contract updates.
- What remains before the milestone is truly usable end-to-end: S07 must close mitigation delta readiness on tiny-test support paths and rerun S05 integrated closeout to `ready_for_handoff`.

## Tasks

- [x] **T01: Add fairness sufficiency diagnostics contract and regression coverage** `est:50m`
  - Why: S06 needs a stable, shared schema for sufficiency/fallback diagnostics before runtime changes so status semantics and handoff parsing do not drift.
  - Files: `src/modeling/common/fairness_audit_contract.py`, `src/modeling/common/__init__.py`, `tests/test_m003_fairness_audit_contract.py`
  - Do: Add contract constants and validators for `signal_sufficiency` payload shape, allowed outcomes/reason vocabulary, and deterministic diagnostics; keep existing fairness status vocabulary unchanged (`ready_for_mitigation`, `blocked_upstream`); expand contract regression tests for pass/fail branches.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py -q`
  - Done when: contract tests prove sufficiency payload validation catches malformed outcomes/reasons and exposes machine-readable check details.
- [x] **T02: Implement S02 fairness sufficiency gate with approved fallback subgroup strategy** `est:2h`
  - Why: Current S02 runtime can emit empty-but-pass fairness bundles; S06 must make readiness truthfully depend on usable signal.
  - Files: `src/modeling/track_e/fairness_audit.py`, `configs/track_e.yaml`, `tests/test_m003_track_e_fairness_audit.py`
  - Do: Add post-aggregation sufficiency evaluation; if primary subgroup/disparity rows are empty, run configured fallback strategy (deterministic and aggregate-safe) and record path metadata; publish `signal_sufficiency` in manifest/validation; emit `ready_for_mitigation` only when sufficiency is achieved, otherwise emit `blocked_upstream` + failing validation with explicit insufficient reasons.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -q && /mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
  - Done when: runtime tests cover primary-sufficient, fallback-sufficient, and blocked-insufficient branches and canonical replay writes deterministic sufficiency diagnostics.
- [x] **T03: Lock S06 handoff/UAT assertions and requirement traceability updates** `est:1h10m`
  - Why: Downstream S03/S05 and M004 consumers need a canonical replay/triage contract that explicitly includes sufficiency path truth.
  - Files: `tests/test_m003_fairness_audit_handoff_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M003-rdpeu4/slices/S06/S06-UAT.md`, `.gsd/REQUIREMENTS.md`
  - Do: Extend handoff tests for `signal_sufficiency` presence/semantics and continuity equality; update README + new S06 UAT with replay and triage order (including mitigation smoke interpretation); update requirement notes for R009/R010/R012 with S06 advancement evidence links.
  - Verify: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q && rg -n "signal_sufficiency|fallback_sufficient|primary_sufficient|blocked_upstream|S06" src/modeling/README.md .gsd/milestones/M003-rdpeu4/slices/S06/S06-UAT.md .gsd/REQUIREMENTS.md`
  - Done when: handoff regressions and docs encode one authoritative sufficiency replay contract and requirements traceability reflects S06 progress.

## Files Likely Touched

- `src/modeling/common/fairness_audit_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_e/fairness_audit.py`
- `configs/track_e.yaml`
- `tests/test_m003_fairness_audit_contract.py`
- `tests/test_m003_track_e_fairness_audit.py`
- `tests/test_m003_fairness_audit_handoff_contract.py`
- `src/modeling/README.md`
- `.gsd/milestones/M003-rdpeu4/slices/S06/S06-UAT.md`
- `.gsd/REQUIREMENTS.md`
- `outputs/modeling/track_e/fairness_audit/manifest.json`
- `outputs/modeling/track_e/fairness_audit/validation_report.json`
