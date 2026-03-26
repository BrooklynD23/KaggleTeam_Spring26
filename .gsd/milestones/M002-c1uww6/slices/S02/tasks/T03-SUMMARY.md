---
id: T03
parent: S02
milestone: M002-c1uww6
provides:
  - Verified Track A baseline quality against the naive-mean comparator and tightened the audit-handoff summary markers to match the slice verification contract
key_files:
  - src/modeling/track_a/baseline.py
  - .gsd/milestones/M002-c1uww6/slices/S02/tasks/T03-PLAN.md
  - outputs/modeling/track_a/summary.md
  - outputs/modeling/track_a/metrics.csv
key_decisions:
  - Keep the Track A baseline summary generator emitting explicit "Known limitations" and "M003 audit suitability" sections so audit-handoff verification stays coupled to the real CLI output rather than ad hoc prose edits.
patterns_established:
  - When a slice verification command depends on specific artifact wording, make the producing CLI emit those markers directly and verify against the regenerated artifact bundle, not a hand-edited summary.
observability_surfaces:
  - outputs/modeling/track_a/metrics.csv
  - outputs/modeling/track_a/summary.md
  - outputs/modeling/track_a/config_snapshot.json
  - python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000
  - python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py
duration: 34m
verification_result: passed
completed_at: 2026-03-23T08:46:30Z
blocker_discovered: false
---

# T03: Verify Track A baseline quality against the naïve comparator

**Verified the Track A baseline clears the naive-mean MAE bar and regenerated the audit handoff summary with explicit limitation and M003 suitability markers.**

## What Happened

I first read the existing `outputs/modeling/track_a/metrics.csv`, `summary.md`, and `config_snapshot.json` surfaces and confirmed the current baseline already beat `naive_mean` on test MAE.

The one substantive mismatch was in the summary contract: the artifact was honest, but its headings did not match the task plan’s planned inspection strings. I updated `src/modeling/track_a/baseline.py` so the real CLI now emits explicit `## Known limitations` and `## M003 audit suitability` sections while preserving the required leakage-guardrail language, cap disclosure, and preferred-default audit-target framing.

I also patched `.gsd/milestones/M002-c1uww6/slices/S02/tasks/T03-PLAN.md` to add the missing `## Observability Impact` section required by the pre-flight note.

After that, I reran the Track A baseline CLI to regenerate the worktree-local artifact bundle, verified the comparator result again, and confirmed the summary/config pair still exposes the banned-feature and audit-target guardrails the slice expects.

## Verification

I ran the full slice pytest gate, reran the real Track A baseline entrypoint with the capped train/eval settings, asserted that test MAE for `hist_gradient_boosting` beats `naive_mean`, and checked the regenerated summary/config artifacts for both the explicit limitation/audit-target markers and the leakage guardrail strings.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py` | 0 | ✅ pass | 14.6s |
| 2 | `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && test -f outputs/modeling/track_a/summary.md && test -f outputs/modeling/track_a/metrics.csv && test -f outputs/modeling/track_a/config_snapshot.json && test -f outputs/modeling/track_a/figures/predicted_vs_actual_test.png` | 0 | ✅ pass | 20.1s |
| 3 | `python - <<'PY' ... assert hist_gradient_boosting test MAE < naive_mean test MAE ... PY` | 0 | ✅ pass | 13.8s |
| 4 | `python - <<'PY' ... assert summary contains "Known limitations", "M003 audit suitability", and "Track A remains the preferred default" ... PY` | 0 | ✅ pass | 10.7s |
| 5 | `python - <<'PY' ... assert summary/config expose excluded banned fields, preferred default M003 audit target text, and banned_features ... PY` | 0 | ✅ pass | 3.6s |

## Diagnostics

Future agents can inspect this task by rerunning:

- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
- `python -m pytest tests/test_track_a_baseline_model.py tests/test_m002_modeling_contract.py`
- `python - <<'PY'
import pandas as pd
metrics = pd.read_csv('outputs/modeling/track_a/metrics.csv')
model_mae = metrics.loc[(metrics.model_name == 'hist_gradient_boosting') & (metrics.split_name == 'test'), 'mae'].iloc[0]
mean_mae = metrics.loc[(metrics.model_name == 'naive_mean') & (metrics.split_name == 'test'), 'mae'].iloc[0]
print({'model_mae': model_mae, 'naive_mean_mae': mean_mae, 'beats_naive_mean': model_mae < mean_mae})
PY`

Primary inspection surfaces remain:

- `outputs/modeling/track_a/metrics.csv` for comparator regressions
- `outputs/modeling/track_a/summary.md` for the explicit limitation and audit-target handoff narrative
- `outputs/modeling/track_a/config_snapshot.json` for banned fields, split provenance, and cap settings

If this task regresses later, the likely failure modes are:

- the baseline no longer beating `naive_mean` on test MAE
- the CLI summary dropping the explicit `Known limitations` / `M003 audit suitability` markers
- the config snapshot losing `banned_features` or other audit-reproducibility metadata

## Deviations

- The task plan specified `rg` for the summary marker check, but `rg` is not installed in this auto-mode environment, so I used a Python text assertion against the same expected markers instead.
- I made a small production-code change in `src/modeling/track_a/baseline.py` even though T03 was primarily a verification task, because the live CLI output needed to match the verification contract rather than relying on a stale or hand-edited summary artifact.

## Known Issues

- The capped Track A baseline still trails `naive_business_prior_avg` on test MAE even though it comfortably beats `naive_mean`. That does not block S02’s stated quality bar, but it remains an important downstream comparator for later modeling slices.

## Files Created/Modified

- `src/modeling/track_a/baseline.py` — updated the real summary generator to emit explicit limitation and M003 audit-suitability sections in the shipped artifact bundle
- `.gsd/milestones/M002-c1uww6/slices/S02/tasks/T03-PLAN.md` — added the missing `## Observability Impact` section required by the task pre-flight note
- `.gsd/milestones/M002-c1uww6/slices/S02/S02-PLAN.md` — marked T03 complete in the slice checklist
- `.gsd/KNOWLEDGE.md` — captured the worktree-path/runtime-artifact resolution gotcha discovered during verification
- `outputs/modeling/track_a/summary.md` — regenerated the Track A audit handoff summary with explicit limitation and audit-target markers
- `outputs/modeling/track_a/metrics.csv` — reconfirmed the comparator metrics surface used for the test-MAE quality gate
- `outputs/modeling/track_a/config_snapshot.json` — reconfirmed the leakage-guardrail and reproducibility metadata surface
