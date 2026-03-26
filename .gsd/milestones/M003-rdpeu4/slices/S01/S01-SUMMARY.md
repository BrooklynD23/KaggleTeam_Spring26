---
id: S01
parent: M003-rdpeu4
milestone: M003-rdpeu4
provides:
  - Reproducible Track A upstream scored-intake builder (`python -m src.modeling.track_a.audit_intake`) that emits a canonical handoff bundle under `outputs/modeling/track_a/audit_intake/`.
  - Machine-validated intake schema contract with deterministic diagnostics for missing columns, nulls, duplicate keys, and forbidden text/demographic column families.
  - Downstream handoff guardrails (tests + docs + UAT) that lock one intake path and readiness status for S02/S03/S04 consumption.
requires:
  - slice: M002-c1uww6/S06
    provides: Track A baseline prediction/metric artifacts and contract-tested upstream modeling surfaces.
affects:
  - M003-rdpeu4/S02
  - M003-rdpeu4/S03
  - M003-rdpeu4/S04
  - M003-rdpeu4/S05
  - M004-fjc2zy
key_files:
  - src/modeling/common/audit_intake_contract.py
  - src/modeling/common/__init__.py
  - src/modeling/track_a/audit_intake.py
  - src/modeling/track_a/__init__.py
  - src/modeling/README.md
  - tests/test_m003_audit_intake_contract.py
  - tests/test_m003_track_a_audit_intake.py
  - tests/test_m003_intake_handoff_contract.py
  - .gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md
  - outputs/modeling/track_a/audit_intake/scored_intake.parquet
  - outputs/modeling/track_a/audit_intake/manifest.json
  - outputs/modeling/track_a/audit_intake/validation_report.json
key_decisions:
  - D026: Keep one canonical intake handoff surface at `outputs/modeling/track_a/audit_intake/` with fixed artifact names and CLI entrypoint.
  - D027: Use `review_id` as primary key, `business_id` as subgroup join key, and centralized forbidden text/demographic column-family checks.
patterns_established:
  - Intake runtime writes machine-readable diagnostics JSON on both success and failure (`ready_for_fairness_audit` vs `blocked_upstream`) with explicit phase timeline.
  - Canonical scored output is normalized to required contract columns and written deterministically sorted by `review_id`.
  - Downstream slices consume one fixed intake bundle path rather than rediscovering paths/columns ad hoc.
observability_surfaces:
  - outputs/modeling/track_a/audit_intake/manifest.json
  - outputs/modeling/track_a/audit_intake/validation_report.json
  - tests/test_m003_audit_intake_contract.py
  - tests/test_m003_track_a_audit_intake.py
  - tests/test_m003_intake_handoff_contract.py
  - src/modeling/README.md
duration: 2h35m
verification_result: passed
completed_at: 2026-03-23
---

# S01: Upstream audit-intake contract on reproducible scored artifacts

**S01 closed successfully.** The slice now provides a reproducible, validated upstream scored-intake bundle for M003 fairness/mitigation/comparator work with explicit failure visibility and deterministic downstream handoff wiring.

## What Happened

S01 delivered all three planned tasks and integrated them into one replayable intake contract:

1. **T01 contract layer:** added the shared `audit_intake_contract` module with schema versioning, required columns, subgroup join keys, non-null/uniqueness checks, forbidden text/demographic family checks, and machine-readable check-level diagnostics.
2. **T02 runtime layer:** implemented `src.modeling.track_a.audit_intake` CLI that loads Track A predictions + metrics, joins context from `review_fact`, resolves split context, validates intake, and writes canonical bundle outputs.
3. **T03 handoff layer:** added downstream handoff regression coverage and canonical docs/UAT so S02/S03/S04 can consume one authoritative intake surface without path/schema guesswork.

As the slice closer, I reran the full slice verification gate end-to-end, confirmed observability signals, updated requirement notes for R009/R010 prerequisite progress, refreshed project/knowledge state, and marked S01 complete in the M003 roadmap.

## Verification

All slice-plan verification checks passed in this worktree (using the project interpreter path from knowledge log):

| # | Command | Result |
|---|---|---|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_audit_intake_contract.py tests/test_m003_track_a_audit_intake.py tests/test_m003_intake_handoff_contract.py` | ✅ 10 passed |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_a.audit_intake --config configs/track_a.yaml --predictions outputs/modeling/track_a/predictions_test.parquet --metrics outputs/modeling/track_a/metrics.csv --output-dir outputs/modeling/track_a/audit_intake` | ✅ exit 0 |
| 3 | Verification snippet from S01 plan (`required` columns + `manifest.status == ready_for_fairness_audit` + `validation.status == pass`) | ✅ pass |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_audit_intake.py -k missing_predictions_emits_diagnostics` | ✅ pass |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_a_audit_intake.py -k malformed_predictions_schema_emits_validation_failure` | ✅ pass |
| 6 | Observability assertion snippet (phase timeline + row-count alignment + required phases present) | ✅ pass |

## Observability / Diagnostics Confirmed

The declared S01 observability surfaces are live and actionable:

- `manifest.json` includes `status`, `phase`, `row_count`, `split_context`, `baseline_anchor`, and upstream path echoes.
- `validation_report.json` includes check-level validation details, phase timeline (`load_predictions` → `write_bundle`), null/duplicate diagnostics, and failure-phase visibility.
- Failure-path behavior is explicit and machine-readable (`blocked_upstream`, missing-input lists, phase markers), not log-only.

## Requirements Advanced

- **R009 (active, mapped):** now includes explicit S01 prerequisite evidence: canonical Track A intake bundle with readiness/diagnostic contract for downstream fairness and mitigation slices.
- **R010 (active, mapped):** now includes explicit S01 prerequisite evidence: baseline metric/runtime anchors (`baseline_anchor`) for S04 materiality-gate comparisons.

## Requirements Validated

- none (S01 is an integration prerequisite slice; fairness/mitigation/materiality closures remain owned by S02/S03/S04/S05).

## Deviations

- Runtime verification used `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python` because default `/usr/bin/python3` in this harness may not include pytest/pip.

## Known Limitations

- S01 does **not** compute fairness disparities or mitigation deltas.
- S01 does **not** make stronger-model adoption decisions.
- These remain downstream obligations (S02–S05).

## Follow-ups for Next Slices

1. **S02:** consume `outputs/modeling/track_a/audit_intake/scored_intake.parquet` + manifest/validation JSON directly; treat `ready_for_fairness_audit` as intake gate.
2. **S03:** use S02 metrics plus S01 baseline anchors for pre/post mitigation reporting.
3. **S04:** reuse `baseline_anchor` runtime/metric context for materiality gate decisions.
4. **S05:** integrate this intake contract into closeout rerun and escalation decision artifacts.

## Files Created/Modified

- `src/modeling/common/audit_intake_contract.py`
- `src/modeling/common/__init__.py`
- `src/modeling/__init__.py`
- `src/modeling/track_a/audit_intake.py`
- `src/modeling/track_a/__init__.py`
- `src/modeling/README.md`
- `tests/test_m003_audit_intake_contract.py`
- `tests/test_m003_track_a_audit_intake.py`
- `tests/test_m003_intake_handoff_contract.py`
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-UAT.md`
- `.gsd/milestones/M003-rdpeu4/slices/S01/S01-SUMMARY.md`
- `.gsd/milestones/M003-rdpeu4/M003-rdpeu4-ROADMAP.md` (S01 marked complete)
- `.gsd/REQUIREMENTS.md` (R009/R010 prerequisite evidence notes)
- `.gsd/PROJECT.md` (current-state refresh)
- `.gsd/KNOWLEDGE.md` (audit-intake failure-diagnostics gotcha)

## Forward Intelligence

### What the next slice should know
S01 locked a single upstream intake contract and path. If S02 fails, inspect intake manifest/validation JSON first before modifying fairness code.

### What is most fragile
- Upstream input availability (`predictions`, `metrics`, `review_fact`) and required schema columns (`y_pred`, etc.).
- Any drift from canonical output path or status semantics (`ready_for_fairness_audit`, `blocked_upstream`) will break downstream assumptions.

### Authoritative triage surfaces
- `outputs/modeling/track_a/audit_intake/manifest.json`
- `outputs/modeling/track_a/audit_intake/validation_report.json`
- `tests/test_m003_track_a_audit_intake.py`
- `tests/test_m003_intake_handoff_contract.py`
