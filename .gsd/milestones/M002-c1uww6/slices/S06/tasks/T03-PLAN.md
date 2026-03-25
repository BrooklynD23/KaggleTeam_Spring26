---
estimated_steps: 5
estimated_files: 6
skills_used:
  - verification-loop
  - debug-like-expert
  - test
---

# T03: Execute integrated rerun gate and capture S06 UAT evidence

**Slice:** S06 — Integrated modeling handoff and milestone verification
**Milestone:** M002-c1uww6

## Description

Run the authoritative integrated verification sequence across all four modeling tracks and the new handoff harness, then capture reproducible command evidence in `S06-UAT.md`. This task converts the slice from “planned closure” to “proven closure.”

## Steps

1. Run the expanded pytest gate including `tests/test_m002_handoff_verification.py` and existing track-level/modeling-contract suites.
2. Rerun all four baseline CLIs to regenerate `outputs/modeling/track_a`, `track_b`, `track_c`, and `track_d` artifacts from current code.
3. Execute a semantic assertion script over regenerated artifacts to confirm cross-track truth statements and doc-hygiene checks from T02.
4. Write `S06-UAT.md` with exact commands, exit outcomes, key metrics, and failure diagnostics so a fresh agent can replay the integrated gate.
5. Re-run the full integrated command chain once after writing UAT notes and update any stale evidence if outputs changed.

## Must-Haves

- [ ] Integrated pytest gate is green with the new handoff harness included.
- [ ] All four baseline CLIs execute successfully and refresh modeling artifacts.
- [ ] `S06-UAT.md` contains replayable command evidence and not just narrative claims.

## Verification

- `python -m pytest tests/test_track_a_baseline_model.py tests/test_track_b_baseline_model.py tests/test_track_c_baseline_model.py tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py tests/test_m002_handoff_verification.py -q`
- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && python -m src.modeling.track_b.baseline --config configs/track_b.yaml && python -m src.modeling.track_c.baseline --config configs/track_c.yaml && python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
- `rg -n "test_m002_handoff_verification|track_a.baseline|track_b.baseline|track_c.baseline|track_d.baseline" .gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md`

## Observability Impact

- Signals added/changed: integrated gate outcomes recorded in `S06-UAT.md` and refreshed per-track `metrics.csv` artifacts under `outputs/modeling/track_*/`.
- How a future agent inspects this: rerun the integrated command chain from `S06-UAT.md` and diff current outputs against the recorded evidence.
- Failure state exposed: failing tests, baseline runtime errors, and contract-drift assertions are captured with command-level context in `S06-UAT.md`.

## Inputs

- `tests/test_m002_handoff_verification.py` — Cross-track integration assertions from T01
- `tests/test_m002_modeling_contract.py` — Existing M002 scaffold checks
- `.gsd/milestones/M002-c1uww6/slices/S02/S02-SUMMARY.md` — Dependency-slice handoff summary from T02
- `.gsd/milestones/M002-c1uww6/slices/S03/S03-SUMMARY.md` — Dependency-slice handoff summary from T02
- `.gsd/milestones/M002-c1uww6/slices/S04/S04-SUMMARY.md` — Dependency-slice handoff summary from T02
- `.gsd/milestones/M002-c1uww6/slices/S05/S05-SUMMARY.md` — Dependency-slice handoff summary from T02
- `configs/track_a.yaml` — Track A runtime config
- `configs/track_b.yaml` — Track B runtime config
- `configs/track_c.yaml` — Track C runtime config
- `configs/track_d.yaml` — Track D runtime config

## Expected Output

- `.gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md` — Integrated command evidence and replay instructions
- `outputs/modeling/track_a/metrics.csv` — Refreshed Track A metrics from integrated rerun
- `outputs/modeling/track_b/metrics.csv` — Refreshed Track B metrics from integrated rerun
- `outputs/modeling/track_c/metrics.csv` — Refreshed Track C metrics from integrated rerun
- `outputs/modeling/track_d/metrics.csv` — Refreshed Track D metrics from integrated rerun
- `tests/test_m002_handoff_verification.py` — Finalized assertions after integrated rerun adjustments (if needed)
