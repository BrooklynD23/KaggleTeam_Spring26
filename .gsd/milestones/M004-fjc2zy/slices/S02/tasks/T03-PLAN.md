---
estimated_steps: 5
estimated_files: 4
skills_used:
  - verification-loop
  - coding-standards
  - accessibility
---

# T03: Extend smoke/runbook verification for executive artifact parity

Close S02 with executable runtime parity checks that prove rendered executive story content matches generated artifacts in ready and blocked states.

1. Extend `scripts/showcase_smoke_check.py` to accept story artifact input and assert executive headings, section statuses, governance markers, and evidence pointer fields on the live page.
2. Add `showcase/tests/load-story.test.ts` coverage for loader fallback/normalization behavior.
3. Update `docs/showcase_local_runbook.md` with S02 command order (build intake, build story, run tests/build, run dev server, execute smoke check).
4. Ensure smoke output includes actionable PASS/FAIL labels tied to section/evidence fields for fast triage.

## Inputs

- `scripts/showcase_smoke_check.py`
- `docs/showcase_local_runbook.md`
- `outputs/showcase/intake/manifest.json`
- `outputs/showcase/story/sections.json`

## Expected Output

- `scripts/showcase_smoke_check.py`
- `showcase/tests/load-story.test.ts`
- `docs/showcase_local_runbook.md`
- `.gsd/milestones/M004-fjc2zy/slices/S02/S02-PLAN.md`

## Verification

npm --prefix showcase run test -- --run && python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000

## Observability Impact

Extends runtime smoke diagnostics so story-section/evidence drift is machine-detectable during local demos.
