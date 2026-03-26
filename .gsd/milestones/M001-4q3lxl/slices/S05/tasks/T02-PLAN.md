---
estimated_steps: 4
estimated_files: 6
skills_used:
  - article-writing
  - coding-standards
  - review
  - verification-loop
---

# T02: Repair stale S04 handoff artifacts and close requirement drift

**Slice:** S05 — Integrated local handoff verification
**Milestone:** M001-4q3lxl

## Description

Remove the fake-complete state from the milestone handoff surface. This task rewrites the S04 doctor placeholders into real compressed completion artifacts, updates `R004` to match the already-passing S04 contract, and extends the milestone harness so those fixes cannot silently regress.

## Steps

1. Read the S04 task summaries, the current placeholder `S04-SUMMARY.md` and `S04-UAT.md`, and the `R004` section in `.gsd/REQUIREMENTS.md` so the rewrite reflects actual slice output and proof rather than generic filler.
2. Rewrite `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` and `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md` as real milestone artifacts grounded in `T01-SUMMARY.md`, `T02-SUMMARY.md`, and the passing S04 verification commands.
3. Update `.gsd/REQUIREMENTS.md` so `R004` moves from active to validated with concrete proof tied to `tests/test_trust_narrative_workflow.py` and the integrated S05 handoff surface.
4. Extend `tests/test_m001_handoff_verification.py` to fail on placeholder language in the S04 artifacts or stale `R004` status, then rerun the S04 + S05 contract tests until they pass together.

## Must-Haves

- [ ] `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` is a real compressed slice summary with actual deliverables, proof, diagnostics, and forward intelligence.
- [ ] `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md` is a real UAT/checklist artifact rather than a doctor placeholder.
- [ ] `.gsd/REQUIREMENTS.md` records `R004` as validated with concrete proof language, not just “mapped.”
- [ ] `tests/test_m001_handoff_verification.py` now protects against placeholder regression and stale requirement status.

## Verification

- `python -m pytest tests/test_trust_narrative_workflow.py tests/test_m001_handoff_verification.py -q`
- `python - <<'PY'
from pathlib import Path
for path in [
    Path('.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md'),
    Path('.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md'),
]:
    text = path.read_text(encoding='utf-8')
    assert 'Recovery placeholder' not in text, path
    assert 'doctor-created placeholder' not in text, path
requirements = Path('.gsd/REQUIREMENTS.md').read_text(encoding='utf-8')
section = requirements.split('### R004', 1)[1].split('### ', 1)[0]
assert 'Status: validated' in section
print('S04 handoff artifacts are real and R004 is validated')
PY`

## Inputs

- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` — placeholder artifact to replace
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md` — placeholder artifact to replace
- `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T01-SUMMARY.md` — authoritative source for S04 task-one delivery and diagnostics
- `.gsd/milestones/M001-4q3lxl/slices/S04/tasks/T02-SUMMARY.md` — authoritative source for S04 task-two delivery and diagnostics
- `.gsd/REQUIREMENTS.md` — requirement status source of truth
- `tests/test_trust_narrative_workflow.py` — current S04 proof surface
- `tests/test_m001_handoff_verification.py` — milestone harness to extend from T01

## Expected Output

- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md` — repaired real S04 slice summary
- `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md` — repaired real S04 UAT/checklist artifact
- `.gsd/REQUIREMENTS.md` — updated with validated `R004` proof
- `tests/test_m001_handoff_verification.py` — extended to guard against placeholder and requirement-state drift

## Observability Impact

- The milestone handoff harness gains direct failure visibility for two previously silent drift classes: stale S04 placeholder language and stale `R004` requirement status.
- Future agents can inspect the repaired handoff state through `.gsd/milestones/M001-4q3lxl/slices/S04/S04-SUMMARY.md`, `.gsd/milestones/M001-4q3lxl/slices/S04/S04-UAT.md`, `.gsd/REQUIREMENTS.md`, and `tests/test_m001_handoff_verification.py` without re-deriving S04 completion from task logs alone.
- Failure states become concrete and machine-checkable: pytest will name the exact S04 artifact or requirement section that drifted, while the requirement proof text now points back to `tests/test_trust_narrative_workflow.py` and the integrated S05 milestone harness as the authoritative validation surfaces.
