# S06: Integrated modeling handoff and milestone verification

**Goal:** Prove that Track A, Track B, Track C, and Track D1 baselines hold together under one executable handoff contract, while repairing slice handoff docs/state surfaces so a fresh agent can continue into M003 without cleanup archaeology.
**Demo:** A single integrated verification run passes end-to-end (all four baseline CLIs + cross-track pytest harness), S02–S05 handoff docs are complete and non-placeholder, and M002 state surfaces explicitly show R005–R008 validated with Track A as the default M003 audit target.

## Must-Haves

- S06 closes **R005, R006, R007, and R008** at milestone integration level by proving cross-track artifact contract truth in one gate.
- S06 supports **R009** by preserving a clean fairness-audit handoff surface with Track A explicitly preferred by default and Track D D1 evidence still available.
- S06 supports **R012** by shipping complete cross-track handoff docs (S02–S05 summaries/UAT + S06 UAT/summary) that narrate prediction, surfacing, monitoring, and onboarding coherently.
- No placeholder UAT content remains in S02–S05, and missing slice summaries are backfilled with real command evidence.
- M002 state surfaces (`.gsd/PROJECT.md`, `.gsd/REQUIREMENTS.md`, roadmap checkbox state) reflect current integrated modeling truth.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `python -m pytest tests/test_track_a_baseline_model.py tests/test_track_b_baseline_model.py tests/test_track_c_baseline_model.py tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py tests/test_m002_handoff_verification.py -q`
- `python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000`
- `python -m src.modeling.track_b.baseline --config configs/track_b.yaml`
- `python -m src.modeling.track_c.baseline --config configs/track_c.yaml`
- `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`
- `python - <<'PY'
from pathlib import Path
import re

root = Path('.')
required_summaries = [
    root / '.gsd/milestones/M002-c1uww6/slices/S02/S02-SUMMARY.md',
    root / '.gsd/milestones/M002-c1uww6/slices/S03/S03-SUMMARY.md',
    root / '.gsd/milestones/M002-c1uww6/slices/S04/S04-SUMMARY.md',
    root / '.gsd/milestones/M002-c1uww6/slices/S05/S05-SUMMARY.md',
]
required_uat = [
    root / '.gsd/milestones/M002-c1uww6/slices/S02/S02-UAT.md',
    root / '.gsd/milestones/M002-c1uww6/slices/S03/S03-UAT.md',
    root / '.gsd/milestones/M002-c1uww6/slices/S04/S04-UAT.md',
    root / '.gsd/milestones/M002-c1uww6/slices/S05/S05-UAT.md',
    root / '.gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md',
]
for path in required_summaries + required_uat:
    assert path.exists(), f'missing file: {path}'
    text = path.read_text(encoding='utf-8').strip()
    assert text, f'empty file: {path}'
for path in required_uat[:-1]:
    text = path.read_text(encoding='utf-8')
    assert 'Recovery placeholder' not in text, f'placeholder still present: {path}'

requirements = (root / '.gsd/REQUIREMENTS.md').read_text(encoding='utf-8')
for req in ['R005', 'R006', 'R007', 'R008']:
    block = re.search(rf'### {req}.*?(?=\n### R|\n## |\Z)', requirements, re.S)
    assert block, f'missing requirement block: {req}'
    assert 'Status: validated' in block.group(0), f'{req} not validated'

roadmap = (root / '.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md').read_text(encoding='utf-8')
assert '- [x] **S06: Integrated modeling handoff and milestone verification**' in roadmap
print('S06 handoff docs, requirement status, and roadmap closure verified')
PY`

## Observability / Diagnostics

- Runtime signals: per-track modeling bundles under `outputs/modeling/track_a/`, `outputs/modeling/track_b/`, `outputs/modeling/track_c/`, and `outputs/modeling/track_d/` plus integrated assertions in `tests/test_m002_handoff_verification.py`.
- Inspection surfaces: integrated pytest gate, four baseline CLI entrypoints, and `S06-UAT.md` command evidence.
- Failure visibility: contract drift surfaces as explicit pytest assertion failures (missing artifacts, phrase/metric regressions, placeholder docs, state mismatch) and runtime CLI errors.
- Redaction constraints: no raw review text in generated summaries, UAT docs, or modeling artifacts.

## Integration Closure

- Upstream surfaces consumed: `src/modeling/README.md`, `tests/test_m002_modeling_contract.py`, `outputs/modeling/track_*/` artifact bundles, and S02–S05 task summaries.
- New wiring introduced in this slice: milestone-level integration harness `tests/test_m002_handoff_verification.py` and clean handoff docs/state surfaces for M003 intake.
- What remains before the milestone is truly usable end-to-end: nothing inside M002 after this slice gate is green; downstream work proceeds from S06 handoff surfaces.

## Tasks

- [x] **T01: Add cross-track M002 handoff verification harness** `est:1h`
  - Why: S06 needs one executable contract that proves all four baseline tracks agree under shared handoff expectations.
  - Files: `tests/test_m002_handoff_verification.py`, `tests/test_m002_modeling_contract.py`
  - Do: Create a dedicated integration pytest module that asserts required artifact files/columns/summary markers for Track A/B/C/D1 and key comparator truths (A beats `naive_mean`, B test ALL NDCG ordering, C monitoring-only framing, D1 comparator + D2 optional gate), reusing helper patterns from existing modeling-contract tests.
  - Verify: `python -m pytest tests/test_m002_handoff_verification.py -q`
  - Done when: the new harness passes against current artifacts and fails loudly on cross-track contract drift.
- [x] **T02: Backfill S02–S05 summaries and replace placeholder UAT docs** `est:1h 30m`
  - Why: Fresh-agent handoff is currently broken because dependency slices still have missing summaries and placeholder UAT files.
  - Files: `.gsd/milestones/M002-c1uww6/slices/S02/S02-SUMMARY.md`, `.gsd/milestones/M002-c1uww6/slices/S03/S03-SUMMARY.md`, `.gsd/milestones/M002-c1uww6/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M002-c1uww6/slices/S05/S05-SUMMARY.md`, `.gsd/milestones/M002-c1uww6/slices/S02/S02-UAT.md`, `.gsd/milestones/M002-c1uww6/slices/S03/S03-UAT.md`, `.gsd/milestones/M002-c1uww6/slices/S04/S04-UAT.md`, `.gsd/milestones/M002-c1uww6/slices/S05/S05-UAT.md`
  - Do: Convert S02–S05 task evidence into real slice summary artifacts (including forward-intelligence notes), and replace each placeholder UAT with concrete preconditions, smoke checks, and failure signals tied to actual modeling outputs/commands.
  - Verify: `python - <<'PY'
from pathlib import Path
for sid in ['S02','S03','S04','S05']:
    summary = Path(f'.gsd/milestones/M002-c1uww6/slices/{sid}/{sid}-SUMMARY.md')
    uat = Path(f'.gsd/milestones/M002-c1uww6/slices/{sid}/{sid}-UAT.md')
    assert summary.exists() and summary.read_text(encoding='utf-8').strip()
    text = uat.read_text(encoding='utf-8')
    assert 'Recovery placeholder' not in text
    assert '## Smoke Test' in text and '## Failure Signals' in text
print('S02-S05 summary/UAT handoff docs verified')
PY`
  - Done when: all four dependency slices expose non-placeholder summary/UAT artifacts that a new executor can run without reconstructing context from task-level history.
- [x] **T03: Execute integrated rerun gate and capture S06 UAT evidence** `est:1h 10m`
  - Why: S06 closes only with fresh end-to-end proof that runtime outputs and the new integration harness agree.
  - Files: `.gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md`, `outputs/modeling/track_a/metrics.csv`, `outputs/modeling/track_b/metrics.csv`, `outputs/modeling/track_c/metrics.csv`, `outputs/modeling/track_d/metrics.csv`, `tests/test_m002_handoff_verification.py`
  - Do: Run the authoritative integrated sequence (pytest gate + all four baseline CLIs), resolve any drift, and document command evidence, pass/fail outcomes, and notable caveats in `S06-UAT.md` with explicit references to the generated artifacts.
  - Verify: `python -m pytest tests/test_track_a_baseline_model.py tests/test_track_b_baseline_model.py tests/test_track_c_baseline_model.py tests/test_track_d_baseline_model.py tests/test_track_d_cohorts.py tests/test_label_scheme_ranking.py tests/test_feasibility_signoff.py tests/test_track_c_common.py tests/test_m002_modeling_contract.py tests/test_m002_handoff_verification.py -q && python -m src.modeling.track_a.baseline --config configs/track_a.yaml --train-cap 100000 --eval-cap 200000 && python -m src.modeling.track_b.baseline --config configs/track_b.yaml && python -m src.modeling.track_c.baseline --config configs/track_c.yaml && python -m src.modeling.track_d.baseline --config configs/track_d.yaml && rg -n "test_m002_handoff_verification|track_a.baseline|track_b.baseline|track_c.baseline|track_d.baseline" .gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md`
  - Done when: integrated commands are green in one run and `S06-UAT.md` records the executed evidence clearly enough for independent replay.
- [x] **T04: Finalize M002 closure state and milestone handoff summary** `est:55m`
  - Why: M002 cannot be considered complete while requirements/project/roadmap surfaces still describe pre-baseline or provisional state.
  - Files: `.gsd/REQUIREMENTS.md`, `.gsd/PROJECT.md`, `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`, `.gsd/milestones/M002-c1uww6/slices/S06/S06-SUMMARY.md`
  - Do: Update requirements to validate R005–R008 with concrete verification references, refresh project current-state language to reflect integrated modeling completion, mark S06 complete in roadmap, and author `S06-SUMMARY.md` with forward-intelligence handoff guidance for M003.
  - Verify: `python - <<'PY'
from pathlib import Path
import re
requirements = Path('.gsd/REQUIREMENTS.md').read_text(encoding='utf-8')
for req in ['R005','R006','R007','R008']:
    block = re.search(rf'### {req}.*?(?=\n### R|\n## |\Z)', requirements, re.S)
    assert block and 'Status: validated' in block.group(0)
roadmap = Path('.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md').read_text(encoding='utf-8')
assert '- [x] **S06: Integrated modeling handoff and milestone verification**' in roadmap
summary = Path('.gsd/milestones/M002-c1uww6/slices/S06/S06-SUMMARY.md')
assert summary.exists() and summary.read_text(encoding='utf-8').strip()
print('M002 closure state verified')
PY`
  - Done when: requirements, project, roadmap, and S06 summary agree on post-integration truth and downstream teams can start M003 from those artifacts alone.

## Files Likely Touched

- `tests/test_m002_handoff_verification.py`
- `tests/test_m002_modeling_contract.py`
- `.gsd/milestones/M002-c1uww6/slices/S02/S02-SUMMARY.md`
- `.gsd/milestones/M002-c1uww6/slices/S03/S03-SUMMARY.md`
- `.gsd/milestones/M002-c1uww6/slices/S04/S04-SUMMARY.md`
- `.gsd/milestones/M002-c1uww6/slices/S05/S05-SUMMARY.md`
- `.gsd/milestones/M002-c1uww6/slices/S02/S02-UAT.md`
- `.gsd/milestones/M002-c1uww6/slices/S03/S03-UAT.md`
- `.gsd/milestones/M002-c1uww6/slices/S04/S04-UAT.md`
- `.gsd/milestones/M002-c1uww6/slices/S05/S05-UAT.md`
- `.gsd/milestones/M002-c1uww6/slices/S06/S06-UAT.md`
- `.gsd/milestones/M002-c1uww6/slices/S06/S06-SUMMARY.md`
- `.gsd/REQUIREMENTS.md`
- `.gsd/PROJECT.md`
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`
