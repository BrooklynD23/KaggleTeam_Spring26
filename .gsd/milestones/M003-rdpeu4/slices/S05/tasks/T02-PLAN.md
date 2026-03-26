---
estimated_steps: 6
estimated_files: 7
skills_used:
  - tdd-workflow
  - verification-loop
  - test
---

# T02: Implement integrated closeout runtime and conditional escalation decision gate

**Slice:** S05 — Integrated closeout gate with conditional compute-escalation decision
**Milestone:** M003-rdpeu4

## Description

Implement `src.modeling.m003_closeout_gate` as the canonical integrated rerun boundary that composes S01→S04 outputs, evaluates closeout readiness, and emits an explicit compute-escalation decision based on measured trigger evidence.

## Steps

1. Add `src/modeling/m003_closeout_gate.py` CLI with canonical args (`--track-a-config`, `--track-e-config`, `--predictions`, `--metrics`, `--candidate-metrics`, `--output-dir`) and expose entrypoint via `src/modeling/__init__.py`.
2. Execute canonical S01/S02/S03/S04 commands in sequence, then load each stage `manifest.json` + `validation_report.json` from canonical bundle paths and normalize stage rows for `stage_status_table.parquet`.
3. Implement status interpretation that prioritizes manifest/validation payloads (not command exit code), including proper handling for S03/S04 blocked-but-artifacts-written semantics.
4. Evaluate escalation triggers and non-triggers: mark `overflow_required` for runtime-capacity evidence (`runtime_within_budget == false`, OOM/timeout diagnostics, or configured ceiling breaches), and keep `local_sufficient` for fairness-signal scarcity branches (`blocked_insufficient_signal`, no-fairness-signal comparator decisions) without runtime-capacity evidence.
5. Write deterministic closeout bundle outputs (`stage_status_table.parquet`, `manifest.json`, `validation_report.json`, `closeout_summary.md`) with continuity echoes (`baseline_anchor`, `split_context`), stage-level hard/soft block flags, and trigger rationale.
6. Add `tests/test_m003_milestone_closeout_gate.py` integration coverage for ready/local-sufficient, blocked-upstream propagation, blocked-insufficient-signal local path, and overflow-required trigger path.

## Must-Haves

- [ ] Runtime emits all four closeout bundle files on every branch and preserves deterministic stage IDs.
- [ ] Escalation decision is derived from explicit trigger criteria and constrained to `local_sufficient` or `overflow_required`.
- [ ] Integration tests prove that manifest/validation statuses (not exit codes) drive closeout interpretation.

## Verification

- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_milestone_closeout_gate.py -q`
- `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.m003_closeout_gate --track-a-config configs/track_a.yaml --track-e-config configs/track_e.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --candidate-metrics tests/fixtures/m003_candidate_metrics.csv --output-dir outputs/modeling/m003_closeout`
- `test -f outputs/modeling/m003_closeout/stage_status_table.parquet && test -f outputs/modeling/m003_closeout/manifest.json && test -f outputs/modeling/m003_closeout/validation_report.json && test -f outputs/modeling/m003_closeout/closeout_summary.md`

## Observability Impact

- Signals added/changed: closeout manifest/validation outputs expose stage readiness matrix, hard/soft block flags, trigger evaluations, escalation decision, and phase-level diagnostics.
- How a future agent inspects this: rerun `python -m src.modeling.m003_closeout_gate ...` and inspect `outputs/modeling/m003_closeout/` artifacts plus `tests/test_m003_milestone_closeout_gate.py` branch coverage.
- Failure state exposed: blocked runs localize upstream vs signal vs runtime-capacity issues and preserve stage-level evidence required for escalation triage.

## Inputs

- `src/modeling/common/closeout_contract.py` — T01 contract constants and validators for stage table + manifest outputs.
- `src/modeling/track_a/audit_intake.py` — Canonical S01 command and bundle semantics.
- `src/modeling/track_e/fairness_audit.py` — Canonical S02 command and readiness contract.
- `src/modeling/track_e/mitigation_experiment.py` — Canonical S03 command and blocked-insufficient-signal semantics.
- `src/modeling/track_a/stronger_comparator.py` — Canonical S04 command and runtime/materiality gating signals.
- `configs/track_a.yaml` — Upstream Track A config required by S01/S04 command replay.
- `configs/track_e.yaml` — Upstream Track E config required by S02/S03 command replay.
- `tests/fixtures/m003_candidate_metrics.csv` — Canonical candidate metrics input for S04 replay inside closeout gate.

## Expected Output

- `src/modeling/m003_closeout_gate.py` — Integrated S05 closeout rerun + escalation decision runtime.
- `src/modeling/__init__.py` — Export surface updates for closeout runtime entrypoint.
- `tests/test_m003_milestone_closeout_gate.py` — Integration tests for closeout decision branches.
- `outputs/modeling/m003_closeout/stage_status_table.parquet` — Stage-by-stage readiness/diagnostic table for S05.
- `outputs/modeling/m003_closeout/manifest.json` — Closeout status + escalation decision payload.
- `outputs/modeling/m003_closeout/validation_report.json` — Check-level and phase-level closeout diagnostics.
- `outputs/modeling/m003_closeout/closeout_summary.md` — Human-readable closeout synopsis linked to canonical machine-readable artifacts.
