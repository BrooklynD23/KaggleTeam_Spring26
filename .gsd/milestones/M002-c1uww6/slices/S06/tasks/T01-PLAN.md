---
estimated_steps: 5
estimated_files: 2
skills_used:
  - tdd-workflow
  - test
  - coding-standards
  - verification-loop
---

# T01: Add cross-track M002 handoff verification harness

**Slice:** S06 — Integrated modeling handoff and milestone verification
**Milestone:** M002-c1uww6

## Description

Create the milestone-level pytest harness that composes all four modeling tracks into one enforceable handoff contract. This test file should verify cross-track artifact shape, summary semantics, and comparator truths so S06 has a single place to detect integration drift.

## Steps

1. Create `tests/test_m002_handoff_verification.py` with shared helpers for reading metrics, summaries, and config snapshots from `outputs/modeling/track_a`, `track_b`, `track_c`, and `track_d`.
2. Add assertions for required bundle files and minimum schema expectations per track (`metrics.csv`, `config_snapshot.json`, `summary.md`, and track-specific score artifacts).
3. Add cross-track semantic assertions for key truths: Track A model beats `naive_mean`; Track B test/ALL NDCG@10 ordering (`model > text_length_only > review_stars_only`); Track C summary keeps monitoring-only/non-forecast framing; Track D keeps D1 comparator metrics plus D2 optional/non-blocking gate semantics.
4. Reuse and/or align constants from `tests/test_m002_modeling_contract.py` to avoid duplicated marker drift between scaffold and integrated handoff tests.
5. Run the new test file, tighten assertion messages, and keep failures explicit enough for a fresh agent to localize drift quickly.

## Must-Haves

- [ ] `tests/test_m002_handoff_verification.py` exists and runs as a standalone pytest target.
- [ ] The test file asserts at least one contract condition for each owned requirement surface (Track A/B/C/D1 outputs).
- [ ] Failures clearly identify the track and artifact/phrase that drifted.

## Verification

- `python -m pytest tests/test_m002_handoff_verification.py -q`
- `python -m pytest tests/test_m002_modeling_contract.py tests/test_m002_handoff_verification.py -q`

## Inputs

- `tests/test_m002_modeling_contract.py` — Existing M002 scaffold-level contract patterns and marker constants
- `outputs/modeling/track_a/metrics.csv` — Track A comparator evidence surface
- `outputs/modeling/track_b/metrics.csv` — Track B ranking metric evidence surface
- `outputs/modeling/track_c/metrics.csv` — Track C monitoring metric evidence surface
- `outputs/modeling/track_d/metrics.csv` — Track D D1/comparator metric evidence surface
- `outputs/modeling/track_a/summary.md` — Track A handoff narrative markers
- `outputs/modeling/track_b/summary.md` — Track B snapshot-ranking narrative markers
- `outputs/modeling/track_c/summary.md` — Track C monitoring-only narrative markers
- `outputs/modeling/track_d/summary.md` — Track D D1-required / D2-optional narrative markers

## Expected Output

- `tests/test_m002_handoff_verification.py` — Integrated M002 handoff pytest harness
- `tests/test_m002_modeling_contract.py` — Optional shared-constant/helper alignment to avoid duplicate contract drift

## Observability Impact

- Signals changed: integrated cross-track handoff drift now fails in one place (`tests/test_m002_handoff_verification.py`) with track/artifact-specific assertion messages instead of scattered per-track checks.
- Future inspection path: run `python -m pytest tests/test_m002_handoff_verification.py -q` first, then inspect the named track bundle under `outputs/modeling/track_*/` and shared marker constants in `tests/test_m002_modeling_contract.py`.
- Newly visible failure state: missing artifacts, schema/key metric regressions, or summary phrase drift across Track A/B/C/D now surface as explicit pytest failures tagged to the owning track and contract clause.
