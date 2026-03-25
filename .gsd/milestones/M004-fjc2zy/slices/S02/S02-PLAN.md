# S02: Executive trust-story flow from real exported artifacts

**Goal:** Deliver an executive-first trust-story flow that is rendered from real generated/exported artifacts, keeps blocked evidence explicit when upstream files are missing, and adds Motion transitions that remain fully usable under reduced-motion preferences.
**Demo:** stakeholders can navigate an executive-first narrative (prediction, surfacing, onboarding, monitoring, accountability) with real charts/tables/summary content loaded from static exports and motion-enhanced transitions that remain usable with reduced-motion preferences.

## Must-Haves

- S02 directly advances **R011** by extending the local-hosted Next.js runtime from shell-only status into an executive narrative flow powered by artifact reads.
- S02 supports **R012** continuity by enforcing canonical section ordering (`prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`) and claim-to-evidence pointers.
- S02 supports **R013** continuity by keeping internal-only + aggregate-safe governance markers visible in executive surfaces.
- S02 supports **R022** continuity by rendering required M003 closeout evidence as explicit blocked diagnostics (never hidden when absent).
- S02 keeps **R009/R010** continuity visible by surfacing fairness/comparator evidence readiness state per executive section.
- Executive UI sections are loaded from generated story artifacts (`outputs/showcase/story/*.json`) rather than hardcoded literals or runtime analytics queries.

## Proof Level

- This slice proves: integration

## Integration Closure

S02 consumes S01 intake manifest/blocked diagnostics and introduces canonical story artifact generation + runtime loader + executive route/component wiring. After this slice, executive narrative and evidence pointers are live in the local app, while track drill-down depth, report/deck generation parity, and full milestone hardening remain for S03–S05.

## Verification

- `python -m pytest tests/test_showcase_story_contract.py -q`
- `python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && test -f outputs/showcase/story/sections.json && test -f outputs/showcase/story/validation_report.json`
- `npm --prefix showcase run test -- --run`
- `npm --prefix showcase run build`
- `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000`

## Observability / Diagnostics

- Runtime signals: story contract `section_status` rollups, per-evidence blocked reason rows, and UI-visible section status chips/evidence diagnostics.
- Inspection surfaces: `outputs/showcase/story/sections.json`, `outputs/showcase/story/validation_report.json`, executive flow route rendering, and smoke-check labeled PASS/FAIL output.
- Failure visibility: missing upstream surfaces remain explicit through `surface_key`, `path`, `reason`, and `requirement_key` values in both artifacts and rendered UI.
- Redaction constraints: keep internal-only/aggregate-safe markers visible and never include raw review text.

## Tasks

- [x] **T01: Define executive story contract and generate canonical section/evidence artifacts** `est:1h 30m`
  Create a deterministic story contract builder that transforms intake diagnostics + configured narrative mapping into `sections.json` and `validation_report.json`, with explicit ready/blocked semantics per section and per evidence row.
  - Files: `configs/showcase.yaml`, `src/showcase/story_contract.py`, `src/showcase/__init__.py`, `scripts/build_showcase_story.py`, `tests/test_showcase_story_contract.py`
  - Verify: python -m pytest tests/test_showcase_story_contract.py -q && python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && test -f outputs/showcase/story/sections.json && test -f outputs/showcase/story/validation_report.json

- [x] **T02: Build executive-first Next.js flow with Motion and reduced-motion-safe behavior** `est:2h`
  Wire a typed story loader and executive page/components that render canonical section order, evidence pointers, governance markers, and blocked diagnostics from generated artifacts, with Motion transitions that automatically degrade for reduced-motion users.
  - Files: `showcase/package.json`, `showcase/lib/load-story.ts`, `showcase/app/page.tsx`, `showcase/app/executive/page.tsx`, `showcase/components/executive-flow.tsx`, `showcase/components/evidence-list.tsx`, `showcase/app/layout.tsx`, `showcase/app/globals.css`, `showcase/tests/executive-flow.test.tsx`, `showcase/tests/homepage-shell.test.tsx`
  - Verify: npm --prefix showcase run test -- --run && npm --prefix showcase run build

- [x] **T03: Extend smoke/runbook verification for executive artifact parity** `est:1h`
  Extend local smoke checks and runbook steps to assert executive headings, evidence pointer fields, governance markers, and blocked-state visibility against generated story artifacts while preserving the existing readiness checks.
  - Files: `scripts/showcase_smoke_check.py`, `docs/showcase_local_runbook.md`, `showcase/tests/load-story.test.ts`
  - Verify: python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && npm --prefix showcase run test -- --run && python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000

## Files Likely Touched

- configs/showcase.yaml
- src/showcase/story_contract.py
- src/showcase/__init__.py
- scripts/build_showcase_story.py
- tests/test_showcase_story_contract.py
- showcase/package.json
- showcase/lib/load-story.ts
- showcase/app/page.tsx
- showcase/app/executive/page.tsx
- showcase/components/executive-flow.tsx
- showcase/components/evidence-list.tsx
- showcase/app/layout.tsx
- showcase/app/globals.css
- showcase/tests/executive-flow.test.tsx
- showcase/tests/homepage-shell.test.tsx
- scripts/showcase_smoke_check.py
- docs/showcase_local_runbook.md
- showcase/tests/load-story.test.ts
