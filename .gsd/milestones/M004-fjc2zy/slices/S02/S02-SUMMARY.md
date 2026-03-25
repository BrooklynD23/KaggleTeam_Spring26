---
id: S02
parent: M004-fjc2zy
milestone: M004-fjc2zy
provides:
  - Canonical executive story artifact contract and generator outputs for downstream drill-down/report/deck parity work
  - Typed runtime story loader with deterministic fallback semantics
  - Smoke-check parity assertions that validate executive route content against generated story artifacts
requires:
  - slice: S01
    provides: Canonical showcase intake manifest, blocked diagnostic schema, and artifact-root resolution contract consumed by S02 story generation and runtime rendering.
affects:
  - S03
  - S04
  - S05
key_files:
  - configs/showcase.yaml
  - src/showcase/story_contract.py
  - scripts/build_showcase_story.py
  - tests/test_showcase_story_contract.py
  - showcase/lib/load-story.ts
  - showcase/app/executive/page.tsx
  - showcase/components/executive-flow.tsx
  - showcase/components/evidence-list.tsx
  - showcase/tests/executive-flow.test.tsx
  - showcase/tests/load-story.test.ts
  - scripts/showcase_smoke_check.py
  - docs/showcase_local_runbook.md
key_decisions:
  - Enforced canonical executive section ordering (`prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`) in generated story artifacts and runtime rendering.
  - Used intake manifest diagnostics as source-of-truth for section/evidence readiness and blocked reasons rather than synthesizing runtime placeholders.
  - Implemented reduced-motion-safe executive transitions so motion-enhanced flow remains fully usable when user preference requests reduced motion.
  - Anchored smoke parity assertions on `data-testid`-scoped fields to stay strict but resilient to Next.js SSR wrapper/comment-node markup.
patterns_established:
  - Contract-first narrative generation: derive executive sections/evidence from generated artifacts, then render UI directly from that contract.
  - Fail-visible evidence handling: missing required upstream surfaces remain explicit in artifacts and UI with machine-readable reason fields.
  - Parity-first smoke verification: compare rendered executive flow against story artifact structure/fields, not static text snapshots.
observability_surfaces:
  - `outputs/showcase/story/sections.json` section/evidence status rollups with blocked reasons
  - `outputs/showcase/story/validation_report.json` contract diagnostics for story generation
  - `scripts/showcase_smoke_check.py` PASS/FAIL labeled parity checks across homepage + executive routes
  - UI-visible section status chips and per-evidence diagnostics fields (`surface_key`, `path`, `reason`, `requirement_key`)
drill_down_paths:
  - .gsd/milestones/M004-fjc2zy/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M004-fjc2zy/slices/S02/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-25T04:19:15.863Z
blocker_discovered: false
---

# S02: Executive trust-story flow from real exported artifacts

**Delivered a manifest-driven executive trust-story route that renders canonical sections and evidence diagnostics from generated story artifacts, with reduced-motion-safe transitions and smoke-verified artifact-to-UI parity.**

## What Happened

S02 converted the showcase from shell-only readiness reporting into an executive-first narrative flow backed by generated artifacts. T01 introduced the story contract generator and CLI (`scripts/build_showcase_story.py`) so intake diagnostics and narrative mapping now produce canonical `sections.json` and `validation_report.json` with deterministic section ordering, section/evidence readiness rollups, governance markers, and explicit blocked reasons. T02 wired Next.js runtime loading through `showcase/lib/load-story.ts`, added executive UI components/routes, and rendered section status chips plus per-evidence fields (`surface_key`, `path`, `reason`, `requirement_key`) while preserving blocked-state visibility and adding Framer Motion transitions that degrade safely under reduced-motion preferences. T03 extended smoke verification and runbook flow so local checks now assert homepage readiness diagnostics and executive artifact parity end-to-end against the generated story artifact. The slice consumed S01 intake-manifest diagnostics and now provides a stable executive contract/runtime path for downstream drill-down and report/deck parity slices.

## Verification

Executed all slice-plan verification commands successfully in the S02 worktree: (1) `python -m pytest tests/test_showcase_story_contract.py -q` (3 passed), (2) `python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story` plus artifact existence checks for `sections.json` and `validation_report.json`, (3) `npm --prefix showcase run test -- --run` (12 tests passed), (4) `npm --prefix showcase run build` (Next.js production build passed), and (5) `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000` after starting local dev server at 127.0.0.1:3000; smoke output reported PASS across homepage blocked diagnostics, executive section order, governance markers, and evidence-field parity checks.

## Requirements Advanced

- R011 — Extended the local-hosted showcase from intake shell to an executive runtime route backed by generated story artifacts and verified by local smoke checks.
- R012 — Locked canonical executive narrative ordering and claim-to-evidence pointer rendering in both generated artifacts and Next.js UI.
- R013 — Kept governance markers (internal-only, aggregate-safe, raw-review-text disallow) visible in executive artifacts and runtime surfaces.
- R022 — Preserved explicit blocked diagnostics for missing M003 closeout surfaces in generated story evidence rows and rendered UI.
- R009 — Maintained fairness/mitigation continuity by surfacing readiness/blocked state of Track E evidence in executive accountability flow.
- R010 — Maintained stronger-model continuity by surfacing readiness/blocked state of comparator-related evidence in executive flow diagnostics.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

Most upstream M001–M003 evidence surfaces are still absent in this worktree snapshot, so executive sections render as blocked diagnostics rather than ready evidence; this is expected and intentionally explicit. Report/deck generation parity is not complete in S02 and remains owned by S04/S05.

## Follow-ups

S03 should reuse the same section/evidence contract and loader semantics for per-track drill-down routes. S04 should consume the canonical story artifact as the source for report/deck section ordering and evidence anchors to avoid parallel narrative drift.

## Files Created/Modified

- `configs/showcase.yaml` — Added/updated executive narrative mapping and canonical section ordering used by story generation.
- `src/showcase/story_contract.py` — Implemented contract builder that maps intake diagnostics into section/evidence readiness outputs with governance markers and blocked reasons.
- `src/showcase/__init__.py` — Exported story-contract interfaces/constants for reuse.
- `scripts/build_showcase_story.py` — Added CLI to generate `sections.json` and `validation_report.json` story artifacts from config + intake manifest.
- `tests/test_showcase_story_contract.py` — Added regression coverage for ready/blocked story contract behavior and artifact generation shape.
- `showcase/package.json` — Added runtime dependency support for motion-enhanced executive flow.
- `showcase/package-lock.json` — Updated lockfile for new showcase dependencies.
- `showcase/lib/load-story.ts` — Implemented typed story loader with deterministic fallback behavior for missing/invalid artifacts.
- `showcase/app/page.tsx` — Updated homepage shell behavior to link into executive-first narrative flow while preserving intake diagnostics.
- `showcase/app/executive/page.tsx` — Added executive narrative route consuming generated story artifacts.
- `showcase/components/executive-flow.tsx` — Rendered canonical sections, readiness chips, governance markers, and evidence diagnostics with reduced-motion-safe transitions.
- `showcase/components/evidence-list.tsx` — Added per-evidence rendering component for pointer fields and blocked diagnostics.
- `showcase/app/layout.tsx` — Updated layout/accessibility shell for executive flow integration.
- `showcase/app/globals.css` — Added styles supporting executive flow readability and reduced-motion-safe behavior.
- `showcase/tests/executive-flow.test.tsx` — Added tests for executive rendering, blocked diagnostics visibility, governance markers, and reduced-motion behavior.
- `showcase/tests/homepage-shell.test.tsx` — Updated homepage tests for executive-first entry behavior and shell diagnostics continuity.
- `scripts/showcase_smoke_check.py` — Extended smoke checker to validate executive route parity, evidence fields, governance markers, and canonical section ordering against story artifacts.
- `showcase/tests/load-story.test.ts` — Added load-story normalization and deterministic fallback tests for missing/invalid story artifacts.
- `docs/showcase_local_runbook.md` — Updated local runbook sequence to include story generation and executive parity smoke checks with live server prerequisite.
