---
estimated_steps: 5
estimated_files: 7
skills_used:
  - verification-loop
  - test
---

# T03: Rerun closeout with S03-ready artifacts and lock handoff-readiness evidence

**Slice:** S07 — Mitigation ready-path delta closure + closeout rerun
**Milestone:** M003-rdpeu4

## Description

Prove milestone-level closure by rerunning canonical S03 and S05 flows, asserting that closeout becomes handoff-ready, and codifying the resulting requirement-evidence updates.

## Steps

1. Extend `tests/test_m003_milestone_closeout_gate.py` and/or `tests/test_m003_closeout_handoff_contract.py` to lock the ready-path expectation that S03 `ready_for_closeout` propagates to empty `readiness_block_stage_ids` at S05.
2. Run canonical S03 mitigation replay to regenerate `outputs/modeling/track_e/mitigation_experiment/` with non-empty `pre_post_delta.parquet` and `status=ready_for_closeout`.
3. Run canonical S05 closeout replay to regenerate `outputs/modeling/m003_closeout/` and verify `status=ready_for_handoff` plus valid escalation decision vocabulary.
4. Validate continuity echoes (`baseline_anchor`, `split_context`) and stage matrix truth (`s03_mitigation` ready, no readiness blocks) in closeout artifacts.
5. Update `.gsd/REQUIREMENTS.md` with S07 advancement evidence for R009, R010, R012, and R022, then re-run focused mitigation/closeout pytest suites to confirm contract and handoff stability.

## Must-Haves

- [ ] Canonical closeout rerun resolves to `ready_for_handoff` with `stage_rollup.readiness_block_stage_ids=[]`.
- [ ] Escalation decision remains evidence-based (`local_sufficient` or `overflow_required`) and not coupled to fairness-signal scarcity alone.
- [ ] Requirement traceability reflects S07 evidence without introducing status vocabulary drift.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_mitigation_contract.py tests/test_m003_track_e_mitigation_experiment.py tests/test_m003_mitigation_handoff_contract.py tests/test_m003_milestone_closeout_gate.py tests/test_m003_closeout_handoff_contract.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.mitigation_experiment --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --fairness-dir outputs/modeling/track_e/fairness_audit --output-dir outputs/modeling/track_e/mitigation_experiment`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY'
import json
from pathlib import Path

m = json.loads(Path('outputs/modeling/m003_closeout/manifest.json').read_text(encoding='utf-8'))
v = json.loads(Path('outputs/modeling/m003_closeout/validation_report.json').read_text(encoding='utf-8'))

assert m['status'] == 'ready_for_handoff', m['status']
assert m['compute_escalation_decision'] in {'local_sufficient', 'overflow_required'}
assert m['stage_rollup']['readiness_block_stage_ids'] == [], m['stage_rollup']
assert v['status'] == 'pass', v['status']
print('s07 closeout readiness verified')
PY`

## Observability Impact

- Signals added/changed: closeout readiness rollup must now clear S03 from `readiness_block_stage_ids`, and escalation payload remains explicit with runtime-capacity vs fairness-scarcity evidence separation.
- How a future agent inspects this: inspect `outputs/modeling/m003_closeout/{manifest.json,validation_report.json,stage_status_table.parquet,closeout_summary.md}` and run closeout handoff tests.
- Failure state exposed: any regression back to mitigation-blocked closeout is visible as non-empty readiness-block lists with stage-local reason codes.

## Inputs

- `tests/test_m003_milestone_closeout_gate.py` — Existing integrated closeout regression suite to tighten for S07 ready-path outcome.
- `tests/test_m003_closeout_handoff_contract.py` — Handoff contract assertions for stage coverage, continuity, and escalation semantics.
- `outputs/modeling/track_e/fairness_audit/manifest.json` — Upstream fairness readiness prerequisite from S06.
- `outputs/modeling/track_e/mitigation_experiment/manifest.json` — S03 status surface consumed by closeout stage rollup.
- `outputs/modeling/m003_closeout/manifest.json` — S05 closeout status/decision artifact to validate/update.
- `.gsd/REQUIREMENTS.md` — Active requirement traceability that must record S07 advancement evidence.

## Expected Output

- `tests/test_m003_milestone_closeout_gate.py` — Regression coverage locking S07-ready closeout propagation semantics.
- `tests/test_m003_closeout_handoff_contract.py` — Handoff assertions aligned to S07 ready-path expectations.
- `outputs/modeling/track_e/mitigation_experiment/manifest.json` — Regenerated mitigation manifest with `ready_for_closeout` status.
- `outputs/modeling/track_e/mitigation_experiment/validation_report.json` — Regenerated mitigation validation report with passing status.
- `outputs/modeling/m003_closeout/manifest.json` — Regenerated closeout manifest with `ready_for_handoff` status.
- `outputs/modeling/m003_closeout/validation_report.json` — Regenerated closeout validation report with passing readiness checks.
- `.gsd/REQUIREMENTS.md` — Updated requirement advancement notes linked to S07 evidence.
