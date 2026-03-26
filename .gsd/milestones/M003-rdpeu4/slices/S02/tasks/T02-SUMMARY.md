---
id: T02
parent: S02
milestone: M003-rdpeu4
provides:
  - Executable Track E fairness-audit runtime that consumes S01 intake, computes subgroup/disparity aggregates, and writes canonical success/failure diagnostics bundles
key_files:
  - src/modeling/track_e/fairness_audit.py
  - src/modeling/track_e/__init__.py
  - tests/test_m003_track_e_fairness_audit.py
  - outputs/modeling/track_e/fairness_audit/manifest.json
  - outputs/modeling/track_e/fairness_audit/validation_report.json
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
  - .gsd/milestones/M003-rdpeu4/slices/S02/S02-PLAN.md
key_decisions:
  - D029: when curated business context is missing, synthesize business rows from intake business_id values and continue subgroup derivation with unknown labels instead of blocking upstream
patterns_established:
  - Fail-closed gating for S01 readiness/schema paired with always-written canonical bundle files (including blocked_upstream fallback parquets + JSON diagnostics)
observability_surfaces:
  - outputs/modeling/track_e/fairness_audit/manifest.json and validation_report.json (phase timeline, row counts, threshold checks, upstream path echoes, blocking reason)
duration: 1h 45m
verification_result: passed
completed_at: 2026-03-23
blocker_discovered: false
---

# T02: Implement Track E model-aware fairness runtime from S01 intake with diagnostics bundle outputs

**Implemented the Track E fairness-audit CLI/runtime with S01 readiness gating, subgroup/disparity aggregate outputs, and deterministic `blocked_upstream` diagnostics.**

## What Happened

I followed TDD for this task: added `tests/test_m003_track_e_fairness_audit.py` first (green-path bundle build + blocked-upstream regressions), confirmed initial red on missing `src.modeling.track_e` module, then implemented `src/modeling/track_e/fairness_audit.py` and package wiring in `src/modeling/track_e/__init__.py`.

Runtime behavior implemented:
- CLI args: `--config`, `--intake-dir`, `--output-dir`.
- Upstream gate: requires S01 intake artifacts, `manifest.status == ready_for_fairness_audit`, `validation_report.status == pass`, and `validate_audit_intake_dataframe(...) == pass`.
- Subgroup context: reuses Track E subgroup utilities (`build_subgroup_definitions`) and review-count context; if `business.parquet` is missing, synthesizes business context from intake business IDs with unknown descriptive fields.
- Metrics bundle: computes aggregate subgroup metrics (`support_count`, `mean_y_true`, `mean_y_pred`, `mean_signed_error`, `mae`, `rmse`, `within_1_star_rate`) with `min_group_size` filtering.
- Disparity bundle: deterministic reference group per subgroup type (max support, then lexical tie-break), signed deltas, and boolean `exceeds_threshold` flags.
- Diagnostics: writes `manifest.json` + `validation_report.json` with phase timeline, row counts, threshold checks, split/baseline echoes, and upstream paths.
- Failure semantics: writes canonical `blocked_upstream` outputs with phase-local reasons (`load_intake_manifest`, `validate_intake`, `join_subgroups`, `write_bundle`) and missing-input details.

I also recorded decision D029 and appended a knowledge-log note covering the intentional empty-output behavior when `min_group_size` filters all groups in stripped worktrees.

## Verification

Task-level verification passed (`tests/test_m003_track_e_fairness_audit.py`, runtime command, and file existence checks).

Slice-level verification was run as required for this intermediate task:
- Runtime + contract checks passed.
- The combined 3-file pytest command partially failed because `tests/test_m003_fairness_audit_handoff_contract.py` is not created yet (T03 scope), which matches expected slice progression.

Observability impact was directly verified on both success and blocked paths:
- Success path JSON shows phase timeline, row counts, threshold checks, split/baseline echo, and upstream paths.
- Blocked path emits `manifest.status == blocked_upstream`, phase `load_intake_manifest`, and explicit `missing_inputs` payload.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -q` | 0 | ✅ pass | 8.05s |
| 2 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit` | 0 | ✅ pass | 5.78s |
| 3 | `test -f outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet && test -f outputs/modeling/track_e/fairness_audit/disparity_summary.parquet && test -f outputs/modeling/track_e/fairness_audit/manifest.json && test -f outputs/modeling/track_e/fairness_audit/validation_report.json` | 0 | ✅ pass | 0.02s |
| 4 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_fairness_audit_contract.py tests/test_m003_track_e_fairness_audit.py tests/test_m003_fairness_audit_handoff_contract.py -q` | 4 | ❌ fail | 1.92s |
| 5 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... m003 s02 fairness bundle verification script ... PY` | 0 | ✅ pass | 3.63s |
| 6 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python -m pytest tests/test_m003_track_e_fairness_audit.py -k blocked_upstream -q` | 0 | ✅ pass | 8.05s |
| 7 | `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26/.venv-local/bin/python - <<'PY' ... blocked_upstream observability probe ... PY` | 0 | ✅ pass | 5.33s |

## Diagnostics

Future agents can inspect the runtime via:
- `python -m src.modeling.track_e.fairness_audit --config configs/track_e.yaml --intake-dir outputs/modeling/track_a/audit_intake --output-dir outputs/modeling/track_e/fairness_audit`
- `outputs/modeling/track_e/fairness_audit/manifest.json`
- `outputs/modeling/track_e/fairness_audit/validation_report.json`
- `tests/test_m003_track_e_fairness_audit.py` (ready path + blocked-upstream failure surfaces)

Key payload fields to triage quickly:
- `manifest.status`, `manifest.phase`, `manifest.row_counts`, `manifest.threshold_checks`
- `validation_report.status`, `validation_report.phase`, `validation_report.phases[]`, `validation_report.missing_inputs`

## Deviations

- Minor local adaptation: although `data/curated/business.parquet` is listed as an upstream surface, this worktree can be stripped; runtime now synthesizes business context from intake `business_id` values so subgroup derivation remains deterministic and non-blocking while still enforcing S01 readiness/schema gates.

## Known Issues

- Slice-level combined pytest command still fails on missing `tests/test_m003_fairness_audit_handoff_contract.py`; this is expected until T03 is implemented.

## Files Created/Modified

- `src/modeling/track_e/fairness_audit.py` — added full S02 fairness runtime (CLI, gating, subgroup/disparity metrics, diagnostics, blocked-upstream bundle handling).
- `src/modeling/track_e/__init__.py` — added Track E modeling package export surface (`run`, `main`).
- `tests/test_m003_track_e_fairness_audit.py` — added runtime integration and blocked-upstream regression tests.
- `outputs/modeling/track_e/fairness_audit/subgroup_metrics.parquet` — generated canonical subgroup metrics artifact from runtime.
- `outputs/modeling/track_e/fairness_audit/disparity_summary.parquet` — generated canonical disparity summary artifact from runtime.
- `outputs/modeling/track_e/fairness_audit/manifest.json` — generated success manifest with row counts, threshold checks, and upstream context.
- `outputs/modeling/track_e/fairness_audit/validation_report.json` — generated check-level validation diagnostics and phase timeline.
- `.gsd/DECISIONS.md` — appended D029 documenting subgroup-context fallback behavior.
- `.gsd/KNOWLEDGE.md` — appended a runtime gotcha/pattern note for empty-but-valid outputs under high `min_group_size`.
- `.gsd/milestones/M003-rdpeu4/slices/S02/S02-PLAN.md` — marked T02 complete (`[x]`).
